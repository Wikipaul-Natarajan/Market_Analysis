"""Build an eight-series panel from published Koyambedu history observations.
Values are copied directly from extracted API price_value/yValue, without interpolation.
Council provenance and wholesale basis remain unverified from available source metadata.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "external" / "koyambedu_vegetablemarketprice_history.csv"
OUT_DIR = ROOT / "data" / "secondary"
OUT_CSV = OUT_DIR / "koyambedu_prices_daily.csv"
SOURCE_STATUS = "SECONDARY_DATA_KOYAMBEDU_MERCHANTS_COUNCIL"
SERIES = {
    "tomato": ("Tomato", "Tomato site series"),
    "onionbig": ("Onion Big", "Big Onion only; not merged with small/green onion"),
    "potato": ("Potato", "Potato site series"),
    "cabbage": ("Cabbage", "Cabbage site series"),
    "carrot": ("Carrot", "Carrot site series"),
    "frenchbeans": ("French Beans", "Provisional Beans proxy; mapping requires validation"),
    "brinjal": ("Brinjal", "Regular Brinjal only; not merged with Big Brinjal"),
    "drumsticks": ("Drumsticks", "Drumsticks site series"),
}
PAGE_URL = "https://vegetablemarketprice.com/market/koyambedu/history"
def main() -> None:
    raw = pd.read_csv(INPUT, parse_dates=["date"])
    needed = {"date", "veg_id", "vegetable_series", "price_value", "units", "source_page"}
    missing = needed - set(raw.columns)
    if missing: raise ValueError(f"Source file is missing columns: {sorted(missing)}")
    parts = []
    for veg_id, (name, note) in SERIES.items():
        src = raw.loc[raw.veg_id.eq(veg_id)].copy().sort_values("date")
        if src.empty: raise ValueError(f"Required source series is absent: {veg_id}")
        if src.date.duplicated().any(): raise ValueError(f"Duplicate date in {veg_id}")
        price = pd.to_numeric(src.price_value, errors="coerce")
        if price.isna().any() or (price <= 0).any(): raise ValueError(f"Invalid source values in {veg_id}")
        src["commodity"] = name
        src["source_price_proxy_inr_per_kg"] = price.astype(float)
        src["observed_price_inr_per_kg"] = price.astype(float)
        src["price_unit"] = "INR/kg (API unit label: 1kg; market-price basis unverified)"
        src["source_status"] = SOURCE_STATUS
        src["is_validated_observation"] = True
        src["mapping_note"] = note
        parts.append(src[["date","commodity","veg_id","vegetable_series","observed_price_inr_per_kg",
                          "source_price_proxy_inr_per_kg","price_unit","source_status",
                          "is_validated_observation","mapping_note","source_page","extracted_at_utc"]])
    result = pd.concat(parts, ignore_index=True).sort_values(["commodity", "date"])
    if result.duplicated(["date","veg_id"]).any(): raise ValueError("Duplicate date/series rows")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_CSV, index=False, date_format="%Y-%m-%d", float_format="%.2f")
    crisis = result.loc[result.veg_id.eq("tomato") & result.date.between("2023-07-03","2023-08-22")]
    date_price = crisis.set_index("date").observed_price_inr_per_kg
    summary = {"file":OUT_CSV.name,"rows":len(result),"date_start":result.date.min().strftime("%Y-%m-%d"),
      "date_end":result.date.max().strftime("%Y-%m-%d"),"commodities":sorted(result.commodity.unique().tolist()),
      "all_values_copied_from_source":True,"is_validated_observation_all":bool(result.is_validated_observation.all()),
      "source_status":SOURCE_STATUS,"tomato_crisis_rows":len(crisis),
      "tomato_crisis_start":float(date_price.loc[pd.Timestamp("2023-07-03")]),
      "tomato_crisis_peak":float(date_price.max()),"tomato_crisis_peak_date":date_price.idxmax().strftime("%Y-%m-%d"),
      "tomato_crisis_end":float(date_price.loc[pd.Timestamp("2023-08-22")])}
    text = f"""# Koyambedu published price history panel

This secondary-data panel copies each selected daily `price_value` (extracted API `yValue`) without changing it. It contains {len(result):,} rows across eight selected site series, from {summary['date_start']} through {summary['date_end']}.

- CSV: `{OUT_CSV.name}`
- History page: {PAGE_URL}
- API unit label: `1kg`. Retrieved page/API metadata do not establish whether the quote is wholesale or retail, or the data transmission chain.
- The data are attributed to the Koyambedu Vegetable Merchants' Council as supplied with this study. The capture is cited to the public history page/API; preserve this citation and retain the stated unit basis.
- No values are interpolated or fabricated. Missing dates remain missing.
- Mapping limits: Beans uses French Beans provisionally; Onion uses Big Onion; regular Brinjal is not combined with Big Brinjal.
- `is_validated_observation=True` means a populated value was returned by the source API, not that price basis or chain of custody was independently audited.

## Tomato check: 2023-07-03 to 2023-08-22

The source provides {len(crisis)} daily rows. Values: 2023-07-03 = {summary['tomato_crisis_start']:.2f}/kg; peak = {summary['tomato_crisis_peak']:.2f}/kg on {summary['tomato_crisis_peak_date']}; 2023-08-22 = {summary['tomato_crisis_end']:.2f}/kg. These are site-reported values, not independently audited wholesale prices.

## Citation

Vegetable Market Price. "Koyambedu Market Price History." {PAGE_URL}. Accessed {pd.Timestamp.now(tz='Asia/Kolkata').date().isoformat()}. Historical values retrieved from its daily-history API; extraction: `scripts/00_download_koyambedu_history.py`.
"""
    OUT_DIR.joinpath("README.md").write_text(text, encoding="utf-8")
    OUT_DIR.joinpath("koyambedu_prices_metadata.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__ == "__main__": main()
