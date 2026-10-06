"""Normalize supplied Agmarknet CSVs and optional data.gov.in pages into one dataset."""
import os, glob, re, requests
import pandas as pd
from agrisight_common import RAW, PROC, REPORT, COMMODITIES

API = "https://api.data.gov.in/resource"
ALIASES = {
 "state":("state","state_name"), "district":("district","district_name"),
 "market":("market","market_name","mandi"), "commodity":("commodity","commodity_name","crop"),
 "variety":("variety",), "grade":("grade",), "arrival_date":("arrival_date","arrivals_date","date"),
 "min_price":("min_price","minimum_price"), "max_price":("max_price","maximum_price"),
 "modal_price":("modal_price","modalprice")
}
VARIANTS = {
 "tomato":"Tomato","onion":"Onion","potato":"Potato","cabbage":"Cabbage","carrot":"Carrot",
 "beans":"Beans","french beans":"Beans","indian beans(seam)":"Beans","seam":"Beans",
 "brinjal":"Brinjal","eggplant":"Brinjal","drumstick":"Drumstick"
}
def key(s): return re.sub(r"[^a-z0-9]+","_",str(s).strip().lower()).strip("_")
def normalize(df):
    df=df.copy(); df.columns=[key(c) for c in df.columns]
    ren={}
    for target, names in ALIASES.items():
        for c in df.columns:
            if c in names or any(c.endswith("_"+n) for n in names):
                ren[c]=target; break
    df=df.rename(columns=ren)
    for c in ALIASES:
        if c not in df: df[c]=pd.NA
    return df[list(ALIASES)]
def parse_dates(s):
    s=s.astype("string").str.strip()
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d-%m-%Y","%d-%b-%Y"):
        p=pd.to_datetime(s,format=fmt,errors="coerce")
        if p.notna().sum()>len(s)*.5: return p
    return pd.to_datetime(s,errors="coerce",dayfirst=True)
def pull_api():
    rid=os.getenv("AGMARKNET_RESOURCE_ID"); token=os.getenv("DATA_GOV_IN_API_KEY")
    if not rid or not token: return []
    out=[]; limit=min(int(os.getenv("AGMARKNET_API_LIMIT","50000")),50000)
    for commodity in COMMODITIES:
        for offset in range(0,limit,500):
            r=requests.get(f"{API}/{rid}",params={"api-key":token,"format":"json","limit":500,"offset":offset,
             "filters[state]":"Tamil Nadu","filters[commodity]":commodity},timeout=45)
            r.raise_for_status(); records=r.json().get("records",[])
            if not records: break
            out.append(normalize(pd.DataFrame(records)))
            if len(records)<500: break
    return out
def main():
    frames=[]
    for f in glob.glob(str(RAW/"*")):
        if f.lower().endswith(".csv") and os.path.basename(f).lower().startswith(("apmc","commodity","agmarknet")):
            try: raw=pd.read_csv(f,encoding="utf-8")
            except UnicodeDecodeError: raw=pd.read_csv(f,encoding="latin-1")
            frames.append(normalize(raw))
    frames += pull_api()
    if not frames: raise SystemExit("No source CSVs found. Add a raw CSV or configure data.gov.in credentials/resource ID.")
    d=pd.concat(frames,ignore_index=True)
    d["arrival_date"]=parse_dates(d.arrival_date)
    for c in ("min_price","max_price","modal_price"):
        d[c]=pd.to_numeric(d[c].astype("string").str.replace(",","",regex=False),errors="coerce")
    # The standalone scraper is already restricted to state 33 and does not return a state column.
    d["state"]=d.state.fillna("Tamil Nadu").replace("", "Tamil Nadu")
    d=d[d.state.astype(str).str.contains(r"Tamil\s*Nadu|Tamil Nadu|^TN$|^33$",case=False,regex=True)]
    d["commodity"]=d.commodity.astype(str).str.strip().str.lower().map(VARIANTS)
    d=d.dropna(subset=["arrival_date","commodity","modal_price"])
    d=d.sort_values("modal_price").drop_duplicates(["arrival_date","market","commodity"],keep="last")
    coverage=d.assign(year=d.arrival_date.dt.year).groupby(["commodity","year"]).size().rename("records").reset_index()
    coverage.to_csv(REPORT/"data_coverage_summary.csv",index=False)
    d.to_parquet(PROC/"tn_vegetables_daily.parquet",index=False); d.to_csv(PROC/"tn_vegetables_daily.csv",index=False)
if __name__=="__main__": main()
