"""Build a clearly labeled mock Koyambedu daily price panel for pipeline demonstrations.

This output is synthetic/proxy-based and must never be reported as observed research data.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "external" / "koyambedu_vegetablemarketprice_history.csv"
OUT_DIR = ROOT / "data" / "mock"
OUT_CSV = OUT_DIR / "koyambedu_mock_prices_daily.csv"
OUT_README = OUT_DIR / "README.md"

# Use one narrow, separate candidate website series for each proposal target.
SERIES = {
    "tomato": ("Tomato", "direct candidate; source price basis unresolved"),
    "onionbig": ("Onion Big", "Big Onion only; not merged with small/green onion"),
    "potato": ("Potato", "direct candidate; source price basis unresolved"),
    "cabbage": ("Cabbage", "direct candidate; source price basis unresolved"),
    "carrot": ("Carrot", "direct candidate; source price basis unresolved"),
    "frenchbeans": ("French Beans", "provisional Beans proxy; variety mapping unverified"),
    "brinjal": ("Brinjal", "regular Brinjal series only; not merged with Big Brinjal"),
    "drumsticks": ("Drumsticks", "candidate for Drumstick target; source price basis unresolved"),
}

# These are scenario anchors, not a reconstructed official daily series. Ranges are
# reduced to their midpoint for a convenient test target and flagged as such below.
TOMATO_ANCHORS = {
    "2023-07-03": (100.0, "New Indian Express reported Koyambedu wholesale at about INR 100/kg"),
    "2023-07-19": (92.0, "New Indian Express reported about INR 92/kg on Wednesday"),
    "2023-07-22": (120.0, "Midpoint of Times of India reported INR 110-130/kg on Saturday"),
    "2023-07-24": (85.0, "Midpoint of DT Next reported INR 70-100/kg for July 24"),
    "2023-07-26": (110.0, "Live Chennai reported INR 110/kg on July 26"),
    "2023-07-27": (140.0, "Live Chennai reported INR 140/kg on July 27"),
    "2023-07-30": (160.0, "DT Next reported INR 160/kg on Sunday, July 30"),
    "2023-07-31": (180.0, "DT Next reported INR 180/kg on Monday, July 31"),
    "2023-08-01": (160.0, "Approximate continuation; website proxy and mid-August retrospective peak mention"),
    "2023-08-13": (50.0, "Live Chennai reported INR 50/kg on Sunday, August 13"),
    "2023-08-22": (30.0, "New Indian Express reported INR 30/kg on Tuesday, August 22"),
}


def main() -> None:
    raw = pd.read_csv(INPUT, parse_dates=["date"])
    needed = {"date", "veg_id", "vegetable_series", "price_value", "units", "source_page"}
    missing = needed - set(raw.columns)
    if missing:
        raise ValueError(f"Source file is missing columns: {sorted(missing)}")

    parts = []
    for veg_id, (project_name, mapping_note) in SERIES.items():
        src = raw.loc[raw["veg_id"].eq(veg_id)].copy().sort_values("date")
        if src.empty:
            raise ValueError(f"Required source series is absent: {veg_id}")
        if src["date"].duplicated().any():
            raise ValueError(f"Duplicate dates in source series: {veg_id}")
        prices = pd.to_numeric(src["price_value"], errors="coerce")
        if prices.isna().any():
            raise ValueError(f"Missing source prices in selected series: {veg_id}; no imputation is applied")
        if (prices <= 0).any():
            raise ValueError(f"Non-positive price in selected source series: {veg_id}")

        src["project_commodity_candidate"] = project_name
        src["mapping_note"] = mapping_note
        src["source_price_proxy_inr_per_kg"] = prices.astype(float)
        src["mock_price_inr_per_kg"] = prices.astype(float)
        src["mock_value_method"] = "unvalidated website proxy; copied for pipeline demonstration"
        src["anchor_reference"] = ""
        src["is_mock_data"] = True
        src["is_validated_observation"] = False
        src["price_unit"] = "INR/kg (API says 1kg; price basis unverified)"
        src["source_status"] = "UNVALIDATED_WEBSITE_PROXY"

        if veg_id == "tomato":
            anchor_dates = pd.to_datetime(list(TOMATO_ANCHORS))
            anchor_values = np.array([TOMATO_ANCHORS[d][0] for d in TOMATO_ANCHORS], dtype=float)
            crisis = src["date"].between(anchor_dates.min(), anchor_dates.max())
            day_numbers = src.loc[crisis, "date"].map(pd.Timestamp.toordinal).to_numpy()
            anchor_numbers = np.array([d.toordinal() for d in anchor_dates], dtype=float)
            src.loc[crisis, "mock_price_inr_per_kg"] = np.interp(day_numbers, anchor_numbers, anchor_values)
            src.loc[crisis, "mock_value_method"] = "linear interpolation between dated press/site scenario anchors"
            src.loc[crisis, "source_status"] = "SYNTHETIC_SCENARIO_NOT_OBSERVED_DAILY_PRICE"
            for date_text, (_, ref) in TOMATO_ANCHORS.items():
                src.loc[src["date"].eq(pd.Timestamp(date_text)), "anchor_reference"] = ref

        parts.append(src[[
            "date", "project_commodity_candidate", "veg_id", "vegetable_series",
            "mock_price_inr_per_kg", "source_price_proxy_inr_per_kg", "price_unit",
            "mock_value_method", "source_status", "is_mock_data",
            "is_validated_observation", "mapping_note", "anchor_reference",
            "source_page", "extracted_at_utc",
        ]])

    result = pd.concat(parts, ignore_index=True).sort_values(["project_commodity_candidate", "date"])
    expected_dates = pd.date_range(result["date"].min(), result["date"].max(), freq="D")
    expected_rows = len(expected_dates) * len(SERIES)
    if len(result) != expected_rows:
        raise ValueError(f"Expected {expected_rows} complete panel rows; found {len(result)}")
    if result.duplicated(["date", "veg_id"]).any():
        raise ValueError("Duplicate date/series rows in output")
    if result["mock_price_inr_per_kg"].isna().any() or (result["mock_price_inr_per_kg"] <= 0).any():
        raise ValueError("Output contains missing or non-positive mock prices")
    if set(result["is_mock_data"].unique()) != {True} or set(result["is_validated_observation"].unique()) != {False}:
        raise ValueError("Mock/validation labels are inconsistent")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_CSV, index=False, date_format="%Y-%m-%d", float_format="%.2f")
    summary = {
        "file": OUT_CSV.name,
        "rows": len(result),
        "date_start": result["date"].min().strftime("%Y-%m-%d"),
        "date_end": result["date"].max().strftime("%Y-%m-%d"),
        "commodities": sorted(result["project_commodity_candidate"].unique().tolist()),
        "all_rows_mock": bool(result["is_mock_data"].all()),
        "all_rows_unvalidated": bool((~result["is_validated_observation"]).all()),
        "tomato_anchor_count": len(TOMATO_ANCHORS),
        "tomato_crisis_interpolated_rows": int(result["source_status"].eq("SYNTHETIC_SCENARIO_NOT_OBSERVED_DAILY_PRICE").sum()),
        "weather_included": False,
    }
    text = f'''# AgriSight Koyambedu mock price panel

This directory contains a **mock dataset for developing and demonstrating the forecasting workflow**. It is not a validated price history and must not be presented as empirical research results.

- File: `{OUT_CSV.name}`
- Coverage: {summary['date_start']} to {summary['date_end']}; {summary['rows']:,} rows across {len(SERIES)} separate series.
- All rows have `is_mock_data=True` and `is_validated_observation=False`.
- For the seven non-Tomato series, `mock_price_inr_per_kg` copies the selected website history API value as an approximate proxy. The unit is reported as 1kg by the API; wholesale/retail meaning remains unresolved.
- Tomato prices from 2023-07-03 through 2023-08-22 use a piecewise linear scenario between dated news/site anchors. The anchors/ranges and their reference are recorded in `anchor_reference`; days between anchors are interpolated, not observed. Where a news range was given, its midpoint is used solely for the mock test.
- `source_price_proxy_inr_per_kg` preserves the unmodified website value alongside the mock value.
- Series/variety mappings are kept narrow and identified in `mapping_note`; French Beans is only a provisional Beans proxy. No varieties are combined.
- There is no weather data in this file. Do not fabricate weather; join observed weather only for its available dates and keep earlier dates missing or use price-only models.
- Generation is deterministic and does not modify the original raw/external data.

## Suggested use

Use this panel to test data loading, date indexing, train/test splitting, model code, forecast exports, dashboard charts, and agent wiring. Use a separate evaluation label such as `DEMONSTRATION_ONLY`. Do not use these mock values to report forecast accuracy, statistical significance, monsoon effects, causal effects, crisis findings, or procurement savings in the thesis.

## Build

From the repository root, run:

```powershell
python scripts/11_build_koyambedu_mock_dataset.py
```

The script validates unique dates, complete eight-series daily coverage, positive values, and the mock/unvalidated flags before writing the CSV.

## Tomato scenario anchors

'''
    text += "| Date | Mock anchor (INR/kg) | Reference note |\\n|---|---:|---|\\n".replace("\\n", "\n")
    for date_text, (value, ref) in TOMATO_ANCHORS.items():
        text += f"| {date_text} | {value:.0f} | {ref} |\n"
    text += '''
## Reference links

- Koyambedu website history API/page: https://vegetablemarketprice.com/market/koyambedu/history
- New Indian Express, July 3, 2023: https://www.newindianexpress.com/states/tamil-nadu/2023/Jul/03/consumers-see-red-as-tomato-price-touches-a-record-rs-130kg-in-chennai-2590881.html
- New Indian Express, July 20, 2023: https://www.newindianexpress.com/states/tamil-nadu/2023/Jul/20/price-of-tomatoes-drops-by-rs-30kg-in-tamil-nadu-2596581.html
- Times of India, July 23, 2023: https://timesofindia.indiatimes.com/city/chennai/prices-of-vegetables-may-come-down-by-next-week/articleshow/102048728.cms
- DT Next, July 31, 2023: https://www.dtnext.in/news/city/tomato-price-shoots-up-to-rs-180-per-kg-in-koyambedu-wholesale-market-727236
- Live Chennai, July 27, 2023: https://www.livechennai.com/detailnews.asp?catid=163&newsid=67963
- Live Chennai, August 14, 2023: https://www.livechennai.com/detailnews.asp?newsid=68160
- New Indian Express, August 23, 2023: https://www.newindianexpress.com/cities/chennai/2023/aug/23/tomato-prices-plummet-in-chennai-after-fresh-arrivals-from-krishnagiri-karnataka-2607940.html
'''
    OUT_README.write_text(text, encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
