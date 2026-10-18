"""Exploratory research analysis of published Koyambedu observations."""
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
DATA=ROOT/'data'/'secondary'/'koyambedu_prices_daily.csv'
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
    d=pd.read_csv(DATA,parse_dates=['date'])
    if not d['is_validated_observation'].astype(str).str.lower().eq('true').all(): raise ValueError('Input contains rows not labeled observed')

    cache=REPORT/'koyambedu_model_predictions.csv'; preds=[]; errors=[]
    for commodity,g in d.groupby('commodity',sort=True):
        g=g.sort_values('date').reset_index(drop=True); dates=pd.DatetimeIndex(g.date); y=g.observed_price_inr_per_kg.to_numpy(float)
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
                current={'date':str(target.date()),'origin':str(origin.date()),'commodity':commodity,'horizon_days':h,'actual_observed_inr_per_kg':actual}
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
                    current_row=dict(current,model=model,predicted_observed_inr_per_kg=max(0.01,float(pred)))
                    preds.append(current_row)
    pred=pd.DataFrame(preds)
    if pred.empty: raise RuntimeError('No model predictions were produced')
    pred.to_csv(REPORT/'koyambedu_model_predictions.csv',index=False,float_format='%.4f')
    rows=[]
    for model,g in pred.groupby('model',sort=False): rows.append({'model':model,**metrics(g.actual_observed_inr_per_kg,g.predicted_observed_inr_per_kg),'origins':int(g.origin.nunique()),'commodities':int(g.commodity.nunique()),'horizons':','.join(map(str,sorted(g.horizon_days.unique()))),'status':'SECONDARY_DATA_EXPLORATORY'})
    overall=pd.DataFrame(rows).sort_values('wape_pct'); overall.to_csv(REPORT/'koyambedu_model_metrics.csv',index=False,float_format='%.4f')
    by=pd.DataFrame([{'commodity':c,'model':m,**metrics(g.actual_observed_inr_per_kg,g.predicted_observed_inr_per_kg),'status':'SECONDARY_DATA_EXPLORATORY'} for (c,m),g in pred.groupby(['commodity','model'])])
    by.to_csv(REPORT/'koyambedu_model_metrics_by_commodity.csv',index=False,float_format='%.4f')
    pd.DataFrame(errors,columns=['commodity','origin','horizon','model','error']).to_csv(REPORT/'koyambedu_model_run_errors.csv',index=False)

    # Descriptive NE-monsoon data only: observed weather covers just two complete seasons.
    weather=(pd.read_csv(WEATHER,parse_dates=['date']) if WEATHER.exists()
             else pd.read_parquet(WEATHER.with_suffix('.parquet')))
    weather['date']=pd.to_datetime(weather['date']); weather['rain_mm']=pd.to_numeric(weather.get('precipitation',weather.get('rain')),errors='coerce')
    weather['year']=weather.date.dt.year; weather['month']=weather.date.dt.month
    w=weather.loc[weather.month.isin([10,11,12])].groupby(['year','month'],as_index=False).rain_mm.sum()
    w=w.loc[w.year.isin([2024,2025])].copy(); w['season_year']=w.year
    price_month=d.assign(year=d.date.dt.year,month=d.date.dt.month).groupby(['commodity','year','month'],as_index=False).observed_price_inr_per_kg.mean()
    price_month['prev_month_price']=price_month.sort_values(['commodity','year','month']).groupby('commodity').observed_price_inr_per_kg.shift(1)
    price_month['monthly_price_change_pct']=(price_month.observed_price_inr_per_kg/price_month.prev_month_price-1)*100
    pm=price_month.loc[price_month.month.isin([10,11,12]) & price_month.year.isin([2024,2025])]
    mon=pm.merge(w,on=['year','month'],how='inner')
    mon.to_csv(REPORT/'koyambedu_monsoon_descriptive.csv',index=False,float_format='%.4f')
    season_rain=w.groupby('year').rain_mm.sum().to_dict()

    # Tomato event summary uses the observed website series; it is descriptive arithmetic, not a real event estimate.
    tomo=d.loc[(d.commodity=='Tomato') & d.date.between('2023-07-03','2023-08-22')].copy()
    peak=tomo.loc[tomo.observed_price_inr_per_kg.idxmax()]
    first=tomo.loc[tomo.date.eq(pd.Timestamp('2023-07-03'))].iloc[0]
    last=tomo.loc[tomo.date.eq(pd.Timestamp('2023-08-22'))].iloc[0]
    event={'status':'SECONDARY_DATA_OBSERVED_SERIES','period_start':'2023-07-03','period_end':'2023-08-22','start_observed_price_inr_per_kg':float(first.observed_price_inr_per_kg),'peak_observed_price_inr_per_kg':float(peak.observed_price_inr_per_kg),'peak_date':str(peak.date.date()),'end_observed_price_inr_per_kg':float(last.observed_price_inr_per_kg),'start_to_peak_change_pct':float((peak.observed_price_inr_per_kg/first.observed_price_inr_per_kg-1)*100),'peak_to_end_change_pct':float((last.observed_price_inr_per_kg/peak.observed_price_inr_per_kg-1)*100),'procurement_savings_estimate':None,'savings_reason':'No purchase quantities, decision baseline, or actual transactions are available.'}
    (REPORT/'koyambedu_tomato_event_summary.json').write_text(json.dumps(event,indent=2),encoding='utf-8')

    model_table=overall[['model','n_predictions','rmse_inr_per_kg','mae_inr_per_kg','mape_pct','smape_pct','wape_pct','origins','commodities','horizons']].to_markdown(index=False,floatfmt='.2f')
    e_lines='\n'.join(f"- {r['model']} at {r.get('origin','')}: {r['error']}" for r in errors[:12]) or '- None.'
    report=f'''# Koyambedu Research Analysis — AgriSight Koyambedu

**Status: exploratory secondary-data analysis.** This is an exploratory analysis of genuine daily secondary observations retrieved from the Koyambedu history API and attributed to the Koyambedu Vegetable Merchants' Council. The site API identifies the unit as 1kg; no interpolation is applied.

## Data and scope

- Eight separate published series; {len(d):,} daily observed rows, {d.date.min().date()} to {d.date.max().date()}.
- All eight series copy the website `yValue` source observation directly. Tomato values from 2023-07-03 through 2023-08-22 are copied directly from daily source responses; no interpolation is used.
- No varieties were combined. French Beans to Beans mapping remains provisional.
- API unit label is 1kg; the quote's wholesale/retail basis and Council data chain are unverified.
- Weather is observed Chennai data only from 2024 onward; no weather values were fabricated.

## Forecast comparison

Models were evaluated on common expanding-window origins ({', '.join(ORIGIN_TEXT)}), the same eight commodities, and 7-, 14-, and 30-day direct horizons. At each origin, only price history available on or before that date was used. Metrics aggregate stored predictions across all origins, series, and horizons. WAPE and MAE are emphasized because MAPE can over-weight low-price periods. Results are exploratory and source-qualified.

{model_table}

The lowest-WAPE method on this selected website panel is **{overall.iloc[0].model}** ({overall.iloc[0].wape_pct:.2f}% WAPE), with **{overall.iloc[0].n_predictions}** scored predictions. This ranks methods only on the selected published site series; it does not establish out-of-source market accuracy. Per-series/per-horizon predictions are in `koyambedu_model_predictions.csv`; per-commodity metrics are in `koyambedu_model_metrics_by_commodity.csv`.

### Run notes

{e_lines}

## Northeast Monsoon

The descriptive table joins observed weather and prices in `koyambedu_monsoon_descriptive.csv` by joining observed weather to observed monthly price summaries for October–December 2024 and 2025. The weather file contains only two complete Northeast Monsoon seasons for this period and no long climatological baseline. Findings remain descriptive/limited evidence; no significance or causal claim is made. This objective remains open for the real study.

Observed rainfall totals in the available complete seasons (mm): {json.dumps({int(k):round(float(v),1) for k,v in season_rain.items()})}.

## Tomato price-episode findings

The Tomato observations move from ₹{event['start_observed_price_inr_per_kg']:.0f}/kg on {event['period_start']} to an observed peak of ₹{event['peak_observed_price_inr_per_kg']:.0f}/kg on {event['peak_date']} ({event['start_to_peak_change_pct']:.1f}%), then reaches ₹{event['end_observed_price_inr_per_kg']:.0f}/kg on {event['period_end']}. These are direct daily website values with no interpolation; the wholesale price basis is not independently audited. The proposal's ₹200/kg figure is not established as Koyambedu wholesale by this analysis.

No realized procurement savings are calculated: buyer transaction records, purchasing quantities, and a decision baseline are unavailable. A price spike alone cannot support a savings claim.

## Source citation

Vegetable Market Price. "Koyambedu Market Price History." https://vegetablemarketprice.com/market/koyambedu/history. Accessed on the extraction date; daily yValue fields were retained unchanged. The data are attributed to the Koyambedu Vegetable Merchants' Council.

## Conclusion and limitations

This run demonstrates that the data pipeline can produce aligned multi-horizon forecasts and reports for eight series. It does **not** complete the empirical research analysis. Before thesis claims, verify quote basis and source attribution; obtain historical rainfall covering the chosen price period; predefine the monsoon index and time-series inference; validate mappings; rerun the common evaluation protocol; and define procurement inputs before calculating hypothetical savings.
'''
    (REPORT/'koyambedu_research_analysis.md').write_text(report,encoding='utf-8')
    print(json.dumps({'prediction_rows':len(pred),'model_metrics':overall.to_dict(orient='records'),'run_errors':len(errors),'monsoon_rows':len(mon),'tomato_event':event,'report':str(REPORT/'koyambedu_research_analysis.md')},indent=2,default=float))

if __name__=='__main__': main()
