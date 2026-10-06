import numpy as np,pandas as pd,matplotlib.pyplot as plt,seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from agrisight_common import PROC,REPORT,FIG
def main():
 d=pd.read_parquet(PROC/'tn_vegetables_daily.parquet'); d.arrival_date=pd.to_datetime(d.arrival_date)
 lines=[f"Rows: {len(d)}\nDate range: {d.arrival_date.min()} to {d.arrival_date.max()}\nCommodities: {d.commodity.nunique()}",f"Nulls:\n{d.isna().sum()}\nCounts:\n{d.groupby('commodity').size()}"]
 fig,ax=plt.subplots(figsize=(10,5)); sns.boxplot(data=d,y='commodity',x='modal_price',showfliers=False,ax=ax); fig.tight_layout(); fig.savefig(FIG/'eda_price_boxplot.png'); plt.close(fig)
 trends=d[(d.arrival_date.dt.year>=2020)].assign(month=lambda x:x.arrival_date.dt.to_period('M').dt.to_timestamp()).groupby(['commodity','month']).modal_price.median().reset_index()
 fig,axes=plt.subplots(4,2,figsize=(15,13))
 for ax,(c,g) in zip(axes.flat,trends.groupby('commodity')): ax.plot(g.month,g.modal_price); ax.set_title(c); ax.tick_params(axis='x',rotation=45)
 fig.tight_layout(); fig.savefig(FIG/'eda_monthly_trends_2020_2026.png'); plt.close(fig)
 tomato=d[d.commodity.eq('Tomato')].groupby('arrival_date').modal_price.median().asfreq('D').interpolate().rolling(7,min_periods=1).mean()
 if len(tomato)>=730:
  dec=seasonal_decompose(tomato,model='multiplicative',period=365,extrapolate_trend='freq'); dec.plot(); plt.tight_layout(); plt.savefig(FIG/'eda_tomato_decomposition.png'); plt.close()
  lines.append('Tomato multiplicative seasonal decomposition (365d) completed.')
 hm=d[d.arrival_date.dt.year.between(2015,2026)].assign(year=lambda x:x.arrival_date.dt.year).pivot_table(index='commodity',columns='year',values='modal_price',aggfunc='mean')
 plt.figure(figsize=(12,5)); sns.heatmap(hm,cmap='YlOrRd',annot=True,fmt='.0f'); plt.tight_layout(); plt.savefig(FIG/'eda_commodity_year_heatmap.png'); plt.close()
 daily=tomato; roll=daily.rolling(30,min_periods=10); z=(daily-roll.mean())/roll.std(); anomalies=z.abs()>2.5
 fig,ax=plt.subplots(2,1,figsize=(13,7),sharex=True); ax[0].plot(daily); ax[0].scatter(daily.index[anomalies],daily[anomalies],c='red'); ax[1].plot(z); ax[1].axhline(2.5,color='red'); ax[1].axhline(-2.5,color='red'); fig.tight_layout(); fig.savefig(FIG/'eda_tomato_spikes.png'); plt.close(fig); lines.append(f'Tomato rolling-z anomalies: {int(anomalies.sum())}.')
 monthly=d.assign(month=d.arrival_date.dt.to_period('M').dt.to_timestamp()).groupby(['month','commodity']).modal_price.median().unstack()
 corr=monthly.corr(); mask=np.triu(np.ones_like(corr,dtype=bool)); plt.figure(figsize=(9,7)); sns.heatmap(corr,mask=mask,annot=True,cmap='coolwarm',center=0); plt.tight_layout(); plt.savefig(FIG/'eda_monthly_correlation.png'); plt.close()
 adfs=[]
 for c,g in d.groupby('commodity'):
  s=g.groupby('arrival_date').modal_price.median().asfreq('D').interpolate().ffill().bfill()
  try: stat,p=adfuller(s); adfs.append(dict(commodity=c,adf=stat,p_value=p,stationary=p<.05))
  except Exception as e: adfs.append(dict(commodity=c,error=str(e)))
 lines.append('ADF tests:\n'+pd.DataFrame(adfs).to_string(index=False))
 crisis=d[d.commodity.eq('Tomato')&d.arrival_date.dt.year.between(2022,2024)].groupby('arrival_date').agg(median=('modal_price','median'),peak=('modal_price','max'),markets=('market','nunique'))
 if not crisis.empty:
  fig,ax=plt.subplots(2,1,figsize=(12,7)); crisis[['median','peak']].plot(ax=ax[0]); crisis.markets.plot(ax=ax[1]); fig.tight_layout(); fig.savefig(FIG/'eda_tomato_crisis.png'); plt.close(fig)
  date=crisis.peak.idxmax(); lines.append(f'Tomato crisis peak: ₹{crisis.loc[date,"peak"]} on {date.date()}.')
 markets=d.market.value_counts().head(15); markets.sort_values().plot.barh(figsize=(9,6)); plt.tight_layout(); plt.savefig(FIG/'eda_top_markets.png'); plt.close()
 prof=d.assign(month=d.arrival_date.dt.month).groupby(['commodity','month']).modal_price.median().reset_index()
 fig,axes=plt.subplots(4,2,figsize=(12,12))
 for ax,(c,g) in zip(axes.flat,prof.groupby('commodity')): ax.plot(g.month,g.modal_price,marker='o'); ax.set_title(c); ax.set_xticks(range(1,13))
 fig.tight_layout(); fig.savefig(FIG/'eda_seasonality_profiles.png'); plt.close(fig)
 REPORT.joinpath('eda_summary.txt').write_text('\n\n'.join(lines),encoding='utf-8')
if __name__=='__main__': main()
