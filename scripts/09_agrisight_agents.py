"""Deterministic four-agent procurement advice pipeline (no external LLM calls)."""
import json,pickle
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from agrisight_common import PROC,REPORT,FIG,MODELS
class Agent:
 def __init__(self,name,role,goal): self.name=name; self.role=role; self.goal=goal; self.memory=[]; self.output=None
 def run(self,context): raise NotImplementedError
class DataAnalystAgent(Agent):
 def __init__(self): super().__init__('Data Analyst','price and volatility analyst','identify anomalies and recent trends')
 def run(self,ctx):
  d=ctx['features']; result={}
  for c,g in d.groupby('commodity'):
   s=g.sort_values('arrival_date').modal_price; m30=s.tail(30); m7=s.tail(7); std=float(m30.std()); mean=float(m30.mean()); change=float((m7.mean()/s.tail(14).head(7).mean()-1)*100) if len(s)>=14 and s.tail(14).head(7).mean() else 0
   z=float((s.iloc[-1]-m30.mean())/(std or 1)); result[c]={'mean_30d':mean,'std_30d':std,'cv_30d':std/(mean or 1),'change_7d_pct':change,'z_30d':z,'anomaly':abs(z)>2,'trend':'up' if change>5 else 'down' if change < -5 else 'stable'}
  self.output=result; return result
class PriceForecasterAgent(Agent):
 def __init__(self): super().__init__('Price Forecaster','XGBoost forecast agent','forecast 7 and 14 days')
 def run(self,ctx):
  results={}; ml=ctx['ml']
  for c,g in ctx['features'].groupby('commodity'):
   g=g.sort_values('arrival_date'); r=g.iloc[-1]; features=ml[c]['features']; model=ml[c]['model']; today=pd.Timestamp(r.arrival_date); preds={}
   for horizon in (7,14):
    future=today+pd.Timedelta(days=horizon); row=r[features].copy()
    for k,v in {'month':future.month,'week_of_year':int(future.isocalendar().week),'quarter':future.quarter,'day_of_week':future.dayofweek,'year':future.year,'days_since_start':(future-today).days+int(r.get('days_since_start',0))}.items():
     if k in row: row[k]=v
    row['sw_monsoon']=int(future.month in (6,7,8,9)); row['ne_monsoon']=int(future.month in (10,11,12))
    for k,val in {'pongal':int(future.month==1 and 13<=future.day<=17),'tamil_new_year':int(future.month==4 and 13<=future.day<=15),'diwali':int(future.month in (10,11) and int(future.isocalendar().week) in range(40,47)),'navratri':int(future.month in (9,10) and int(future.isocalendar().week) in range(38,43))}.items():
     if k in row: row[k]=val
    preds[horizon]=max(1,float(model.predict(row.to_frame().T)[0]))
   now=float(r.modal_price); pct=(preds[14]/now-1)*100; signal='BUY' if pct < -5 else 'SELL' if pct>5 else 'HOLD'
   results[c]={'current_price':now,'forecast_7d':preds[7],'forecast_14d':preds[14],'change_14d_pct':pct,'signal':signal}
  self.output=results; return results
class MarketIntelligenceAgent(Agent):
 def __init__(self): super().__init__('Market Intelligence','risk and SHAP analyst','explain commodity risks')
 def run(self,ctx):
  drivers=ctx['drivers']; result={}
  for c,stats in ctx['analysis'].items():
   f=ctx['forecast'][c]; cv=stats['cv_30d']; z=abs(stats['z_30d']); move=abs(f['change_14d_pct'])
   score=min(100,cv*120+z*12+move*1.2); risk='HIGH' if score>=55 else 'MEDIUM' if score>=28 else 'LOW'
   driver=drivers.get(c,'market_price'); trigger='demand surge' if stats['change_7d_pct']>5 else 'possible supply shock' if z>2 else 'routine volatility'
   result[c]={'risk_score':score,'risk':risk,'driver':driver,'trigger':f'{trigger}; leading driver: {driver}'}
  self.output=result; return result
class ProcurementAdvisorAgent(Agent):
 def __init__(self): super().__init__('Procurement Advisor','procurement planner','recommend timing and quantities')
 def run(self,ctx):
  actions=[]
  for c,a in ctx['analysis'].items():
   f=ctx['forecast'][c]; risk=ctx['intelligence'][c]['risk']; change=f['change_14d_pct']
   action='PROCURE NOW' if change>5 and risk!='HIGH' else 'DELAY PROCUREMENT' if change < -5 else 'PARTIAL PROCUREMENT' if risk=='HIGH' else 'HEDGE' if abs(change)>3 else 'HOLD'
   timing='within 1-2 days' if action=='PROCURE NOW' else 'reassess in 7 days' if action=='DELAY PROCUREMENT' else 'split purchase across 7-14 days'
   qty='70-100%' if action=='PROCURE NOW' else '25-50%' if action in ('PARTIAL PROCUREMENT','HEDGE') else 'defer discretionary volume' if action=='DELAY PROCUREMENT' else 'normal replenishment'
   saving=max(0,abs(change)/100*f['current_price']); actions.append({'commodity':c,'action':action,'timing':timing,'quantity_guidance':qty,'estimated_savings_per_quintal':saving,'risk':ctx['intelligence'][c]['risk'],'forecast_14d_change_pct':change})
  self.output=actions; return actions
def main():
 d=pd.read_parquet(PROC/'tn_features.parquet'); d.arrival_date=pd.to_datetime(d.arrival_date); ml=pickle.load(open(MODELS/'ml_results.pkl','rb'))
 drivers={}
 p=REPORT/'shap_top_drivers.csv'
 if p.exists():
  for _,r in pd.read_csv(p).iterrows(): drivers[r.commodity]=str(r.top1)
 ctx={'features':d,'ml':ml,'drivers':drivers}
 a,b,c,e=DataAnalystAgent(),PriceForecasterAgent(),MarketIntelligenceAgent(),ProcurementAdvisorAgent()
 ctx['analysis']=a.run(ctx); ctx['forecast']=b.run(ctx); ctx['intelligence']=c.run(ctx); ctx['actions']=e.run(ctx)
 for item in ctx['actions']: item.update(ctx['forecast'][item['commodity']]); item.update(ctx['intelligence'][item['commodity']])
 summary=[]
 for file in ('ml_summary.csv','sarima_summary.csv'):
  path=REPORT/file
  if path.exists():
   df=pd.read_csv(path); col='mape'
   if col in df:
    avg=df.loc[df['commodity'].astype(str).eq('AVERAGE'),col] if 'commodity' in df else pd.Series(dtype=float)
    value=float(avg.iloc[0]) if len(avg) else float(df[col].mean())
    summary.append(f'{file} mean MAPE {value:.2f}%')
 report={'agents':[x.name for x in (a,b,c,e)],'analysis':ctx['analysis'],'forecasts':ctx['forecast'],'intelligence':ctx['intelligence'],'recommendations':ctx['actions'],'priority_actions':sorted(ctx['actions'],key=lambda x:(x['action']!='PROCURE NOW',-abs(x['forecast_14d_change_pct']))),'executive_summary':{'high_risk':[k for k,v in ctx['intelligence'].items() if v['risk']=='HIGH'],'model_basis':'; '.join(summary) or 'Model summary files not yet available'}}
 (REPORT/'agrisight_pipeline_report.json').write_text(json.dumps(report,indent=2,default=float),encoding='utf-8'); (REPORT/'agrisight_pipeline_report.txt').write_text(pd.DataFrame(ctx['actions']).to_string(index=False),encoding='utf-8')
 names=list(ctx['forecast']); x=np.arange(len(names)); fig,ax=plt.subplots(figsize=(13,6)); ax.bar(x-.25,[ctx['forecast'][n]['current_price'] for n in names],.25,label='Current'); ax.bar(x,[ctx['forecast'][n]['forecast_7d'] for n in names],.25,label='7 days'); ax.bar(x+.25,[ctx['forecast'][n]['forecast_14d'] for n in names],.25,label='14 days'); ax.set_xticks(x,names); ax.legend(); fig.tight_layout(); fig.savefig(FIG/'agent_forecasts.png'); plt.close(fig)
 fig,ax=plt.subplots(figsize=(9,6))
 for n in names: ax.scatter(ctx['analysis'][n]['cv_30d'],abs(ctx['analysis'][n]['z_30d']),label=n)
 ax.set_xlabel('30d CV'); ax.set_ylabel('|30d z-score|'); ax.legend(); fig.tight_layout(); fig.savefig(FIG/'agent_risk_matrix.png'); plt.close(fig)
 print(pd.DataFrame(ctx['actions']).to_string(index=False))
if __name__=='__main__': main()
