"""Launch with: streamlit run 10_dashboard.py"""
import json,pickle
import pandas as pd,streamlit as st
from agrisight_common import PROC,REPORT,MODELS,FIG
st.set_page_config(page_title='AgriSight',page_icon='🌱',layout='wide')
@st.cache_data
def parquet(path): return pd.read_parquet(path)
@st.cache_data
def csv(path): return pd.read_csv(path)
@st.cache_resource
def ml_models(path):
 with open(path,'rb') as f: return pickle.load(f)
def warn(path,step): st.warning(f'Required artifact is missing: {path.name}. Run script {step} first.')
def load_report(path):
 return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
page=st.sidebar.radio('AgriSight pages',['Overview','Market Analysis','Price Forecast','Agent Pipeline','Model Comparison','SHAP Explainability'])
st.title('AgriSight | Tamil Nadu Vegetable Prices')
raw=PROC/'tn_vegetables_daily.parquet'; features=PROC/'tn_features.parquet'
if page=='Overview':
 if raw.exists():
  d=parquet(str(raw)); d.arrival_date=pd.to_datetime(d.arrival_date)
  c1,c2,c3=st.columns(3); c1.metric('Observations',f'{len(d):,}'); c2.metric('Commodities',d.commodity.nunique()); c3.metric('Markets',d.market.nunique())
  st.line_chart(d.groupby('arrival_date').modal_price.median())
  st.caption('This Kaggle build is intentionally filtered to price records from 2024 onward; older years are outside the selected input window.')
 else: warn(raw,'02')
elif page=='Market Analysis':
 if raw.exists():
  d=parquet(str(raw)); d.arrival_date=pd.to_datetime(d.arrival_date); tabs=st.tabs(['Price Trends','Seasonality','Market Coverage','Data Quality'])
  with tabs[0]:
   years=sorted(d.arrival_date.dt.year.unique()); year=st.selectbox('Year',years,index=len(years)-1); c=st.selectbox('Commodity',sorted(d.commodity.unique()),key='trend'); g=d[(d.commodity==c)&(d.arrival_date.dt.year==year)].groupby('arrival_date').modal_price.median(); st.line_chart(g)
  with tabs[1]:
   c=st.selectbox('Commodity',sorted(d.commodity.unique()),key='season'); g=d[d.commodity==c].assign(month=lambda x:x.arrival_date.dt.month).groupby('month').modal_price.median(); st.bar_chart(g)
  with tabs[2]:
   st.bar_chart(d.market.value_counts().head(20)); st.line_chart(d.groupby(d.arrival_date.dt.year).size())
  with tabs[3]:
   st.warning('This build filters prices to 2024 onward by design. Missing pre-2024 years reflect the configured input window, not an inferred market reporting gap.')
   st.dataframe(d.isna().sum().rename('null_count'))
 else: warn(raw,'02')
elif page=='Price Forecast':
 if features.exists() and (MODELS/'ml_results.pkl').exists():
  d=parquet(str(features)); models=ml_models(str(MODELS/'ml_results.pkl')); c=st.selectbox('Commodity',sorted(models)); horizon=st.selectbox('Forecast horizon (days)',[7,14,30]); r=d[d.commodity==c].sort_values('arrival_date').iloc[-1]; future=pd.Timestamp(r.arrival_date)+pd.Timedelta(days=horizon); row=r[models[c]['features']].copy().astype(float)
  for k,v in {'month':future.month,'week_of_year':int(future.isocalendar().week),'quarter':future.quarter,'day_of_week':future.dayofweek,'year':future.year}.items():
   if k in row: row[k]=v
  val=float(models[c]['model'].predict(row.to_frame().T.astype(float))[0]); st.metric(f'{c} forecast · {horizon} days',f'₹{val:,.0f}/quintal',f'{(val/r.modal_price-1)*100:+.1f}%'); st.caption('Weather, market count, and cross-commodity features stay at their last known values across this horizon.')
 else:
  warn(features,'04')
  if not (MODELS/'ml_results.pkl').exists(): warn(MODELS/'ml_results.pkl','07')
elif page=='Agent Pipeline':
 rep=load_report(REPORT/'agrisight_pipeline_report.json')
 if rep:
  st.subheader('Executive summary'); st.json(rep.get('executive_summary',{})); st.dataframe(pd.DataFrame(rep.get('recommendations',[])))
  for n in ('agent_forecasts.png','agent_risk_matrix.png'):
   if (FIG/n).exists(): st.image(str(FIG/n))
 else: warn(REPORT/'agrisight_pipeline_report.json','09')
elif page=='Model Comparison':
 p=REPORT/'ml_summary.csv'
 if p.exists(): st.dataframe(csv(str(p)))
 else: warn(p,'07')
 for name in ('sarima_summary.csv','prophet_summary.csv'):
  q=REPORT/name
  if q.exists():
   st.subheader(name.replace('_',' ').replace('.csv','').title())
   st.dataframe(csv(str(q)))
  else: warn(q,'05' if name.startswith('sarima') else '06')
 for n in ('model_comparison.png','sarima_comparison.png','prophet_comparison.png'):
  if (FIG/n).exists(): st.image(str(FIG/n))
else:
 tabs=st.tabs(['Per-Commodity SHAP','Tomato Deep-Dive','Global Insights'])
 with tabs[0]:
  c=st.selectbox('Commodity',['Tomato','Onion','Potato','Cabbage','Carrot','Beans','Brinjal','Drumstick']); p=FIG/f'shap_bar_{c.lower()}.png'; st.image(str(p)) if p.exists() else warn(p,'08')
 with tabs[1]:
  st.info('SHAP values show each feature contribution to the selected model prediction; they describe model behavior, not causal effects.')
  for n in ('shap_tomato_waterfall.png',):
   p=FIG/n; st.image(str(p)) if p.exists() else warn(p,'08')
  for p in FIG.glob('shap_tomato_dependence_*.png'): st.image(str(p))
 with tabs[2]:
  p=FIG/'shap_global_importance.png'; st.image(str(p)) if p.exists() else warn(p,'08')
