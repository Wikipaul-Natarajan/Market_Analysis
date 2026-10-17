"""Evaluate proposal gaps with a shared, source-qualified Koyambedu protocol.

The extracted history contains direct daily source observations. Outputs are exploratory and must not be presented as realized procurement savings.
"""
from __future__ import annotations
import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.stattools import durbin_watson
import statsmodels.api as sm
from prophet import Prophet

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/external/koyambedu_vegetablemarketprice_history.csv'
WEATHER = ROOT / 'data/external/weather_chennai.csv'
OUT = ROOT / 'outputs/proposal_objective_evaluation'
SOURCE_STATUS = 'SECONDARY_DATA_KOYAMBEDU_MERCHANTS_COUNCIL'
SERIES = {'Tomato':'tomato','Onion':'onionbig','Potato':'potato','Cabbage':'cabbage',
          'Carrot':'carrot','Beans':'frenchbeans','Brinjal':'brinjal','Drumstick':'drumsticks'}
HORIZONS = (7, 14, 30)
FEATURES = ('lag_1','lag_7','lag_14','lag_30','mean_7','mean_30','std_30','dow','week','month')


def load_series():
    if not SOURCE.exists(): raise FileNotFoundError(f'Missing local source: {SOURCE}')
    d = pd.read_csv(SOURCE, parse_dates=['date'])
    d['price_value'] = pd.to_numeric(d['price_value'], errors='coerce')
    return d


def features_for(s):
    x = pd.DataFrame(index=s.index)
    for lag in (1,7,14,30): x[f'lag_{lag}'] = s.shift(lag)
    x['mean_7'] = s.shift(1).rolling(7).mean()
    x['mean_30'] = s.shift(1).rolling(30).mean()
    x['std_30'] = s.shift(1).rolling(30).std()
    x['dow'] = x.index.dayofweek; x['week'] = x.index.isocalendar().week.astype(int).to_numpy()
    x['month'] = x.index.month
    return x


def score(y, p):
    y, p = np.asarray(y,float), np.asarray(p,float)
    return {'rmse':float(np.sqrt(mean_squared_error(y,p))),
            'mae':float(mean_absolute_error(y,p)),
            'mape_pct':float(np.mean(np.abs((y-p)/np.maximum(np.abs(y),1e-8)))*100)}


def origin_dates(common_dates):
    dates = pd.DatetimeIndex(common_dates).sort_values()
    if len(dates) < 500: raise ValueError('Not enough consecutive observations for the prespecified evaluation windows.')
    start, end = dates.max()-pd.Timedelta(days=420), dates.max()-pd.Timedelta(days=30)
    proposed = pd.date_range(start, end, freq='120D')
    chosen = [d for d in proposed if d in dates and all((d+pd.Timedelta(days=h)) in dates for h in HORIZONS)]
    return chosen


def fit_classic(s, origin, horizon):
    train = s.loc[:origin].astype(float)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        fit = SARIMAX(train, order=(1,1,1), seasonal_order=(1,1,1,7),
                      enforce_stationarity=False, enforce_invertibility=False).fit(disp=False,maxiter=60)
    sarima = fit.forecast(horizon)
    pf = pd.DataFrame({'ds':train.index,'y':train.values})
    pm = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False,
                 seasonality_mode='multiplicative', uncertainty_samples=0)
    pm.fit(pf)
    future = pm.make_future_dataframe(periods=horizon, freq='D', include_history=True)
    prophet = pm.predict(future).yhat.iloc[-horizon:]
    return sarima, prophet


def models_for_horizon(x, s, origin, horizon):
    target = s.shift(-horizon).rename('target')
    frame = x.join(target).dropna(subset=list(FEATURES)+['target'])
    train = frame.loc[frame.index + pd.to_timedelta(horizon,unit='D') <= origin]
    if len(train) < 180: raise ValueError(f'Only {len(train)} target-known training rows at {origin.date()}.')
    row = x.loc[[origin],list(FEATURES)]
    rf = RandomForestRegressor(n_estimators=180,max_depth=10,min_samples_leaf=4,max_features=.8,n_jobs=-1,random_state=42)
    xgb = XGBRegressor(n_estimators=240,max_depth=4,learning_rate=.04,subsample=.8,colsample_bytree=.8,
                       min_child_weight=4,reg_alpha=.1,reg_lambda=1,objective='reg:squarederror',
                       random_state=42,n_jobs=2,verbosity=0)
    rf.fit(train[list(FEATURES)],train.target); xgb.fit(train[list(FEATURES)],train.target)
    return float(rf.predict(row)[0]), float(xgb.predict(row)[0])


def evaluate_models(data):
    # Use only eight explicit one-to-one IDs. Never collapse website varieties.
    selected = data[data.veg_id.isin(SERIES.values())].copy()
    pivot = selected.pivot(index='date',columns='veg_id',values='price_value').sort_index()
    dates = pivot.dropna(subset=list(SERIES.values())).index
    origins = origin_dates(dates)
    predictions=[]
    for commodity, veg_id in SERIES.items():
        s = pivot[veg_id].dropna().sort_index().astype(float)
        x = features_for(s)
        for origin in origins:
            if origin not in s.index: continue
            try:
                sarima_forecast, prophet_forecast = fit_classic(s,origin,max(HORIZONS))
                classic_error = None
            except Exception as exc:
                sarima_forecast = prophet_forecast = None
                classic_error = str(exc)[:180]
            for h in HORIZONS:
                try:
                    rf, xv = models_for_horizon(x,s,origin,h)
                    actual = float(s.loc[origin+pd.Timedelta(days=h)])
                    vals=[('RF',rf),('XGBoost',xv),('SeasonalNaive',float(s.loc[origin]))]
                    if sarima_forecast is not None:
                        vals.extend([('SARIMA',float(sarima_forecast.iloc[h-1])),('Prophet',float(prophet_forecast.iloc[h-1]))])
                    else:
                        predictions.append({'commodity':commodity,'veg_id':veg_id,'origin':origin.date().isoformat(),
                                            'horizon_days':h,'model':'SARIMA/Prophet','prediction':np.nan,
                                            'error':classic_error,'source_status':SOURCE_STATUS})
                    for name,val in vals:
                        predictions.append({'commodity':commodity,'veg_id':veg_id,'origin':origin.date().isoformat(),
                                            'target_date':(origin+pd.Timedelta(days=h)).date().isoformat(),
                                            'horizon_days':h,'model':name,'actual':actual,'prediction':max(0.0,val),
                                            'source_status':SOURCE_STATUS})
                except Exception as exc:
                    predictions.append({'commodity':commodity,'veg_id':veg_id,'origin':origin.date().isoformat(),
                                        'horizon_days':h,'model':'evaluation_error','error':str(exc)[:220],
                                        'source_status':SOURCE_STATUS})

    pred=pd.DataFrame(predictions); pred.to_csv(OUT/'common_horizon_predictions.csv',index=False)
    valid=pred.dropna(subset=['actual','prediction'])
    rows=[]
    for (commodity,h,name),g in valid.groupby(['commodity','horizon_days','model']):
        rows.append({'commodity':commodity,'horizon_days':int(h),'model':name,'n_origins':len(g),**score(g.actual,g.prediction),
                     'source_status':SOURCE_STATUS})
    summary=pd.DataFrame(rows); summary.to_csv(OUT/'common_horizon_metrics.csv',index=False)
    return summary, pred, origins


def monsoon_analysis(data):
    if not WEATHER.exists():
        return pd.DataFrame(), 'Local Chennai weather file is missing; monsoon analysis not run.'
    w=pd.read_csv(WEATHER,parse_dates=['arrival_date'])
    rain_col='precipitation' if 'precipitation' in w else 'rain'
    w[rain_col]=pd.to_numeric(w[rain_col],errors='coerce')
    # Within-available-period month anomaly, explicitly not a long-run climatological deviation.
    month_stats=w.groupby(w.arrival_date.dt.month)[rain_col].agg(['mean','std']).rename(columns={'mean':'month_rain_mean','std':'month_rain_sd'})
    w=w.join(month_stats,on=w.arrival_date.dt.month)
    w['rain_anomaly_z_sample']=(w[rain_col]-w.month_rain_mean)/w.month_rain_sd.replace(0,np.nan)
    w=w.sort_values('arrival_date'); w['rain_anomaly_7d']=w.rain_anomaly_z_sample.rolling(7,min_periods=5).mean()
    w['rainfall_source_window_years']=w.arrival_date.dt.year.nunique()
    selected=data[data.veg_id.isin(SERIES.values())].copy(); selected['date']=pd.to_datetime(selected.date)
    rows=[]
    for commodity,veg_id in SERIES.items():
        g=selected[selected.veg_id.eq(veg_id)].sort_values('date').copy()
        g['price_value']=pd.to_numeric(g.price_value,errors='coerce'); g['price_log']=np.log(g.price_value.where(g.price_value>0))
        g['price_return_7d']=(g.price_log.shift(-7)-g.price_log)*100
        g['price_momentum_7d']=(g.price_log-g.price_log.shift(7))*100
        z=g.merge(w[['arrival_date','rain_anomaly_7d','rainfall_source_window_years']],left_on='date',right_on='arrival_date',how='inner')
        z=z.dropna(subset=['price_return_7d','price_momentum_7d','rain_anomaly_7d'])
        if len(z)<50:
            rows.append({'commodity':commodity,'n':len(z),'status':'INSUFFICIENT_OVERLAP','source_status':SOURCE_STATUS}); continue
        X=sm.add_constant(z[['rain_anomaly_7d','price_momentum_7d']].astype(float))
        fit=sm.OLS(z.price_return_7d.astype(float),X).fit(cov_type='HAC',cov_kwds={'maxlags':7})
        rows.append({'commodity':commodity,'n':len(z),'rain_anomaly_coef':float(fit.params['rain_anomaly_7d']),
                     'rain_anomaly_hac_se':float(fit.bse['rain_anomaly_7d']),'rain_anomaly_pvalue':float(fit.pvalues['rain_anomaly_7d']),
                     'price_momentum_coef':float(fit.params['price_momentum_7d']),'price_momentum_pvalue':float(fit.pvalues['price_momentum_7d']),
                     'r_squared':float(fit.rsquared),'hac_lags':7,'arrival_volume_available':False,
                     'source_status':SOURCE_STATUS,'inference_status':'EXPLORATORY_SHORT_WEATHER_HISTORY_NO_ARRIVAL_CONTROL'})
    result=pd.DataFrame(rows); result.to_csv(OUT/'monsoon_association_hac.csv',index=False)
    note=('Rainfall anomaly is standardized against the same calendar month within the local weather file, not a long-run climatology. '
          'HAC regression uses seven-day price return and controls for prior seven-day price momentum; market arrival volume is absent. '
          'The short local weather record (two complete Northeast Monsoon seasons) means p-values are exploratory and do not fulfill the proposal’s claim of a statistically established monsoon effect.')
    (OUT/'monsoon_method_note.txt').write_text(note+'\n',encoding='utf-8')
    return result,note


def crisis_scenario(data):
    # Proposal's retrospective scenario: period preceding the event named in the proposal.
    # This calculation is explicitly source-qualified and is not realized procurement savings.
    sdata=data[data.veg_id.eq('tomato')].copy(); sdata['date']=pd.to_datetime(sdata.date)
    sdata['price_value']=pd.to_numeric(sdata.price_value,errors='coerce')
    s=sdata.set_index('date').price_value.dropna().sort_index().astype(float)
    x=features_for(s); start=pd.Timestamp('2023-04-01'); end=pd.Timestamp('2023-06-30')
    origins=pd.date_range(start,end,freq='7D'); rows=[]
    for origin in origins:
        target=origin+pd.Timedelta(days=14)
        if origin not in x.index or target not in s.index: continue
        y=s.shift(-14).rename('target'); frame=x.join(y).dropna(subset=list(FEATURES)+['target'])
        train=frame.loc[frame.index+pd.Timedelta(days=14)<=origin]
        if len(train)<180: continue
        model=XGBRegressor(n_estimators=240,max_depth=4,learning_rate=.04,subsample=.8,colsample_bytree=.8,
                           min_child_weight=4,reg_alpha=.1,reg_lambda=1,objective='reg:squarederror',random_state=42,n_jobs=2,verbosity=0)
        model.fit(train[list(FEATURES)],train.target); predicted=max(0,float(model.predict(x.loc[[origin],list(FEATURES)])[0]))
        current=float(s.loc[origin]); future=float(s.loc[target]); change=(predicted/current-1)*100 if current else 0
        hist=s.loc[:origin].tail(30); cv=float(hist.std()/(hist.mean() or 1)); z=float((current-hist.mean())/(hist.std() or 1))
        risk_score=min(100,cv*120+abs(z)*12+abs(change)*1.2)
        risk='HIGH' if risk_score>=55 else 'MEDIUM' if risk_score>=28 else 'LOW'
        action='PROCURE NOW' if change>5 and risk!='HIGH' else 'DELAY PROCUREMENT' if change < -5 else 'PARTIAL PROCUREMENT' if risk=='HIGH' else 'HEDGE' if abs(change)>3 else 'HOLD'
        buy_now=current
        share=1.0 if action in ('PROCURE NOW','HOLD') else 0.0 if action=='DELAY PROCUREMENT' else .5
        advice_cost=share*current+(1-share)*future
        rows.append({'origin':origin.date().isoformat(),'target':target.date().isoformat(),'horizon_days':14,'model':'XGBoost',
                     'current_source_value':current,'predicted_source_value':predicted,'actual_source_value':future,
                     'action':action,'risk':risk,'scenario_difference_vs_buy_now_source_units':buy_now-advice_cost,
                     'source_status':SOURCE_STATUS,'economic_status':'SCENARIO_ONLY_NO_BUYER_OUTCOMES_OR_VALIDATED_PRICE_BASIS'})
    result=pd.DataFrame(rows); result.to_csv(OUT/'crisis_period_procurement_scenario.csv',index=False)
    if result.empty:
        return result, 'No eligible historical origins were available for the specified backtest window.'
    note=('A rule-based 14-day XGBoost counterfactual was run on the local Tomato candidate series. It assumes a normalized one-quote-unit purchase, '
          'compares the advice timing with buying entirely at the origin, and omits storage, transport, spoilage, quality, stockouts and inventory constraints. '
          'The observations are attributed to the Koyambedu Vegetable Merchants' Council. The API unit is 1kg; this analysis does not independently establish wholesale transaction basis or realized economic value/savings.')
    (OUT/'crisis_period_procurement_note.txt').write_text(note+'\n',encoding='utf-8')
    return result,note


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=load_series(); summary,pred,origins=evaluate_models(d)
    mono,mono_note=monsoon_analysis(d); savings,savings_note=crisis_scenario(d)
    meta={'source_status':SOURCE_STATUS,'source':'Vegetable Market Price, Koyambedu history API; attributed to Koyambedu Vegetable Merchants Council; https://vegetablemarketprice.com/market/koyambedu/history',
          'evaluation_origins':[x.date().isoformat() for x in origins],'horizons_days':list(HORIZONS),
          'commodities':list(SERIES),'models':['SARIMA','Prophet','RF','XGBoost','SeasonalNaive'],
          'monsoon_note':mono_note,'procurement_note':savings_note,
          'benchmark_note':'Published Koyambedu SARIMA study reports monthly series/horizon metrics; those are not directly comparable with these daily 7/14/30-day matched-origin scores. No numeric cross-study delta is claimed.',
          'proposal_status':{'model_comparison':'IMPLEMENTED_EXPLORATORY_SECONDARY_DATA',
                             'monsoon_test':'IMPLEMENTED_EXPLORATORY_ARRIVALS_MISSING_AND_WEATHER_WINDOW_SHORT',
                             'procurement_case':'IMPLEMENTED_SCENARIO_ONLY_SOURCE_UNVERIFIED'}}
    (OUT/'objective_evaluation_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    lines=['# Proposal objective evaluation outputs','',
           f'Source disposition: **{SOURCE_STATUS}**. These outputs are exploratory price-series accuracy results and must not be represented as realized procurement savings.','',
           '## Matched horizon model evaluation','',
           f'Common origin dates: {", ".join(meta["evaluation_origins"])}. Horizons: 7, 14 and 30 days. Models use the same origin and target dates; SeasonalNaive is included as a baseline. See `common_horizon_metrics.csv` and row-level `common_horizon_predictions.csv`.','',
           'The published benchmark is monthly and does not provide directly comparable daily 7/14/30-day forecasts; cross-study numeric comparison is therefore withheld.','',
           '## Monsoon association','',mono_note,'','Market arrivals are not available in the local price panel.','',
           '## Procurement scenario','',savings_note,'',
           'Source citation: Vegetable Market Price. Koyambedu Market Price History. https://vegetablemarketprice.com/market/koyambedu/history (daily API values, accessed at extraction). The API unit is labeled 1kg. Procurement outputs are counterfactuals, not realized savings.']
    (OUT/'objective_evaluation_readme.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Wrote {len(pred)} prediction/error rows; {len(summary)} metric rows; {len(mono)} weather-association rows; {len(savings)} scenario rows to {OUT}')

if __name__=='__main__': main()

