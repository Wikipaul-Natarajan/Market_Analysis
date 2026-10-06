import pickle
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from prophet import Prophet
from sklearn.metrics import mean_squared_error,mean_absolute_error
from agrisight_common import PROC,REPORT,FIG,MODELS
HOLIDAYS=('Pongal','Tamil New Year','Ramadan End','Diwali','Navratri Start','Christmas','New Year')
def holiday_frame():
 rows=[]
 for year in range(2024,2027):
  # Tamil Nadu local holiday dates; Ramadan observance can move with moon-sighting.
  dates={2024:{'Pongal':'2024-01-15','Tamil New Year':'2024-04-14','Ramadan End':'2024-04-11','Diwali':'2024-10-31','Navratri Start':'2024-10-03'},2025:{'Pongal':'2025-01-14','Tamil New Year':'2025-04-14','Ramadan End':'2025-03-31','Diwali':'2025-10-20','Navratri Start':'2025-09-22'},2026:{'Pongal':'2026-01-15','Tamil New Year':'2026-04-14','Ramadan End':'2026-03-20','Diwali':'2026-11-08','Navratri Start':'2026-10-11'}}[year]
  dates.update({'Christmas':f'{year}-12-25','New Year':f'{year}-01-01'})
  for name,ds in dates.items(): rows.append(dict(holiday=name,ds=pd.Timestamp(ds),lower_window=-3,upper_window=3))
 return pd.DataFrame(rows)
def main():
 d=pd.read_parquet(PROC/'tn_features.parquet'); sar=pd.read_csv(REPORT/'sarima_summary.csv',index_col=0); rows=[]; store={}
 for c,g in d.groupby('commodity'):
  g=g.sort_values('arrival_date').copy(); g['arrival_date']=pd.to_datetime(g.arrival_date)
  s=g.set_index('arrival_date').modal_price.resample('D').mean().interpolate().ffill().bfill().clip(1)
  x=pd.DataFrame({'ds':s.index,'y':s.values}); x['sw_monsoon']=x.ds.dt.month.between(6,9).astype(int); x['ne_monsoon']=x.ds.dt.month.between(10,12).astype(int)
  tr,te=x.iloc[:-90],x.iloc[-90:]
  m=Prophet(holidays=holiday_frame(),yearly_seasonality=True,weekly_seasonality=True,daily_seasonality=False,seasonality_mode='multiplicative',changepoint_prior_scale=.05,seasonality_prior_scale=10,holidays_prior_scale=10,interval_width=.95)
  m.add_regressor('sw_monsoon',standardize=False); m.add_regressor('ne_monsoon',standardize=False); m.fit(tr)
  pred=m.predict(te.drop(columns='y')); y=te.y.values; p=pred.yhat.values; rmse=np.sqrt(mean_squared_error(y,p)); mae=mean_absolute_error(y,p); mape=np.mean(np.abs((y-p)/np.maximum(y,1e-8)))*100
  naive=np.mean(np.abs((y-tr.y.iloc[-1])/np.maximum(y,1e-8)))*100; sr=sar[sar.index.astype(str)==c]; sar_mape=float(sr.iloc[0].mape) if len(sr) and 'mape' in sr else np.nan
  rows.append(dict(commodity=c,rmse=rmse,mae=mae,mape=mape,naive_mape=naive,sarima_mape=sar_mape,winner=min([('Prophet',mape),('Naive',naive),('SARIMA',sar_mape) if np.isfinite(sar_mape) else ('SARIMA',np.inf)],key=lambda z:z[1])[0]))
  fig,ax=plt.subplots(2,1,figsize=(11,7)); ax[0].plot(te.ds,y,label='Actual'); ax[0].plot(te.ds,p,label='Forecast'); ax[0].fill_between(te.ds,pred.yhat_lower,pred.yhat_upper,alpha=.2); ax[0].legend(); ax[1].plot(pred.ds,pred.trend); ax[1].set_title('Trend'); fig.tight_layout(); fig.savefig(FIG/f'prophet_{c.lower()}.png'); plt.close(fig); store[c]={'model':m,'forecast':pred,'test':te}
 pd.DataFrame(rows).to_csv(REPORT/'prophet_summary.csv',index=False); pd.DataFrame(rows).set_index('commodity')[['sarima_mape','mape','naive_mape']].plot.bar(); plt.tight_layout(); plt.savefig(FIG/'prophet_comparison.png')
 with open(MODELS/'prophet_results.pkl','wb') as f: pickle.dump(store,f)
if __name__=='__main__': main()
