"""Download daily Chennai weather from Open-Meteo Historical Weather API."""
import os,requests,pandas as pd
from agrisight_common import EXT
URL='https://archive-api.open-meteo.com/v1/archive'
def main():
 params={'latitude':float(os.getenv('CHENNAI_LATITUDE','13.0827')),'longitude':float(os.getenv('CHENNAI_LONGITUDE','80.2707')),
  'start_date':os.getenv('WEATHER_START_DATE','2024-01-01'),'end_date':os.getenv('WEATHER_END_DATE','2026-09-30'),
  'daily':'precipitation_sum,rain_sum,temperature_2m_max,temperature_2m_mean,temperature_2m_min',
  'timezone':'Asia/Kolkata'}
 r=requests.get(URL,params=params,timeout=90); r.raise_for_status(); payload=r.json()
 daily=payload.get('daily')
 if not daily or not daily.get('time'): raise RuntimeError(f'Open-Meteo returned no daily values: {payload}')
 d=pd.DataFrame({'arrival_date':pd.to_datetime(daily['time']),'date':pd.to_datetime(daily['time']),
  'precipitation':daily['precipitation_sum'],'rain':daily['rain_sum'],'temp_max':daily['temperature_2m_max'],
  'temp_avg':daily['temperature_2m_mean'],'temp_min':daily['temperature_2m_min']})
 d['latitude']=payload.get('latitude'); d['longitude']=payload.get('longitude'); d['timezone']=payload.get('timezone')
 out=EXT/'weather_chennai.parquet'; d.to_parquet(out,index=False); d.to_csv(EXT/'weather_chennai.csv',index=False)
 print(f'Saved {len(d)} daily observations, {d.arrival_date.min().date()} to {d.arrival_date.max().date()} at {params["latitude"]},{params["longitude"]}: {out}')
if __name__=='__main__': main()
