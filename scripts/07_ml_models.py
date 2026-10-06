import pickle,numpy as np,pandas as pd,matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error,mean_absolute_error
from xgboost import XGBRegressor
from agrisight_common import PROC,REPORT,FIG,MODELS,COMMODITIES
FEATURES=['lag_7','lag_14','lag_21','lag_30','rolling_mean_7','rolling_mean_14','rolling_std_7','rolling_std_14','rolling_min_7','rolling_max_7','ema_7','ema_14','momentum_7','momentum_14','momentum_30','price_acceleration','position_52w','month','week_of_year','day_of_week','sw_monsoon','ne_monsoon','pongal','tamil_new_year','diwali','navratri','market_count','rain_7d_sum','rain_30d_sum','temp_max']
FEATURES += ['cross_'+c+'_lag1' for c in COMMODITIES]
def metrics(y,p):
 y=np.asarray(y); p=np.asarray(p); return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'mape':float(np.mean(np.abs((y-p)/np.maximum(abs(y),1e-8)))*100)}
def rf(): return RandomForestRegressor(n_estimators=300,max_depth=10,min_samples_leaf=5,max_features=.7,n_jobs=-1,random_state=42)
def xgb(): return XGBRegressor(n_estimators=400,max_depth=5,learning_rate=.05,subsample=.8,colsample_bytree=.8,min_child_weight=3,reg_alpha=.1,reg_lambda=1,objective='reg:squarederror',random_state=42,n_jobs=-1)
def walk(model_factory,tr,te,features):
 preds=[]; step=30
 for start in range(0,len(te),step):
  model=model_factory(); fit=pd.concat([tr,te.iloc[:start]])
  model.fit(fit[features],fit.modal_price)
  preds.extend(model.predict(te.iloc[start:start+step][features]))
 return np.asarray(preds)
def main():
 d=pd.read_parquet(PROC/'tn_features.parquet')
 missing=sorted(set(FEATURES)-set(d.columns))
 if missing: raise SystemExit('Missing model features: '+', '.join(missing)+'; check the weather input schema and rerun script 04.')
 sar=pd.read_csv(REPORT/'sarima_summary.csv'); pro=pd.read_csv(REPORT/'prophet_summary.csv')
 results={}; rows=[]; importances=[]
 sar_map=pd.read_csv(REPORT/'sarima_summary.csv').set_index('commodity').mape.to_dict() if (REPORT/'sarima_summary.csv').exists() else {}
 pro_map=pd.read_csv(REPORT/'prophet_summary.csv').set_index('commodity').mape.to_dict() if (REPORT/'prophet_summary.csv').exists() else {}
 for c,g in d.groupby('commodity'):
  g=g.sort_values('arrival_date').replace([np.inf,-np.inf],np.nan).dropna(subset=FEATURES+['modal_price'])
  tr,te=g.iloc[:-90],g.iloc[-90:]; predictions={}
  for name,factory in [('RF',rf),('XGBoost',xgb)]:
   p=walk(factory,tr,te,FEATURES); predictions[name]=p; met=metrics(te.modal_price,p)
   models= factory().fit(tr[FEATURES],tr.modal_price)
   imp=getattr(models,'feature_importances_',np.zeros(len(FEATURES)))
   if name=='XGBoost': importances.extend(dict(commodity=c,feature=f,importance=float(v)) for f,v in zip(FEATURES,imp))
   rows.append(dict(commodity=c,model=name,**met,sarima_mape=sar_map.get(c,np.nan),prophet_mape=pro_map.get(c,np.nan),delta_vs_sarima=met['mape']-sar_map.get(c,np.nan),predictions=p.tolist()))
  best='RF' if rows[-2]['mape']<=rows[-1]['mape'] else 'XGBoost'
  rows[-2]['best_model']=best; rows[-1]['best_model']=best
  # Refit deployable models on all eligible observations.
  final_rf=rf().fit(g[FEATURES],g.modal_price); final_xgb=xgb().fit(g[FEATURES],g.modal_price)
  results[c]={'models':{'RF':final_rf,'XGBoost':final_xgb},'model':final_xgb,'features':FEATURES,'latest':g.iloc[-1][FEATURES].to_dict(),
   'test_dates':te.arrival_date.astype(str).tolist(),'actual':te.modal_price.tolist(),'predictions':predictions,'best_model':best}
  fig,ax=plt.subplots(2,1,figsize=(12,8)); ax[0].plot(pd.to_datetime(te.arrival_date),te.modal_price,label='Actual')
  for name,p in predictions.items(): ax[0].plot(pd.to_datetime(te.arrival_date),p,label=name)
  ax[0].legend(); top=pd.Series(final_xgb.feature_importances_,index=FEATURES).nlargest(15).sort_values(); top.plot.barh(ax=ax[1]); fig.tight_layout(); fig.savefig(FIG/f'ml_{c.lower()}.png'); plt.close(fig)
 summary=pd.DataFrame(rows); summary.drop(columns=['predictions']).to_csv(REPORT/'ml_summary.csv',index=False)
 for model in ('RF','XGBoost'):
  subset=summary[summary.model==model].set_index('commodity').mape.rename(model); summary.loc[summary.model==model,model+'_mape']=summary.loc[summary.model==model,'mape']
 wide=summary.pivot(index='commodity',columns='model',values='mape')
 for f in ('sarima_summary.csv','prophet_summary.csv'):
  p=REPORT/f
  if p.exists():
   ext=pd.read_csv(p); ext=ext[ext.commodity.astype(str)!='AVERAGE'].set_index('commodity')
   wide[f.replace('_summary.csv','')]=ext.mape
 wide.plot.bar(figsize=(13,6)); plt.ylabel('MAPE (%)'); plt.tight_layout(); plt.savefig(FIG/'model_comparison.png'); plt.close()
 imp=pd.DataFrame(importances).groupby('feature').importance.mean().nlargest(20).sort_values(); imp.plot.barh(); plt.tight_layout(); plt.savefig(FIG/'ml_global_feature_importance.png')
 summary.drop(columns=['predictions']).to_csv(REPORT/'ml_summary.csv',index=False)
 with open(MODELS/'ml_results.pkl','wb') as f: pickle.dump(results,f)
if __name__=='__main__': main()
