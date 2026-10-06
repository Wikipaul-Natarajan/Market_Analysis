"""Fetch year files from the Kaggle dataset and filter to Tamil Nadu vegetables.

Requires Kaggle CLI credentials only when source files are not already local. Only downloads selected year files, not the 7+ GB
full dataset. The currently linked Kaggle input listing includes 2024 and 2025;
2026 is attempted optionally and may not yet be published.
"""
import os,subprocess,shutil
from pathlib import Path
import pandas as pd
from agrisight_common import RAW,COMMODITIES
DATASET=os.getenv('KAGGLE_DATASET','khandelwalmanas/daily-commodity-prices-india')
YEARS=[int(x) for x in os.getenv('KAGGLE_YEARS','2024,2025,2026').split(',')]
ALIASES={
 'state':('state','state_name'),'district':('district','district_name'),'market':('market','market_name','mandi'),
 'commodity':('commodity','commodity_name','crop'),'variety':('variety',),'grade':('grade',),
 'arrival_date':('arrival_date','date'),'min_price':('min_price','minimum_price'),
 'max_price':('max_price','maximum_price'),'modal_price':('modal_price','modalprice')
}
NAMES={'tomato':'Tomato','onion':'Onion','potato':'Potato','cabbage':'Cabbage','carrot':'Carrot','beans':'Beans','french beans':'Beans','indian beans(seam)':'Beans','seam':'Beans','brinjal':'Brinjal','eggplant':'Brinjal','drumstick':'Drumstick'}
def normalize(df):
 df=df.copy(); df.columns=[str(c).strip().lower().replace(' ','_').replace('-','_') for c in df.columns]
 rename={}
 for target,aliases in ALIASES.items():
  col=next((c for c in df.columns if c in aliases or any(c.endswith('_'+a) for a in aliases)),None)
  if col: rename[col]=target
 df=df.rename(columns=rename)
 for col in ALIASES:
  if col not in df: df[col]=pd.NA
 return df[list(ALIASES)]
def download(year,folder):

 candidates=[f'csv/{year}.csv',f'{year}.csv']
 for rel in candidates:
  cmd=['kaggle','datasets','download',DATASET,'-f',rel,'-p',str(folder),'--unzip']
  run=subprocess.run(cmd,capture_output=True,text=True)
  if run.returncode==0:
   matches=list(folder.rglob(f'{year}.csv'))
   if matches: return matches[0]
  print(f'Kaggle file unavailable ({rel}): {(run.stderr or run.stdout).strip()[-500:]}')
 return None
def main():

 folder=RAW/'kaggle_years'; folder.mkdir(parents=True,exist_ok=True); out=RAW/'agmarknet_kaggle_tn_vegetables_2024_plus.csv'
 if out.exists(): out.unlink()
 found=[]; wrote=False
 for year in YEARS:
  file=next(iter(folder.rglob(f'{year}.csv')),None)
  if file is None:
   try: file=download(year,folder)
   except SystemExit:
    if year in (2024,2025): raise
    file=None
  if file is None:
   if year in (2024,2025): raise SystemExit(f'Could not fetch required Kaggle file for {year}. Configure Kaggle API credentials and verify that year file is available.')
   continue
  found.append(year)
  for chunk in pd.read_csv(file,chunksize=200000,low_memory=False):
   d=normalize(chunk)
   d['arrival_date']=pd.to_datetime(d.arrival_date,errors='coerce',dayfirst=True)
   d['commodity']=d.commodity.astype(str).str.strip().str.lower().map(NAMES)
   state=d.state.astype(str).str.strip().str.lower()
   keep=state.isin(['tamil nadu','tamilnadu','tn','33']) & d.commodity.isin(COMMODITIES) & d.arrival_date.ge(pd.Timestamp('2024-01-01'))
   d=d.loc[keep].copy()
   for col in ('min_price','max_price','modal_price'): d[col]=pd.to_numeric(d[col].astype(str).str.replace(',','',regex=False),errors='coerce')
   d=d.dropna(subset=['arrival_date','market','commodity','modal_price'])
   if len(d):
    d.to_csv(out,mode='a',index=False,header=not wrote); wrote=True
 if not wrote: raise SystemExit('No matching Tamil Nadu vegetable rows were found. Inspect Kaggle column names and filters.')
 result=pd.read_csv(out); result=result.drop_duplicates(['arrival_date','market','commodity']).sort_values(['arrival_date','commodity','market'])
 result.to_csv(out,index=False); result.to_parquet(out.with_suffix('.parquet'),index=False)
 print(f'Years fetched: {found}; rows after filters: {len(result):,}; date range: {result.arrival_date.min()} to {result.arrival_date.max()}')
 print(f'Filtered files saved: {out} and {out.with_suffix(".parquet")}')
if __name__=='__main__': main()
