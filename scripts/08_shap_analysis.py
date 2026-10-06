import pickle,numpy as np,pandas as pd,matplotlib.pyplot as plt
from xgboost import XGBRegressor
import shap
from agrisight_common import PROC,REPORT,FIG,MODELS
def category(name):
 if name.startswith('cross_'): return 'Cross-commodity'
 if name.startswith(('lag_','rolling_','ema_','momentum_','price_','position_')): return 'Price history'
 if name in ('pongal','tamil_new_year','diwali','navratri','sw_monsoon','ne_monsoon'): return 'Seasonal/festival'
 return 'Calendar/other'
def main():
 d=pd.read_parquet(PROC/'tn_features.parquet'); saved=pickle.load(open(MODELS/'ml_results.pkl','rb')); global_values=[]; drivers=[]
 for c,v in saved.items():
  x=d[d.commodity.eq(c)].replace([np.inf,-np.inf],np.nan).dropna(subset=v['features'])
  model=XGBRegressor(n_estimators=400,max_depth=5,learning_rate=.05,subsample=.8,colsample_bytree=.8,min_child_weight=3,reg_alpha=.1,reg_lambda=1,base_score=.5,objective='reg:squarederror',random_state=42)
  model.fit(x[v['features']],x.modal_price); explainer=shap.TreeExplainer(model); values=explainer(x[v['features']])
  imp=pd.Series(np.abs(values.values).mean(axis=0),index=v['features']).sort_values(ascending=False); global_values.append(imp.rename(c))
  top=imp.head(15); colors=[{'Price history':'#2878B5','Cross-commodity':'#F08030','Seasonal/festival':'#48A868','Calendar/other':'#999999'}[category(k)] for k in top.index]
  fig,ax=plt.subplots(figsize=(9,6)); ax.barh(top.index[::-1],top.values[::-1],color=colors[::-1]); ax.set_title(f'{c}: mean |SHAP|'); fig.tight_layout(); fig.savefig(FIG/f'shap_bar_{c.lower()}.png'); plt.close(fig)
  drivers.append(dict(commodity=c,top1=top.index[0],top1_magnitude=top.iloc[0],top2=top.index[1],top2_magnitude=top.iloc[1],top3=top.index[2],top3_magnitude=top.iloc[2]))
  if c=='Tomato':
   latest=x[v['features']].iloc[[-1]]; lv=explainer(latest)
   shap.plots.waterfall(lv[0],show=False); plt.tight_layout(); plt.savefig(FIG/'shap_tomato_waterfall.png',bbox_inches='tight'); plt.close()
   for f in top.index[:3]:
    shap.dependence_plot(f,values.values,x[v['features']],show=False); plt.tight_layout(); plt.savefig(FIG/f'shap_tomato_dependence_{f}.png'); plt.close()
 merged=pd.concat(global_values,axis=1).fillna(0); mean=merged.mean(axis=1).nlargest(15).sort_values()
 mean.plot.barh(figsize=(9,6)); plt.tight_layout(); plt.savefig(FIG/'shap_global_importance.png')
 pd.DataFrame(drivers).to_csv(REPORT/'shap_top_drivers.csv',index=False)
if __name__=='__main__': main()
