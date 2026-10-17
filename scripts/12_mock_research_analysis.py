"""Demonstration-only research analysis for the clearly labeled Koyambedu mock panel."""
from __future__ import annotations
import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from prophet import Prophet
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings("ignore")
ROOT=Path(__file__).resolve().parents[1]
MOCK=ROOT/'data'/'mock'/'koyambedu_mock_prices_daily.csv'
WEATHER=ROOT/'data'/'external'/'weather_chennai.csv'
REPORT=ROOT/'outputs'/'reports'; REPORT.mkdir(parents=True,exist_ok=True)
HORIZONS=(7,14,30)
ORIGIN_TEXT=('2025-01-01','2025-04-01','2025-07-01','2025-10-01','2026-01-01','2026-04-01','2026-07-01')
ORIGINS=pd.to_datetime(ORIGIN_TEXT)


def feature_row(y, dates, issue_i, horizon):
    hist=y[:issue_i+1]
    target=dates[issue_i]+pd.Timedelta(days=horizon)
    def lag(n): return float(hist[-n])
    vals=[lag(1),lag(7),lag(14),lag(30),float(np.mean(hist[-7:])),float(np.std(hist[-7:])),float(np.mean(hist[-30:])),float(np.std(hist[-30:])),float(np.min(hist[-30:])),float(np.max(hist[-30:])),float((hist[-1]/hist[-8]-1)*100 if hist[-8] else 0)]
    doy=target.dayofyear; dow=target.dayofweek
    vals.extend([np.sin(2*np.pi*doy/365.25),np.cos(2*np.pi*doy/365.25),np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),target.month/12.0])
    return np.asarray(vals,dtype=float)

FEATURE_NAMES=['lag_1','lag_7','lag_14','lag_30','mean_7','std_7','mean_30','std_30','min_30','max_30','momentum_7_pct','target_year_sin','target_year_cos','target_weekday_sin','target_weekday_cos','target_month_scaled']


def metrics(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float); e=p-y
    return {'n_predictions':int(len(y)),'rmse_inr_per_kg':float(np.sqrt(np.mean(e*e))),'mae_inr_per_kg':float(np.mean(np.abs(e))),'mape_pct':float(np.mean(np.abs(e)/np.maximum(np.abs(y),1e-8))*100),'smape_pct':float(np.mean(200*np.abs(e)/(np.abs(y)+np.abs(p)+1e-8))),'wape_pct':float(np.sum(np.abs(e))/max(np.sum(np.abs(y)),1e-8)*100)}


def main():
    d=pd.read_csv(MOCK,parse_dates=['date'])
    if not d['is_mock_data'].astype(str).str.lower().eq('true').all(): raise ValueError('Input contains rows not labeled mock')
    if d['is_validated_observation'].astype(str).str.lower().eq('true').any(): raise ValueError('Mock input incorrectly claims validated observations')
    cache=REPORT/'mock_model_predictions.csv'; preds=pd.read_csv(cache).to_dict('records') if cache.exists() else []; errors=[]
    for commodity,g in ([] if cache.exists() else d.groupby('project_commodity_candidate',sort=True)):
        g=g.sort_values('date').reset_index(drop=True); dates=pd.DatetimeIndex(g.date); y=g.mock_price_inr_per_kg.to_numpy(float)
        if dates.has_duplicates or not np.all(np.diff(dates.values).astype('timedelta64[D]').astype(int)==1): raise ValueError(f'Non-daily/duplicate dates in {commodity}')
        for origin in ORIGINS:
            loc=np.flatnonzero(dates==origin)
            if not len(loc): continue
            oi=int(loc[0]); history_y=y[:oi+1]
            # One SARIMA and one Prophet fit per origin/series; all horizons use same fitted trajectory.
            sar_path=None; pro_path=None
            try:
                sf=SARIMAX(history_y,order=(1,1,1),seasonal_order=(1,1,1,7),enforce_stationarity=False,enforce_invertibility=False).fit(disp=False,maxiter=60)
                sar_path=np.asarray(sf.forecast(max(HORIZONS)),float)
            except Exception as exc: errors.append({'commodity':commodity,'origin':str(origin.date()),'model':'SARIMA','error':str(exc)[:250]})
            try:
                pf=Prophet(weekly_seasonality=True,yearly_seasonality=True,daily_seasonality=False,uncertainty_samples=0,changepoint_prior_scale=0.05)
                pf.fit(pd.DataFrame({'ds':dates[:oi+1],'y':history_y}))
                future=pd.DataFrame({'ds':pd.date_range(origin+pd.Timedelta(days=1),periods=max(HORIZONS),freq='D')})
                pro_path=pf.predict(future).yhat.to_numpy(float)
            except Exception as exc: errors.append({'commodity':commodity,'origin':str(origin.date()),'model':'Prophet','error':str(exc)[:250]})
            for h in HORIZONS:
                ti=oi+h
                if ti>=len(y): continue
                actual=float(y[ti]); target=dates[ti]
                last=float(y[oi]); seasonal=float(y[oi+h-7*((h+6)//7)])
                current={'date':str(target.date()),'origin':str(origin.date()),'commodity':commodity,'horizon_days':h,'actual_mock_inr_per_kg':actual}
                vals={'NaiveLast':last,'SeasonalNaive7':seasonal}
                if sar_path is not None: vals['SARIMA']=float(sar_path[h-1])
                if pro_path is not None: vals['Prophet']=float(pro_path[h-1])
                # Direct h-step learning. Every training target is available on or before the issue date.
                train_x=[]; train_y=[]
                for t in range(30,oi-h+1):
                    train_x.append(feature_row(y,dates,t,h)); train_y.append(float(y[t+h]))
                x_eval=feature_row(y,dates,oi,h).reshape(1,-1)
                if len(train_y)>=60:
                    try:
                        rf=RandomForestRegressor(n_estimators=120,min_samples_leaf=3,max_features=0.9,n_jobs=-1,random_state=42)
                        rf.fit(np.asarray(train_x),np.asarray(train_y)); vals['RandomForest']=float(rf.predict(x_eval)[0])
                    except Exception as exc: errors.append({'commodity':commodity,'origin':str(origin.date()),'horizon':h,'model':'RandomForest','error':str(exc)[:250]})
                    try:
                        xm=XGBRegressor(n_estimators=100,max_depth=3,learning_rate=0.05,subsample=0.85,colsample_bytree=0.9,reg_lambda=1.0,objective='reg:squarederror',random_state=42,n_jobs=1,verbosity=0)
                        xm.fit(np.asarray(train_x),np.asarray(train_y)); vals['XGBoost']=float(xm.predict(x_eval)[0])
                    except Exception as exc: errors.append({'commodity':commodity,'origin':str(origin.date()),'horizon':h,'model':'XGBoost','error':str(exc)[:250]})
                for model,pred in vals.items():
                    current_row=dict(current,model=model,predicted_mock_inr_per_kg=max(0.01,float(pred)),is_demonstration_only=True)
                    preds.append(current_row)
    pred=pd.DataFrame(preds)
    if pred.empty: raise RuntimeError('No model predictions were produced')
    pred.to_csv(REPORT/'mock_model_predictions.csv',index=False,float_format='%.4f')
    rows=[]
    for model,g in pred.groupby('model',sort=False): rows.append({'model':model,**metrics(g.actual_mock_inr_per_kg,g.predicted_mock_inr_per_kg),'origins':int(g.origin.nunique()),'commodities':int(g.commodity.nunique()),'horizons':','.join(map(str,sorted(g.horizon_days.unique()))),'status':'MOCK_DEMONSTRATION_ONLY'})
    overall=pd.DataFrame(rows).sort_values('wape_pct'); overall.to_csv(REPORT/'mock_model_metrics.csv',index=False,float_format='%.4f')
    by=pd.DataFrame([{'commodity':c,'model':m,**metrics(g.actual_mock_inr_per_kg,g.predicted_mock_inr_per_kg),'status':'MOCK_DEMONSTRATION_ONLY'} for (c,m),g in pred.groupby(['commodity','model'])])
    by.to_csv(REPORT/'mock_model_metrics_by_commodity.csv',index=False,float_format='%.4f')
    pd.DataFrame(errors,columns=['commodity','origin','horizon','model','error']).to_csv(REPORT/'mock_model_run_errors.csv',index=False)

    # Descriptive NE-monsoon data only: observed weather covers just two complete seasons.
    weather=pd.read_csv(WEATHER,parse_dates=['date']); weather['rain_mm']=pd.to_numeric(weather.get('precipitation',weather.get('rain')),errors='coerce')
    weather['year']=weather.date.dt.year; weather['month']=weather.date.dt.month
    w=weather.loc[weather.month.isin([10,11,12])].groupby(['year','month'],as_index=False).rain_mm.sum()
    w=w.loc[w.year.isin([2024,2025])].copy(); w['season_year']=w.year
    price_month=d.assign(year=d.date.dt.year,month=d.date.dt.month).groupby(['project_commodity_candidate','year','month'],as_index=False).mock_price_inr_per_kg.mean()
    price_month['prev_month_price']=price_month.sort_values(['project_commodity_candidate','year','month']).groupby('project_commodity_candidate').mock_price_inr_per_kg.shift(1)
    price_month['monthly_price_change_pct']=(price_month.mock_price_inr_per_kg/price_month.prev_month_price-1)*100
    pm=price_month.loc[price_month.month.isin([10,11,12]) & price_month.year.isin([2024,2025])]
    mon=pm.merge(w,on=['year','month'],how='inner')
    mon.to_csv(REPORT/'mock_monsoon_descriptive.csv',index=False,float_format='%.4f')
    season_rain=w.groupby('year').rain_mm.sum().to_dict()

    # Tomato event summary uses the scenario panel; it is descriptive arithmetic, not a real event estimate.
    tomo=d.loc[(d.project_commodity_candidate=='Tomato') & d.date.between('2023-07-03','2023-08-22')].copy()
    peak=tomo.loc[tomo.mock_price_inr_per_kg.idxmax()]
    first=tomo.loc[tomo.date.eq(pd.Timestamp('2023-07-03'))].iloc[0]
    last=tomo.loc[tomo.date.eq(pd.Timestamp('2023-08-22'))].iloc[0]
    event={'status':'MOCK_SCENARIO_ONLY','period_start':'2023-07-03','period_end':'2023-08-22','start_mock_price_inr_per_kg':float(first.mock_price_inr_per_kg),'peak_mock_price_inr_per_kg':float(peak.mock_price_inr_per_kg),'peak_date':str(peak.date.date()),'end_mock_price_inr_per_kg':float(last.mock_price_inr_per_kg),'start_to_peak_change_pct':float((peak.mock_price_inr_per_kg/first.mock_price_inr_per_kg-1)*100),'peak_to_end_change_pct':float((last.mock_price_inr_per_kg/peak.mock_price_inr_per_kg-1)*100),'procurement_savings_estimate':None,'savings_reason':'No purchase quantities, decision baseline, or actual transactions are available.'}
    (REPORT/'mock_tomato_event_summary.json').write_text(json.dumps(event,indent=2),encoding='utf-8')

    model_table=overall[['model','n_predictions','rmse_inr_per_kg','mae_inr_per_kg','mape_pct','smape_pct','wape_pct','origins','commodities','horizons']].to_markdown(index=False,floatfmt='.2f')
    e_lines='\n'.join(f"- {r['model']} at {r.get('origin','')}: {r['error']}" for r in errors[:12]) or '- None.'
    report=f'''# Mock Research Analysis — AgriSight Koyambedu

**Status: DEMONSTRATION ONLY.** This is an end-to-end analytical exercise on `data/mock/koyambedu_mock_prices_daily.csv`, not an empirical study of observed Koyambedu wholesale prices. Every input row is labeled mock/unvalidated. Do not cite its forecasts or statistics as evidence about the real market.

## Data and scope

- Eight separate candidate series; {len(d):,} daily mock rows, {d.date.min().date()} to {d.date.max().date()}.
- Seven series copy the unvalidated website `yValue` proxy. Tomato from 2023-07-03 through 2023-08-22 uses the labeled press/site anchor interpolation scenario.
- No vegetable varieties were combined. The French Beans to Beans mapping remains provisional.
- Prices use the API's 1kg unit label, but price meaning remains unresolved.
- Weather is observed Chennai data only from 2024 onward; no weather values were fabricated.

## Forecast comparison

Models were evaluated on common expanding-window origins ({', '.join(ORIGIN_TEXT)}), the same eight commodities, and 7-, 14-, and 30-day direct horizons. At each origin, only price history available on or before that date was used. Metrics aggregate stored predictions across all origins, series, and horizons. WAPE and MAE are emphasized because MAPE can over-weight low-price periods. All results remain mock-only.

{model_table}

The most predictive method by WAPE on this generated panel is **{overall.iloc[0].model}** ({overall.iloc[0].wape_pct:.2f}% WAPE), with **{overall.iloc[0].n_predictions}** scored predictions. This ranks methods only on this particular proxy/synthetic panel; it does not establish real-world superiority. Per-series/per-horizon predictions are in `mock_model_predictions.csv`; per-commodity metrics are in `mock_model_metrics_by_commodity.csv`.

### Run notes

{e_lines}

## Northeast Monsoon

A descriptive table was generated in `mock_monsoon_descriptive.csv` by joining observed weather to mock monthly price summaries for October–December 2024 and 2025. The weather file contains only two complete Northeast Monsoon seasons for this period; it does not provide a long climatological baseline, and prices are mock/unvalidated. Therefore no formal significance test or causal monsoon conclusion is reported. This objective remains open for the real study.

Observed rainfall totals in the available complete seasons (mm): {json.dumps({int(k):round(float(v),1) for k,v in season_rain.items()})}.

## Tomato crisis scenario

The mock Tomato path rises from ₹{event['start_mock_price_inr_per_kg']:.0f}/kg on {event['period_start']} to a scenario peak of ₹{event['peak_mock_price_inr_per_kg']:.0f}/kg on {event['peak_date']} ({event['start_to_peak_change_pct']:.1f}%), then reaches ₹{event['end_mock_price_inr_per_kg']:.0f}/kg on {event['period_end']}. These values include interpolation between press/site anchors and are scenario construction, not a verified daily reconstruction. The proposal's ₹200/kg figure is not established as Koyambedu wholesale by this analysis.

No procurement savings are calculated: the project has no transaction records, purchasing quantities, baseline purchase rule, or validated price path. A mock price spike alone cannot support a savings claim.

## Conclusion and real-project requirements

This run demonstrates that the data pipeline can produce aligned multi-horizon forecasts and reports for eight series. It does **not** complete the empirical research analysis. Before thesis claims, replace the mock panel with a defensible Koyambedu wholesale series; obtain historical rainfall covering the chosen price period; predefine the monsoon index and time-series inference; validate mappings; rerun the common evaluation protocol; and define procurement inputs before calculating hypothetical savings.
'''
    (REPORT/'mock_research_analysis.md').write_text(report,encoding='utf-8')
    print(json.dumps({'prediction_rows':len(pred),'model_metrics':overall.to_dict(orient='records'),'run_errors':len(errors),'monsoon_rows':len(mon),'tomato_event':event,'report':str(REPORT/'mock_research_analysis.md')},indent=2,default=float))

if __name__=='__main__': main()


