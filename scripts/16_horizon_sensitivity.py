"""Horizon sensitivity check for the statewide tree models (scripts 04/07).

Script 04 builds every price feature from information up to t-1 (rolling means,
EMAs and momentum use shift(1); cross_<commodity>_lag1 includes the model's own
commodity). The script-07 target is the same-day price, so its holdout scores
measure NEXT-DAY skill even though features are named lag_7..lag_30.

This script reruns the script-07 protocol (final 90 rows, expanding 30-day refits)
and compares:
  Naive_t-1          yesterday's price
  Naive_t-7          price seven days earlier
  XGB_original       script-07 feature set (next-day information)
  XGB_no_own_lag1    original set minus cross_<own>_lag1
  XGB_strict_7day    every price/cross feature rebuilt from t-7 and earlier only
Outputs: outputs/reports/horizon_sensitivity.csv and _by_commodity.csv
"""
import numpy as np, pandas as pd
from xgboost import XGBRegressor
from agrisight_common import PROC, REPORT, COMMODITIES

FEATURES = ['lag_7','lag_14','lag_21','lag_30','rolling_mean_7','rolling_mean_14','rolling_std_7',
            'rolling_std_14','rolling_min_7','rolling_max_7','ema_7','ema_14','momentum_7','momentum_14',
            'momentum_30','price_acceleration','position_52w','month','week_of_year','day_of_week',
            'sw_monsoon','ne_monsoon','pongal','tamil_new_year','diwali','navratri','market_count',
            'rain_7d_sum','rain_30d_sum','temp_max'] + ['cross_'+c+'_lag1' for c in COMMODITIES]
CAL = ['month','week_of_year','day_of_week','sw_monsoon','ne_monsoon','pongal','tamil_new_year','diwali','navratri']


def xgb():
    return XGBRegressor(n_estimators=400, max_depth=5, learning_rate=.05, subsample=.8, colsample_bytree=.8,
                        min_child_weight=3, reg_alpha=.1, reg_lambda=1, objective='reg:squarederror',
                        random_state=42, n_jobs=-1, verbosity=0)


def walk(tr, te, feats):
    preds = []
    for start in range(0, len(te), 30):
        fit = pd.concat([tr, te.iloc[:start]])
        m = xgb().fit(fit[feats], fit.modal_price)
        preds.extend(m.predict(te.iloc[start:start+30][feats]))
    return np.asarray(preds)


def strict_features(g, cross, h=7):
    """Rebuild price features so the newest information used is t-h."""
    p = g.modal_price
    x = pd.DataFrame(index=g.index)
    base = p.shift(h)
    for n in (0, 7, 14, 23):
        x[f's_lag_{h+n}'] = base.shift(n)
    for n in (7, 14, 30):
        x[f's_mean_{n}'] = base.rolling(n).mean(); x[f's_std_{n}'] = base.rolling(n).std()
        x[f's_ema_{n}'] = base.ewm(span=n, adjust=False).mean()
    x['s_mom_7'] = base.pct_change(7); x['s_mom_14'] = base.pct_change(14)
    roll = base.rolling(365, min_periods=30)
    x['s_pos_52w'] = (base-roll.min())/(roll.max()-roll.min()).replace(0, np.nan)
    for c in COMMODITIES:
        if c in cross: x[f's_cross_{c}'] = g.arrival_date.map(cross[c].shift(h-1)).values
    return x


def mape(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(np.mean(np.abs((y-p)/np.maximum(np.abs(y), 1e-8)))*100)


def main():
    d = pd.read_parquet(PROC/'tn_features.parquet'); d['arrival_date'] = pd.to_datetime(d.arrival_date)
    cross = d.pivot(index='arrival_date', columns='commodity', values='modal_price').shift(1)
    rows = []
    for c, g in d.groupby('commodity'):
        g = g.sort_values('arrival_date').replace([np.inf, -np.inf], np.nan).reset_index(drop=True)
        s = strict_features(g.set_index(g.arrival_date).assign(arrival_date=g.arrival_date.values), cross)
        s.index = g.index; sfeats = list(s.columns) + CAL + ['rain_7d_sum', 'rain_30d_sum', 'temp_max']
        g = pd.concat([g, s], axis=1)
        g['naive_1'] = g.modal_price.shift(1); g['naive_7'] = g.modal_price.shift(7)
        g = g.dropna(subset=FEATURES+sfeats+['modal_price', 'naive_1', 'naive_7']).reset_index(drop=True)
        tr, te = g.iloc[:-90], g.iloc[-90:]
        no_own = [f for f in FEATURES if f != f'cross_{c}_lag1']
        res = {'Naive_t-1': te.naive_1.values, 'Naive_t-7': te.naive_7.values,
               'XGB_original': walk(tr, te, FEATURES), 'XGB_no_own_lag1': walk(tr, te, no_own),
               'XGB_strict_7day': walk(tr, te, sfeats)}
        for name, p in res.items():
            rows.append({'commodity': c, 'variant': name, 'mape_pct': mape(te.modal_price, p),
                         'mae': float(np.mean(np.abs(te.modal_price.values-p))), 'n_test': len(te)})
        print(c, {k: round(mape(te.modal_price, v), 2) for k, v in res.items()}, flush=True)
    by = pd.DataFrame(rows); by.to_csv(REPORT/'horizon_sensitivity_by_commodity.csv', index=False)
    summ = by.groupby('variant', sort=False)[['mape_pct', 'mae']].mean().reset_index()
    summ.to_csv(REPORT/'horizon_sensitivity.csv', index=False); print(summ.round(2).to_string(index=False))


if __name__ == '__main__':
    main()
