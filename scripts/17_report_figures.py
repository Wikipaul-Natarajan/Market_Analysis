"""Publication figures for the final project report, drawn from saved pipeline outputs.

Run after scripts 02-09 and 12-16. Writes PNGs to outputs/figures/report/.
"""
import json, pickle
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs'; REP = OUT/'reports'; POE = OUT/'proposal_objective_evaluation'
FIG = OUT/'figures'/'report'; FIG.mkdir(parents=True, exist_ok=True)
PROC = ROOT/'data'/'processed'; SEC = ROOT/'data'/'secondary'

plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .25,
                     'savefig.dpi': 220, 'savefig.bbox': 'tight', 'legend.frameon': False})
C = {'SARIMA': '#1f77b4', 'Prophet': '#d62728', 'RF': '#2ca02c', 'RandomForest': '#2ca02c', 'XGBoost': '#ff7f0e',
     'Naive': '#7f7f7f', 'NaiveLast': '#7f7f7f', 'SeasonalNaive': '#9467bd', 'SeasonalNaive7': '#9467bd'}
ORDER8 = ['Beans', 'Brinjal', 'Cabbage', 'Carrot', 'Drumstick', 'Onion', 'Potato', 'Tomato']


def save(fig, name):
    fig.savefig(FIG/f'{name}.png'); plt.close(fig); print('saved', name)


def workflow():
    fig, ax = plt.subplots(figsize=(7.2, 4.6)); ax.axis('off'); ax.set_xlim(0, 10); ax.set_ylim(-0.3, 7)
    def box(x, y, w, h, text, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05,rounding_size=0.12', fc=fc, ec='#333', lw=.8))
        ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=7.4, wrap=True)
    def arrow(x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', lw=.9, color='#333'))
    ax.text(2.4, 6.75, 'Track A: Tamil Nadu statewide', ha='center', fontweight='bold', fontsize=8.5)
    ax.text(7.6, 6.75, 'Track B: Koyambedu market', ha='center', fontweight='bold', fontsize=8.5)
    A = [('Kaggle Agmarknet extract\n414,388 rows · 451 markets', '#e8f0fb'),
         ('Daily median + 62 features\nlags, rolling, calendar, weather', '#e8f0fb'),
         ('SARIMA · Prophet · RF · XGBoost\n90-day holdout\n+ strict 7-day horizon check', '#e8f0fb'),
         ('SHAP explanations\nRule-based agent pipeline', '#e8f0fb')]
    B = [('vegetablemarketprice.com API\n14,472 daily ₹/kg values', '#eaf6ea'),
         ('Common-origin evaluation\n7/14/30-day horizons', '#eaf6ea'),
         ('Monsoon HAC regression\nTomato 2023 scenario', '#eaf6ea'),
         ('Procurement backtest\n56 fixed-lot cases', '#eaf6ea')]
    for i, (t, c) in enumerate(A):
        box(.4, 5.3-i*1.35, 4.0, 1.0, t, c)
        if i: arrow(2.4, 5.3-(i-1)*1.35, 2.4, 5.3-i*1.35+1.0)
    for i, (t, c) in enumerate(B):
        box(5.6, 5.3-i*1.35, 4.0, 1.0, t, c)
        if i: arrow(7.6, 5.3-(i-1)*1.35, 7.6, 5.3-i*1.35+1.0)
    box(.4, -.05, 9.2, .75, 'Open-Meteo Chennai weather feeds both tracks\n→  Four-role brief with freshness gate  →  Nine-page Streamlit dashboard', '#fdf3e1')
    arrow(2.4, 1.25, 2.4, .72); arrow(7.6, 1.25, 7.6, .72)
    save(fig, 'fig_3_1_workflow')


def statewide_desc():
    raw = pd.read_parquet(PROC/'tn_vegetables_daily.parquet'); raw['arrival_date'] = pd.to_datetime(raw.arrival_date)
    f = pd.read_parquet(PROC/'tn_features.parquet'); f['arrival_date'] = pd.to_datetime(f.arrival_date)
    # records per commodity and market type
    raw['type'] = np.where(raw.market.str.contains('Uzhavar', case=False), 'Uzhavar Sandhai (farmers\u2019 market)', 'Other regulated markets')
    ct = raw.groupby(['commodity', 'type']).size().unstack().reindex(ORDER8)
    fig, ax = plt.subplots(figsize=(6.6, 3.0)); ct.plot.barh(stacked=True, ax=ax, color=['#9ecae1', '#3182bd'], width=.7)
    ax.set_xlabel('Market-level records'); ax.set_ylabel(''); ax.set_title('Statewide records by commodity and market type, Jan 2024–Apr 2026')
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.18), ncol=2, fontsize=7.5); save(fig, 'fig_4_1_records')
    # monthly median trends (in Rs/kg for readability: /100)
    m = f.assign(month=f.arrival_date.dt.to_period('M').dt.to_timestamp()).groupby(['commodity', 'month']).modal_price.median().div(100).unstack(0)
    fig, axes = plt.subplots(4, 2, figsize=(6.6, 7.2), sharex=True)
    for ax, c in zip(axes.flat, ORDER8):
        ax.plot(m.index, m[c], color='#1f4e79', lw=1.3); ax.set_title(c, fontsize=9); ax.set_ylabel('₹/kg')
    for ax in axes[-1]: ax.tick_params(axis='x', rotation=45)
    fig.suptitle('Monthly median of daily statewide modal price (₹/quintal ÷ 100)', fontweight='bold', fontsize=10); fig.tight_layout()
    save(fig, 'fig_4_2_monthly_trends')
    # seasonal index
    si = f.assign(mo=f.arrival_date.dt.month).groupby(['commodity', 'mo']).modal_price.median().unstack(0)
    si = si/si.mean()*100
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    for c in ORDER8: ax.plot(si.index, si[c], marker='o', ms=3, lw=1.1, label=c)
    ax.axhline(100, color='k', lw=.6); ax.set_xticks(range(1, 13)); ax.set_xticklabels(list('JFMAMJJASOND'))
    ax.set_ylabel('Seasonal index (annual mean = 100)'); ax.set_title('Seasonal price index by month, statewide')
    ax.legend(ncol=4, fontsize=7, loc='upper left'); save(fig, 'fig_4_3_seasonal_index')
    # correlation
    mm = f.assign(month=f.arrival_date.dt.to_period('M')).groupby(['month', 'commodity']).modal_price.median().unstack()[ORDER8]
    corr = mm.corr(); mask = np.triu(np.ones_like(corr, bool), 1)
    fig, ax = plt.subplots(figsize=(5.2, 4.2)); im = ax.imshow(np.where(mask, np.nan, corr), cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xticks(range(8)); ax.set_yticks(range(8)); ax.set_xticklabels(ORDER8, rotation=45, ha='right'); ax.set_yticklabels(ORDER8); ax.grid(False)
    for i in range(8):
        for j in range(i+1):
            ax.text(j, i, f'{corr.iloc[i, j]:.2f}', ha='center', va='center', fontsize=7)
    fig.colorbar(im, ax=ax, shrink=.8); ax.set_title('Correlation of monthly median prices'); save(fig, 'fig_4_4_correlation')
    # tomato with anomaly + unit-mixing flags
    t = f[f.commodity == 'Tomato'].set_index('arrival_date').modal_price
    roll = t.rolling(30, min_periods=10); z = (t-roll.mean())/roll.std(); an = z.abs() > 2.5; low = t < 300
    fig, ax = plt.subplots(figsize=(6.6, 2.8)); ax.plot(t.index, t, lw=.9, color='#1f4e79', label='Daily statewide median')
    ax.scatter(t.index[an], t[an], color='#d62728', s=10, zorder=3, label='|rolling z| > 2.5')
    ax.scatter(t.index[low], t[low], color='#ff7f0e', marker='x', s=14, zorder=3, label='< ₹300/quintal (likely per-kg entry)')
    ax.set_ylabel('₹/quintal'); ax.set_title('Tomato daily statewide price with anomaly and unit-error flags'); ax.legend(fontsize=7)
    save(fig, 'fig_4_5_tomato_anomalies')


def statewide_models():
    sar = pd.read_csv(REP/'sarima_summary.csv'); sar = sar[sar.commodity != 'AVERAGE'].set_index('commodity')
    pro = pd.read_csv(REP/'prophet_summary.csv').set_index('commodity')
    ml = pd.read_csv(REP/'ml_summary.csv').pivot(index='commodity', columns='model', values='mape')
    df = pd.DataFrame({'SARIMA static': sar.mape, 'SARIMA 7-day WF': sar.walk_forward_mape, 'Prophet': pro.mape,
                       'Random Forest': ml.RF, 'XGBoost': ml.XGBoost}).reindex(ORDER8)
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    df.plot.bar(ax=ax, width=.82, color=['#9ecae1', '#1f77b4', '#d62728', '#2ca02c', '#ff7f0e'])
    ax.set_ylabel('MAPE (%)'); ax.set_xlabel(''); ax.set_title('Statewide 90-day holdout MAPE by commodity and model'); ax.tick_params(axis='x', rotation=0)
    ax.legend(ncol=5, fontsize=6.8, loc='upper center', bbox_to_anchor=(.5, -.1)); save(fig, 'fig_4_6_statewide_models')
    hs = pd.read_csv(REP/'horizon_sensitivity.csv')
    lab = {'Naive_t-1': 'Naive: yesterday\u2019s price', 'Naive_t-7': 'Naive: price 7 days ago', 'XGB_original': 'XGBoost, script-07 features',
           'XGB_no_own_lag1': 'XGBoost without own t-1 price', 'XGB_strict_7day': 'XGBoost, strict 7-day-ahead'}
    fig, ax = plt.subplots(figsize=(6.6, 2.6)); y = [lab[v] for v in hs.variant][::-1]; x = hs.mape_pct.values[::-1]
    cols = ['#7f7f7f', '#7f7f7f', '#ff7f0e', '#ff7f0e', '#ff7f0e'][::-1]
    ax.barh(y, x, color=cols)
    for yi, xi in zip(y, x): ax.text(xi+.4, yi, f'{xi:.2f}%', va='center', fontsize=8)
    ax.set_xlabel('Mean MAPE across 8 commodities (%)'); ax.set_title('Horizon sensitivity: same 90-day statewide test window'); save(fig, 'fig_4_7_horizon_sensitivity')
    res = pickle.load(open(OUT/'models'/'ml_results.pkl', 'rb'))['Tomato']
    f = pd.read_parquet(PROC/'tn_features.parquet'); f['arrival_date'] = pd.to_datetime(f.arrival_date)
    tom = f[f.commodity == 'Tomato'].set_index('arrival_date').modal_price
    dates = pd.to_datetime(res['test_dates']); naive = tom.shift(1).reindex(dates)
    fig, ax = plt.subplots(figsize=(6.6, 2.8)); ax.plot(dates, res['actual'], color='k', lw=1.4, label='Actual')
    ax.plot(dates, res['predictions']['RF'], color=C['RF'], lw=1, label='Random Forest')
    ax.plot(dates, res['predictions']['XGBoost'], color=C['XGBoost'], lw=1, label='XGBoost')
    ax.plot(dates, naive, color=C['Naive'], lw=1, ls='--', label='Naive (yesterday)')
    ax.set_ylabel('₹/quintal'); ax.set_title('Tomato: statewide 90-day holdout, models vs yesterday\u2019s price'); ax.legend(ncol=4, fontsize=7)
    ax.tick_params(axis='x', rotation=30); save(fig, 'fig_4_8_tomato_holdout')


def shap_fig():
    import re
    names = {'position_52w': 'Position in 52-week range', 'rolling_mean_7': '7-day average price', 'lag_30': 'Price 30 days earlier',
             'lag_14': 'Price 14 days earlier', 'temp_max': 'Max temperature (t-1)', 'ema_7': '7-day EMA', 'ema_14': '14-day EMA',
             'rolling_max_7': '7-day max price', 'momentum_30': '30-day momentum', 'rain_7d_sum': '7-day rainfall', 'rain_30d_sum': '30-day rainfall',
             'rolling_min_7': '7-day min price', 'market_count': 'Reporting markets (t-1)', 'momentum_14': '14-day momentum'}
    drivers = pd.read_csv(REP/'shap_top_drivers.csv')
    # rebuild global importance from per-commodity SHAP top-3 + global plot data via model refit is heavy; use mean |SHAP| table
    from xgboost import XGBRegressor
    import shap
    f = pd.read_parquet(PROC/'tn_features.parquet'); saved = pickle.load(open(OUT/'models'/'ml_results.pkl', 'rb'))
    imps = []
    for c, v in saved.items():
        x = f[f.commodity == c].replace([np.inf, -np.inf], np.nan).dropna(subset=v['features'])
        m = XGBRegressor(n_estimators=400, max_depth=5, learning_rate=.05, subsample=.8, colsample_bytree=.8, min_child_weight=3,
                         reg_alpha=.1, reg_lambda=1, random_state=42, verbosity=0).fit(x[v['features']], x.modal_price)
        sv = shap.TreeExplainer(m)(x[v['features']]).values
        imp = pd.Series(np.abs(sv).mean(0), index=v['features']); imps.append((imp/imp.sum()*100).rename(c))
    M = pd.concat(imps, axis=1)
    def group(n):
        if n.startswith('cross_'):
            return 'own' if False else 'cross'
        return 'other'
    own = pd.Series({c: M.loc[f'cross_{c}_lag1', c] for c in M.columns})
    M.to_csv(REP/'shap_share_by_feature.csv')
    top = M.mean(1).sort_values(ascending=False).head(12)
    lbl = [names.get(i, re.sub(r'cross_(\w+)_lag1', r'\1 price (t-1)', i)) for i in top.index]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2), gridspec_kw={'width_ratios': [1.35, 1]})
    axes[0].barh(lbl[::-1], top.values[::-1], color=['#ff7f0e' if i.startswith('cross_') else '#1f77b4' for i in top.index][::-1])
    axes[0].set_xlabel('Mean share of |SHAP| (%)'); axes[0].set_title('Top features, average of 8 models')
    axes[1].bar(own.index, own.values, color='#ff7f0e'); axes[1].set_ylabel('% of |SHAP|'); axes[1].tick_params(axis='x', rotation=60)
    axes[1].set_title('Share from own price at t-1'); fig.tight_layout(); save(fig, 'fig_4_9_shap')
    own.round(2).to_csv(REP/'shap_own_lag1_share.csv')


def koyambedu():
    d = pd.read_csv(SEC/'koyambedu_prices_daily.csv', parse_dates=['date'])
    order = ['French Beans', 'Brinjal', 'Cabbage', 'Carrot', 'Drumsticks', 'Onion Big', 'Potato', 'Tomato']
    fig, axes = plt.subplots(4, 2, figsize=(6.6, 7.2), sharex=True)
    for ax, c in zip(axes.flat, order):
        s = d[d.commodity == c].set_index('date').observed_price_inr_per_kg
        ax.plot(s.index, s, lw=.6, color='#2b7a3d'); ax.set_title(c, fontsize=9); ax.set_ylabel('₹/kg')
    for ax in axes[-1]: ax.tick_params(axis='x', rotation=45)
    fig.suptitle('Koyambedu history-page daily prices, Nov 2021–Oct 2026', fontweight='bold', fontsize=10); fig.tight_layout()
    save(fig, 'fig_4_10_koyambedu_panel')
    # tomato 2023 with crisis scenario actions
    t = d[(d.commodity == 'Tomato') & d.date.between('2023-03-15', '2023-09-15')].set_index('date').observed_price_inr_per_kg
    sc = pd.read_csv(POE/'crisis_period_procurement_scenario.csv', parse_dates=['origin'])
    fig, ax = plt.subplots(figsize=(6.6, 3.0)); ax.plot(t.index, t, color='#1f4e79', lw=1.3, label='Observed daily price')
    mk = {'DELAY PROCUREMENT': ('v', '#d62728'), 'PROCURE NOW': ('^', '#2ca02c'), 'PARTIAL PROCUREMENT': ('s', '#ff7f0e'), 'HEDGE': ('D', '#9467bd'), 'HOLD': ('o', '#7f7f7f')}
    for a, (m_, col) in mk.items():
        g = sc[sc.action == a]
        if len(g): ax.scatter(g.origin, g.current_source_value, marker=m_, color=col, s=34, zorder=3, label=f'Advice: {a.title()}')
    ax.axvspan(pd.Timestamp('2023-07-03'), pd.Timestamp('2023-08-22'), color='#fdd', alpha=.5, label='Event window (3 Jul–22 Aug)')
    ax.set_ylabel('₹/kg'); ax.set_title('Tomato 2023: rule-based advice at weekly origins vs observed prices'); ax.legend(fontsize=6.5, ncol=2, loc='upper left')
    save(fig, 'fig_4_11_tomato_2023')
    # horizon WAPE (script 12)
    p = pd.read_csv(REP/'koyambedu_model_predictions.csv'); p['ae'] = (p.predicted_observed_inr_per_kg-p.actual_observed_inr_per_kg).abs()
    w = p.groupby(['model', 'horizon_days']).apply(lambda g: g.ae.sum()/g.actual_observed_inr_per_kg.sum()*100).unstack()
    w = w.loc[['NaiveLast', 'SeasonalNaive7', 'SARIMA', 'XGBoost', 'RandomForest', 'Prophet']]
    w.round(2).to_csv(REP/'koyambedu_wape_by_horizon.csv')
    fig, ax = plt.subplots(figsize=(6.6, 2.9)); xx = np.arange(3); bw = .13
    for i, mname in enumerate(w.index):
        ax.bar(xx+(i-2.5)*bw, w.loc[mname].values, bw, label=mname, color=C[mname])
    ax.set_xticks(xx); ax.set_xticklabels(['7 days', '14 days', '30 days']); ax.set_ylabel('WAPE (%)')
    ax.set_title('Koyambedu: WAPE by forecast horizon (7 origins × 8 series)'); ax.legend(ncol=6, fontsize=6.5, loc='upper center', bbox_to_anchor=(.5, -.12)); save(fig, 'fig_4_12_koyambedu_horizon')
    # monsoon forest plot
    hac = pd.read_csv(POE/'monsoon_association_hac.csv')
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8), sharey=True)
    for ax, (coef, se, title) in zip(axes, [('rain_anomaly_coef', 'rain_anomaly_hac_se', 'Rainfall anomaly (7-day)'), ('price_momentum_coef', None, 'Prior 7-day price momentum')]):
        y = np.arange(len(hac))
        if se:
            ax.errorbar(hac[coef], y, xerr=1.96*hac[se], fmt='o', color='#1f77b4', capsize=2)
        else:
            ax.scatter(hac[coef], y, color='#d62728')
        ax.axvline(0, color='k', lw=.7); ax.set_title(title); ax.set_yticks(y); ax.set_yticklabels(hac.commodity)
    axes[0].set_xlabel('Coefficient, 95% HAC CI'); axes[1].set_xlabel('Coefficient (all p < 0.03)')
    fig.suptitle('Seven-day forward price return regressions (n = 1,000 per commodity)', fontweight='bold', fontsize=9.5); fig.tight_layout()
    save(fig, 'fig_4_13_monsoon_hac')
    # procurement backtest
    s = pd.read_csv(REP/'koyambedu_procurement_advice_summary.csv')
    fig, ax = plt.subplots(figsize=(6.0, 2.6)); col = ['#2ca02c' if v > 0 else '#d62728' if v < 0 else '#7f7f7f' for v in s.mean_counterfactual_difference_inr]
    ax.bar(s.advice_action.str.title().str.replace(' ', '\n'), s.mean_counterfactual_difference_inr, color=col)
    for i, (v, n) in enumerate(zip(s.mean_counterfactual_difference_inr, s.cases)): ax.text(i, v+10 if v >= 0 else v-12, f'₹{v:.0f} (n={n})', ha='center', va='bottom' if v >= 0 else 'top', fontsize=7)
    ax.set_ylim(min(-60, s.mean_counterfactual_difference_inr.min()-50), s.mean_counterfactual_difference_inr.max()*1.25)
    ax.axhline(0, color='k', lw=.7); ax.set_ylabel('Mean ₹ saved vs buy-now\nper 100 kg lot'); ax.tick_params(axis='x', labelsize=7.5)
    ax.set_title('Procurement backtest: counterfactual result by advice action'); save(fig, 'fig_4_14_backtest')


def agents():
    rep = json.load(open(REP/'agrisight_pipeline_report.json'))
    a = rep['analysis']; f = rep['forecasts']; r = rep['intelligence']
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for c in a:
        ax.scatter(a[c]['cv_30d']*100, abs(a[c]['z_30d']), s=40+abs(f[c]['change_14d_pct'])*20,
                   color={'HIGH': '#d62728', 'MEDIUM': '#ff7f0e', 'LOW': '#2ca02c'}[r[c]['risk']], alpha=.8)
        ax.annotate(c, (a[c]['cv_30d']*100, abs(a[c]['z_30d'])), fontsize=7.5, xytext=(4, 3), textcoords='offset points')
    ax.set_xlabel('30-day coefficient of variation (%)'); ax.set_ylabel('|30-day z-score| of latest price')
    ax.set_title('Market Intelligence agent: risk matrix at 20 Apr 2026'); save(fig, 'fig_4_15_risk_matrix')


if __name__ == '__main__':
    workflow(); statewide_desc(); statewide_models(); shap_fig(); koyambedu(); agents()
