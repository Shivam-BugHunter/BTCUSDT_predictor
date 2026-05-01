import numpy as np
import pandas as pd
import scipy.stats as stats
from arch import arch_model

def rolling_entropy(x, window=60, bins=20):
    def ent(v):
        p, _ = np.histogram(v, bins=bins, density=True)
        p = p[p > 0]
        return -np.sum(p * np.log(p))
    return x.rolling(window).apply(ent, raw=True)

def update_params(p, sigma2, bar_sigma2, t):
    err = sigma2 - bar_sigma2
    lr  = p['eta'] / (1 + t**0.55)
    p['gamma'] = np.clip(p['gamma'] + lr * err, 0.01, 0.5)
    return p

def simulate_cyber_gbm(S0, mu, sigma_fig, H, M, redundancy, info_filter, params, bar_sigma2, nu, n_steps, current_macro_stress=1.0, dt=1, eps=1e-6):
    S = np.zeros(n_steps + 1)
    V = np.zeros(n_steps + 1)
    S[0] = S0
    sigma2 = sigma_fig.iloc[-1] ** 2
    H_max = H.max() if H.max() > 0 else 1.0
    M_max = M.max() if M.max() > 0 else 1.0
    for t in range(1, n_steps + 1):
        current = -1
        H_val = min(H.iloc[current] / H_max, 1.0)
        M_val = min(M.iloc[current] / M_max, 1.0)
        crisis  = (H_val > 0.8) or (M_val > 0.8)
        delta_t = params['delta'] if crisis else 0.0
        sigma2 = (
            sigma_fig.iloc[current]**2 * (1 + params['alpha'] * H_val + delta_t * M_val)
            + params['gamma'] * (bar_sigma2 - sigma2)
        )
        sigma2 *= max(1e-12, redundancy.iloc[current])
        sigma2 *= 1 + 0.5 * info_filter.iloc[current]
        sigma2 *= current_macro_stress
        sigma2 = max(eps, min(sigma2, 0.5))
        Z   = np.random.standard_t(nu) * np.sqrt((nu - 2) / nu)
        S[t]= S[t-1] * np.exp((mu - 0.5 * sigma2) * dt + np.sqrt(sigma2 * dt) * Z)
        V[t]= sigma2
        params = update_params(params, sigma2, bar_sigma2, t)
    return S, V

def simulate_mc(S0, mu, sigma_fig, H, M, redundancy, info_filter, bar_sigma2, base_params, nu, current_macro_stress=1.0, n_sims=10000, n_days=1, dt=1):
    out = np.zeros((n_sims, n_days + 1))
    for i in range(n_sims):
        paths, _ = simulate_cyber_gbm(
            S0, mu, sigma_fig, H, M, redundancy, info_filter,
            base_params.copy(),
            bar_sigma2, nu, n_days, current_macro_stress, dt
        )
        out[i] = paths
    return out

def predict_next_bar(prices, macro_data=None, n_sims=10000):
    log_ret = np.log(prices / prices.shift(1)).dropna()
    mu = log_ret.mean()
    S0 = prices.iloc[-1]
    dt = 1
    
    # Fit ARCH model
    am = arch_model(log_ret * 100, vol='FIGARCH', p=1, o=0, q=1, dist='studentst')
    res = am.fit(disp='off')
    sigma_fig = res.conditional_volatility / 100
    resid = (log_ret * 100 - res.params['mu']) / res.conditional_volatility
    nu = max(4, stats.t.fit(resid, floc=0, fscale=1)[0])
    
    H_series = rolling_entropy(resid)
    M_series = log_ret.abs().rolling(60).mean()
    
    H_max, M_max = H_series.max(), M_series.max()
    α0, δ0 = 0.5, 0.3
    if α0 * H_max + δ0 * M_max >= 1:
        fac = 0.95 / (α0 * H_max + δ0 * M_max)
        α0 *= fac
        δ0 *= fac
    base_params = {'alpha': α0, 'delta': δ0, 'gamma': 0.2, 'kappa': 0.1, 'eta': 1e-3}
    
    bar_sigma2 = (sigma_fig**2).mean()
    
    # Needs to align index or drop NA
    redundancy = 1 + 0.1 * np.log1p(prices.rolling(5).var() / prices.rolling(20).var())
    # redundancy corresponds to prices, so length is len(prices). log_ret length is len(prices)-1.
    # we need redundancy aligned with log_ret.
    redundancy = redundancy.loc[log_ret.index]
    
    info_filter = (H_series > H_series.mean()).astype(float)
    
    current_macro_stress = 1.0
    if macro_data is not None and not macro_data.empty:
        if "^VIX" in macro_data.columns and not macro_data["^VIX"].isnull().all():
            vix = macro_data["^VIX"]
            vix_norm = vix / vix.mean()
            vix_norm_aligned = vix_norm.reindex(log_ret.index).fillna(1.0)
            current_macro_stress = vix_norm_aligned.iloc[-1]
        else:
            macro_rets = np.log(macro_data / macro_data.shift(1)).replace([np.inf, -np.inf], np.nan).fillna(0)
            macro_vol = macro_rets.rolling(24).std().mean(axis=1)
            macro_vol_norm = macro_vol / macro_vol.mean()
            macro_vol_aligned = macro_vol_norm.reindex(log_ret.index).fillna(1.0)
            current_macro_stress = macro_vol_aligned.iloc[-1]
            
    # Clip multiplier to avoid extreme narrowness or explosion
    current_macro_stress = np.clip(current_macro_stress, 0.5, 2.0)
    
    # Simulate
    paths = simulate_mc(
        S0, mu, sigma_fig, H_series, M_series, redundancy, info_filter, 
        bar_sigma2, base_params, nu, current_macro_stress, n_sims=n_sims, n_days=1, dt=dt
    )
    
    S_t1 = paths[:, 1]
    low_95, high_95 = np.percentile(S_t1, [2.5, 97.5])
    return low_95, high_95
