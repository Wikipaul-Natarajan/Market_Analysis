"""Analyses required by the approved project proposal, on the Koyambedu series.

1. 30-day 2023 tomato procurement scenario (proposal objective iv).
2. SHAP ranking of a Northeast Monsoon deviation index against price-lag features, with beeswarm and
   dependence plots for the top three features (objective ii and SHAP deliverable).
3. Delta-accuracy test: XGBoost on price features only versus XGBoost with weather context, on a
   six-month held-out period, with a Diebold-Mariano test (AgriSight evaluation deliverable).
Market arrival volumes are not available for the Koyambedu series; historical policy news is not
archived, so the context tested is weather observed up to each forecast date.
Outputs: outputs/proposal_alignment/*.csv and outputs/figures/report/fig_pa_*.png
"""
from pathlib import Path
import warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
import statsmodels.api as sm
from scipy import stats

warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'proposal_alignment'; OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / 'outputs' / 'figures' / 'report'; FIG.mkdir(parents=True, exist_ok=True)
SERIES = {'Tomato': 'Tomato', 'Onion': 'Onion Big', 'Potato': 'Potato', 'Cabbage': 'Cabbage', 'Carrot': 'Carrot',
          'Beans': 'French Beans', 'Brinjal': 'Brinjal', 'Drumstick': 'Drumsticks'}
PRICE_F = ['lag_1', 'lag_7', 'lag_14', 'lag_30', 'mean_7', 'mean_30', 'std_30', 'mom_7', 'doy_sin', 'doy_cos']
WEATHER_F = ['rain_7d', 'rain_30d', 'tmax_7d', 'rain_anomaly_7d', 'ne_monsoon_deviation', 'ne_season']
plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'savefig.dpi': 220, 'savefig.bbox': 'tight'})


def xgb():
    return XGBRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.85, colsample_bytree=0.9,
                        reg_lambda=1.0, objective='reg:squarederror', random_state=42, n_jobs=2, verbosity=0)


def load():
    d = pd.read_csv(ROOT / 'data' / 'secondary' / 'koyambedu_prices_daily.csv', parse_dates=['date'])
    w = pd.read_parquet(ROOT / 'data' / 'external' / 'weather_chennai.parquet')
    w['date'] = pd.to_datetime(w['arrival_date']); w = w.set_index('date').sort_index()
    rain = w['precipitation'].astype(float)
    wf = pd.DataFrame(index=w.index)
    wf['rain_7d'] = rain.rolling(7).sum(); wf['rain_30d'] = rain.rolling(30).sum()
    wf['tmax_7d'] = w['temp_max'].astype(float).rolling(7).mean()
    m = wf.index.month
    daily_z = (rain - rain.groupby(m).transform('mean')) / rain.groupby(m).transform('std')
    wf['rain_anomaly_7d'] = daily_z.rolling(7, min_periods=5).mean()
    z30 = (wf['rain_30d'] - wf['rain_30d'].groupby(m).transform('mean')) / wf['rain_30d'].groupby(m).transform('std')
    wf['ne_season'] = m.isin([10, 11, 12]).astype(int)
    wf['ne_monsoon_deviation'] = z30 * wf['ne_season']   # deviation of 30-day rain from same-month norm, NE season only
    return d, wf


def price_features(s):
    x = pd.DataFrame(index=s.index)
    for k in (1, 7, 14, 30): x[f'lag_{k}'] = s.shift(k - 1)          # lag_1 = price on the origin date
    x['mean_7'] = s.rolling(7).mean(); x['mean_30'] = s.rolling(30).mean(); x['std_30'] = s.rolling(30).std()
    x['mom_7'] = np.log(s / s.shift(7)) * 100
    return x


def add_target_calendar(x, h):
    doy = (x.index + pd.Timedelta(days=h)).dayofyear
    x = x.copy(); x['doy_sin'] = np.sin(2 * np.pi * doy / 365.25); x['doy_cos'] = np.cos(2 * np.pi * doy / 365.25)
    return x


def rules(change, cv, z):
    score = min(100, cv * 120 + abs(z) * 12 + abs(change) * 1.2)
    risk = 'HIGH' if score >= 55 else 'MEDIUM' if score >= 28 else 'LOW'
    action = ('PROCURE NOW' if change > 5 and risk != 'HIGH' else 'DELAY PROCUREMENT' if change < -5 else
              'PARTIAL PROCUREMENT' if risk == 'HIGH' else 'HEDGE' if abs(change) > 3 else 'HOLD')
    return risk, action


def crisis_30(d):
    s = d[d.commodity == 'Tomato'].set_index('date').observed_price_inr_per_kg.astype(float).sort_index()
    rows = []
    for h in (14, 30):
        x = add_target_calendar(price_features(s), h); y = s.shift(-h).rename('y')
        frame = x.join(y).dropna()
        for origin in pd.date_range('2023-04-01', '2023-06-30', freq='7D'):
            train = frame[frame.index + pd.Timedelta(days=h) <= origin]
            if len(train) < 180 or origin + pd.Timedelta(days=h) not in s.index: continue
            m = xgb().fit(train[PRICE_F], train.y)
            pred = max(0.0, float(m.predict(x.loc[[origin], PRICE_F])[0]))
            cur, fut = float(s.loc[origin]), float(s.loc[origin + pd.Timedelta(days=h)])
            hist = s.loc[:origin].tail(30); cv = float(hist.std() / hist.mean()); z = float((cur - hist.mean()) / (hist.std() or 1))
            change = (pred / cur - 1) * 100
            risk, action = rules(change, cv, z)
            share = 1.0 if action in ('PROCURE NOW', 'HOLD') else 0.0 if action == 'DELAY PROCUREMENT' else 0.5
            rows.append({'horizon_days': h, 'origin': origin.date().isoformat(), 'target': (origin + pd.Timedelta(days=h)).date().isoformat(),
                         'price_at_origin': cur, 'forecast': round(pred, 2), 'actual_at_target': fut, 'forecast_change_pct': round(change, 2),
                         'risk': risk, 'action': action, 'result_vs_buy_now_inr_per_kg': round(cur - (share * cur + (1 - share) * fut), 2)})
    r = pd.DataFrame(rows); r.to_csv(OUT / 'tomato_2023_scenario_14_vs_30_day.csv', index=False)
    summ = r.groupby('horizon_days').agg(origins=('origin', 'size'), cumulative_result=('result_vs_buy_now_inr_per_kg', 'sum'),
                                         better=('result_vs_buy_now_inr_per_kg', lambda v: int((v > 0).sum())),
                                         worse=('result_vs_buy_now_inr_per_kg', lambda v: int((v < 0).sum()))).reset_index()
    summ.to_csv(OUT / 'tomato_2023_scenario_summary.csv', index=False)
    t = s.loc['2023-03-15':'2023-09-15']; r30 = r[r.horizon_days == 30]
    fig, ax = plt.subplots(figsize=(6.6, 3.0)); ax.plot(t.index, t, color='#1f4e79', lw=1.3, label='Observed daily price')
    mk = {'DELAY PROCUREMENT': ('v', '#d62728'), 'PROCURE NOW': ('^', '#2ca02c'), 'PARTIAL PROCUREMENT': ('s', '#ff7f0e'), 'HEDGE': ('D', '#9467bd'), 'HOLD': ('o', '#7f7f7f')}
    for a, (mm, c) in mk.items():
        g = r30[r30.action == a]
        if len(g): ax.scatter(pd.to_datetime(g.origin), g.price_at_origin, marker=mm, color=c, s=34, zorder=3, label=f'30-day advice: {a.title()}')
    ax.axvspan(pd.Timestamp('2023-07-03'), pd.Timestamp('2023-08-22'), color='#fdd', alpha=.5, label='Event window')
    ax.set_ylabel('₹/kg'); ax.set_title('Tomato 2023: advice from 30-day forecasts at weekly origins', fontweight='bold'); ax.legend(fontsize=6.5, ncol=2, loc='upper left')
    fig.savefig(FIG / 'fig_pa_tomato_30day.png'); plt.close(fig)
    return r, summ


def build_panel(d, wf, h):
    parts = []
    for name, series in SERIES.items():
        s = d[d.commodity == series].set_index('date').observed_price_inr_per_kg.astype(float).sort_index()
        x = add_target_calendar(price_features(s), h).join(wf, how='inner')
        x['y'] = s.shift(-h).reindex(x.index); x['commodity'] = name
        parts.append(x)
    return pd.concat(parts)


def dm_test(e_base, e_ctx, h):
    """Diebold-Mariano on absolute errors; d>0 means the context model has smaller error. HAC (Newey-West) variance."""
    dlt = np.abs(np.asarray(e_base)) - np.abs(np.asarray(e_ctx))
    res = sm.OLS(dlt, np.ones(len(dlt))).fit(cov_type='HAC', cov_kwds={'maxlags': max(1, h - 1)})
    return float(res.params[0]), float(res.tvalues[0]), float(res.pvalues[0])


def delta_test(d, wf):
    rows = []
    origins = pd.date_range('2026-04-01', '2026-09-30', freq='7D')
    for h in (7, 14, 30):
        p = build_panel(d, wf, h)
        for name in SERIES:
            g = p[p.commodity == name].dropna(subset=PRICE_F + WEATHER_F)
            for origin in origins:
                tgt = origin + pd.Timedelta(days=h)
                if origin not in g.index or pd.isna(g.loc[origin, 'y']): continue
                train = g[(g.index + pd.Timedelta(days=h) <= origin)].dropna(subset=['y'])
                if len(train) < 180: continue
                xo = g.loc[[origin]]
                pb = float(xgb().fit(train[PRICE_F], train.y).predict(xo[PRICE_F])[0])
                pc = float(xgb().fit(train[PRICE_F + WEATHER_F], train.y).predict(xo[PRICE_F + WEATHER_F])[0])
                rows.append({'horizon_days': h, 'commodity': name, 'origin': origin.date().isoformat(), 'target': tgt.date().isoformat(),
                             'actual': float(g.loc[origin, 'y']), 'naive': float(g.loc[origin, 'lag_1']),
                             'xgb_price_only': max(0, pb), 'xgb_with_weather': max(0, pc)})
    r = pd.DataFrame(rows); r.to_csv(OUT / 'delta_accuracy_predictions.csv', index=False)
    out = []
    for h, g in r.groupby('horizon_days'):
        g = g.sort_values(['commodity', 'origin'])
        rec = {'horizon_days': h, 'forecasts': len(g), 'origins': g.origin.nunique()}
        for m in ('naive', 'xgb_price_only', 'xgb_with_weather'):
            e = g[m] - g.actual
            rec[f'{m}_wape'] = round(float(e.abs().sum() / g.actual.sum() * 100), 2)
            rec[f'{m}_mape'] = round(float((e.abs() / g.actual).mean() * 100), 2)
        dm, t, pval = dm_test(g.xgb_price_only - g.actual, g.xgb_with_weather - g.actual, h)
        rec.update({'delta_wape_pts': round(rec['xgb_price_only_wape'] - rec['xgb_with_weather_wape'], 2),
                    'dm_mean_abs_error_gain_inr': round(dm, 3), 'dm_t': round(t, 2), 'dm_p': round(pval, 3)})
        dmn, tn, pn = dm_test(g.naive - g.actual, g.xgb_with_weather - g.actual, h)
        rec.update({'dm_vs_naive_gain_inr': round(dmn, 3), 'dm_vs_naive_p': round(pn, 3)})
        out.append(rec)
    s = pd.DataFrame(out); s.to_csv(OUT / 'delta_accuracy_summary.csv', index=False)
    fig, ax = plt.subplots(figsize=(6.4, 2.8)); xx = np.arange(len(s)); bw = .26
    for i, (m, lab, c) in enumerate([('naive', 'Naive (last value)', '#7f7f7f'), ('xgb_price_only', 'XGBoost, prices only', '#ff7f0e'),
                                     ('xgb_with_weather', 'XGBoost + weather context', '#1f77b4')]):
        ax.bar(xx + (i - 1) * bw, s[f'{m}_wape'], bw, label=lab, color=c)
    ax.set_xticks(xx); ax.set_xticklabels([f'{h} days' for h in s.horizon_days]); ax.set_ylabel('WAPE (%)')
    ax.set_title('Delta-accuracy test: six-month holdout (Apr–Sep 2026)', fontweight='bold')
    ax.legend(ncol=3, fontsize=7, loc='upper center', bbox_to_anchor=(.5, -.12)); fig.savefig(FIG / 'fig_pa_delta_accuracy.png'); plt.close(fig)
    return s


def shap_ranking(d, wf):
    import shap
    h = 7; p = build_panel(d, wf, h); feats = PRICE_F + WEATHER_F; rows = []; tomato = None
    for name in SERIES:
        g = p[p.commodity == name].dropna(subset=feats + ['y'])
        m = xgb().fit(g[feats], g.y); sv = shap.TreeExplainer(m)(g[feats])
        imp = pd.Series(np.abs(sv.values).mean(0), index=feats); share = imp / imp.sum() * 100
        rank = share.rank(ascending=False).astype(int)
        rows.append({'commodity': name, 'n_rows': len(g), 'top1': share.idxmax(), 'top1_share_pct': round(share.max(), 1),
                     'lag_1_share_pct': round(share['lag_1'], 1), 'ne_monsoon_deviation_share_pct': round(share['ne_monsoon_deviation'], 2),
                     'ne_monsoon_deviation_rank': int(rank['ne_monsoon_deviation']), 'rain_anomaly_7d_share_pct': round(share['rain_anomaly_7d'], 2),
                     'rain_anomaly_7d_rank': int(rank['rain_anomaly_7d']), 'all_weather_share_pct': round(share[WEATHER_F].sum(), 1), 'n_features': len(feats)})
        if name == 'Tomato': tomato = (sv, share)
    r = pd.DataFrame(rows); r.to_csv(OUT / 'shap_monsoon_ranking.csv', index=False)
    sv, share = tomato
    NICE = {'lag_1': 'Price at origin', 'lag_7': 'Price 6 days earlier', 'lag_14': 'Price 13 days earlier', 'lag_30': 'Price 29 days earlier',
            'mean_7': '7-day mean price', 'mean_30': '30-day mean price', 'std_30': '30-day price std. dev.', 'mom_7': '7-day momentum (%)',
            'doy_sin': 'Season of target date (sin)', 'doy_cos': 'Season of target date (cos)', 'rain_7d': '7-day rainfall (mm)',
            'rain_30d': '30-day rainfall (mm)', 'tmax_7d': '7-day mean max temp.', 'rain_anomaly_7d': '7-day rainfall anomaly',
            'ne_monsoon_deviation': 'NE Monsoon deviation index', 'ne_season': 'NE Monsoon season flag'}
    sv.feature_names = [NICE[f] for f in feats]
    plt.figure(); shap.plots.beeswarm(sv, max_display=12, show=False)
    plt.title('Tomato (Koyambedu, 7-day XGBoost): SHAP beeswarm', fontweight='bold', fontsize=10)
    plt.gcf().set_size_inches(6.6, 4.2); plt.savefig(FIG / 'fig_pa_shap_beeswarm_tomato.png'); plt.close()
    top3 = list(share.sort_values(ascending=False).index[:3])
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))
    X = p[p.commodity == 'Tomato'].dropna(subset=feats + ['y'])
    for ax, f in zip(axes, top3):
        j = feats.index(f)
        ax.scatter(X[f], sv.values[:, j], s=6, alpha=.6, color='#1f77b4')
        ax.axhline(0, color='k', lw=.6); ax.set_xlabel(NICE[f], fontsize=8); ax.set_ylabel('SHAP value (₹/kg)', fontsize=8)
        ax.set_title(f'{NICE[f]} ({share[f]:.1f}%)', fontsize=8.5); ax.tick_params(labelsize=7)
    fig.suptitle('Tomato: SHAP dependence plots for the top three features', fontweight='bold', fontsize=9.5); fig.tight_layout()
    fig.savefig(FIG / 'fig_pa_shap_dependence_tomato.png'); plt.close(fig)
    pd.Series(top3, name='feature').to_csv(OUT / 'shap_tomato_top3.csv', index=False)
    return r, top3


def main():
    d, wf = load()
    r, summ = crisis_30(d); print(summ.to_string(index=False))
    print(delta_test(d, wf).to_string(index=False))
    rk, top3 = shap_ranking(d, wf); print(rk.to_string(index=False)); print('tomato top3:', top3)


if __name__ == '__main__':
    main()
