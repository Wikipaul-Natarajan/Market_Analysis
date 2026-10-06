import itertools,pickle
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error,mean_absolute_error
from agrisight_common import PROC,REPORT,FIG,MODELS
def scores(y,p):
 y=np.asarray(y); p=np.asarray(p); return float(np.sqrt(mean_squared_error(y,p))),float(mean_absolute_error(y,p)),float(np.mean(np.abs((y-p)/np.maximum(np.abs(y),1e-8)))*100)
def main():
 d=pd.read_parquet(PROC/'tn_features.parquet'); summary=[]; store={}
 for commodity,g in d.groupby('commodity'):
  s=g.set_index(pd.to_datetime(g.arrival_date)).modal_price.resample('D').mean().interpolate().ffill().bfill().clip(1)
  train,test=s.iloc[:-90],s.iloc[-90:]
  try: adf_p=adfuller(train)[1]; order_d=0 if adf_p<.05 else 1
  except Exception: order_d=1
  best=None
  for p,q,P,Q in itertools.product((1,2),(0,1),(0,1),(0,1)):
   try:
    fit=SARIMAX(train,order=(p,order_d,q),seasonal_order=(P,1,Q,7),enforce_stationarity=False,enforce_invertibility=False).fit(disp=False,maxiter=100)
    if best is None or fit.aic<best.aic: best=fit; best_order=((p,order_d,q),(P,1,Q,7))
   except Exception: continue
  if best is None: raise RuntimeError(f'All SARIMA fits failed for {commodity}')
  pred=best.get_forecast(90); forecast=pred.predicted_mean.clip(lower=1); lo,hi=pred.conf_int().iloc[:,0],pred.conf_int().iloc[:,1]
  wf=[]
  for start in range(0,90,7):
   fit=SARIMAX(s.iloc[:len(train)+start],order=best_order[0],seasonal_order=best_order[1],enforce_stationarity=False,enforce_invertibility=False).fit(disp=False,maxiter=100)
   wf.extend(fit.forecast(min(7,90-start)).tolist())
  rmse,mae,mape=scores(test,forecast); wr,_,wm=scores(test,wf); _,_,nm=scores(test,np.repeat(train.iloc[-1],90))
  summary.append(dict(commodity=commodity,order=str(best_order),aic=best.aic,rmse=rmse,mae=mae,mape=mape,naive_mape=nm,walk_forward_rmse=wr,walk_forward_mape=wm))
  fig,ax=plt.subplots(2,1,figsize=(12,8)); ax[0].plot(train.tail(180),label='Train'); ax[0].plot(test,label='Actual'); ax[0].plot(forecast,label='Forecast'); ax[0].fill_between(test.index,lo,hi,alpha=.2); ax[0].legend(); ax[1].plot(test.index,test.values-forecast.values); ax[1].axhline(0,color='black'); fig.tight_layout(); fig.savefig(FIG/f'sarima_{commodity.lower()}.png'); plt.close(fig)
  store[commodity]={'model':best,'forecast':forecast,'lower':lo,'upper':hi,'test':test,'walk_forward':pd.Series(wf,index=test.index)}
 x=pd.DataFrame(summary); x.loc['AVERAGE']=x.select_dtypes('number').mean(); x.loc['AVERAGE','commodity']='AVERAGE'; x.to_csv(REPORT/'sarima_summary.csv',index=False)
 x.drop(index='AVERAGE',errors='ignore').plot.bar(x='commodity',y=['rmse'],legend=False); plt.tight_layout(); plt.savefig(FIG/'sarima_comparison.png'); plt.close()
 with open(MODELS/'sarima_results.pkl','wb') as f: pickle.dump(store,f)
if __name__=='__main__': main()
