"""Leakage-aware state-level daily price feature construction."""
import pandas as pd,numpy as np
from agrisight_common import PROC,EXT,COMMODITIES,REPORT
def festival_flags(idx):
 m=pd.Series(idx.month,index=idx); d=pd.Series(idx.day,index=idx); w=idx.isocalendar().week.astype(int); dow=pd.Series(idx.dayofweek,index=idx)
 return pd.DataFrame({'pongal':((m==1)&(d.between(13,17))).astype(int),'tamil_new_year':((m==4)&(d.between(13,15))).astype(int),
  'diwali':((m.isin([10,11]))&(w.between(40,46))&(dow.isin([0,1,2,3,4,5,6]))).astype(int),
  'navratri':(m.isin([9,10])&(w.between(38,42))).astype(int)},index=idx)
def main():
 d=pd.read_parquet(PROC/'tn_vegetables_daily.parquet'); d.arrival_date=pd.to_datetime(d.arrival_date); dropped=d[d.modal_price>100000]
 dropped.to_csv(REPORT/'feature_outliers_dropped.csv',index=False); d=d[d.modal_price<=100000]
 daily=d.groupby(['arrival_date','commodity']).agg(modal_price=('modal_price','median'),min_price=('min_price','median'),max_price=('max_price','median'),market_count=('market','nunique')).reset_index()
 built=[]
 for c,g in daily.groupby('commodity'):
  g=g.sort_values('arrival_date').set_index('arrival_date').asfreq('D'); p=g.modal_price.ffill(limit=3); g['modal_price']=p
  for n in (7,14,21,30): g[f'lag_{n}']=p.shift(n)
  for n in (7,14,30):
   g[f'rolling_mean_{n}']=p.shift(1).rolling(n).mean(); g[f'rolling_std_{n}']=p.shift(1).rolling(n).std()
  for n in (7,14): g[f'rolling_min_{n}']=p.shift(1).rolling(n).min(); g[f'rolling_max_{n}']=p.shift(1).rolling(n).max()
  for n in (7,14,30): g[f'ema_{n}']=p.shift(1).ewm(span=n,adjust=False).mean()
  g['momentum_7']=p.pct_change(7).shift(1); g['momentum_14']=p.pct_change(14).shift(1); g['momentum_30']=p.pct_change(30).shift(1); g['price_acceleration']=g.momentum_7-g.momentum_14
  roll=p.shift(1).rolling(365,min_periods=30); g['position_52w']=(p-roll.min())/(roll.max()-roll.min()).replace(0,np.nan)
  g['price_range']=g.max_price-g.min_price; idx=g.index
  for k,v in {'month':idx.month,'week_of_year':idx.isocalendar().week.astype(int),'quarter':idx.quarter,'day_of_week':idx.dayofweek,'year':idx.year,'days_since_start':(idx-idx.min()).days}.items(): g[k]=v
  g['sw_monsoon']=idx.month.to_series(index=idx).between(6,9).astype(int); g['ne_monsoon']=idx.month.to_series(index=idx).between(10,12).astype(int)
  g=pd.concat([g,festival_flags(idx)],axis=1); g['commodity']=c; built.append(g.reset_index(names='arrival_date'))
 f=pd.concat(built,ignore_index=True); cross=f.pivot(index='arrival_date',columns='commodity',values='modal_price').shift(1)
 for c in COMMODITIES: f['cross_'+c+'_lag1']=f.arrival_date.map(cross[c]) if c in cross else np.nan
 weather=EXT/'weather_chennai.parquet'
 if weather.exists():
  w=pd.read_parquet(weather); w['arrival_date']=pd.to_datetime(w.get('arrival_date',w.get('date'))); w=w.sort_values('arrival_date')
  if 'precipitation' not in w and 'rain' in w: w=w.rename(columns={'rain':'precipitation'})
  if 'precipitation' in w:
   w['rain_7d_sum']=w.precipitation.rolling(7,min_periods=1).sum(); w['rain_30d_sum']=w.precipitation.rolling(30,min_periods=1).sum()
  if 'temp_max' in w: w['heat_wave']=(w.temp_max>=38).astype(int)
  if 'temp_avg' in w: w['cold_day']=(w.temp_avg<=20).astype(int)
  f=f.merge(w,on='arrival_date',how='left')
 f=f.dropna(subset=['modal_price','lag_30']).query('year>=2024')
 f.to_parquet(PROC/'tn_features.parquet',index=False); f.to_csv(PROC/'tn_features.csv',index=False)
 REPORT.joinpath('feature_summary.txt').write_text(f"rows={len(f)} cols={len(f.columns)}\nnulls:\n{f.isna().sum().to_string()}",encoding='utf-8')
if __name__=='__main__': main()
