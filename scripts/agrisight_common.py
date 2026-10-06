from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'data/raw'; PROC=ROOT/'data/processed'; EXT=ROOT/'data/external'
OUT=ROOT/'outputs'; REPORT=OUT/'reports'; FIG=OUT/'figures'; MODELS=OUT/'models'
COMMODITIES=['Tomato','Onion','Potato','Cabbage','Carrot','Beans','Brinjal','Drumstick']
for p in (RAW,PROC,EXT,REPORT,FIG,MODELS): p.mkdir(parents=True,exist_ok=True)
def read_data(path=PROC/'tn_vegetables_daily.parquet'):
    return pd.read_parquet(path)
def save(df,path):
    path.parent.mkdir(parents=True,exist_ok=True); df.to_parquet(path,index=False); df.to_csv(path.with_suffix('.csv'),index=False)
