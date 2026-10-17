"""Download Koyambedu history from vegetablemarketprice.com into an auditable long-form dataset.

This captures published secondary daily history attributed to the Koyambedu Vegetable Merchants' Council. The public API exposes a 1kg unit label; preserve original series and values, and do not merge varieties without a documented rule.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

PAGE_URL = "https://vegetablemarketprice.com/market/koyambedu/history"
API_ROOT = "https://vegetablemarketprice.com/api/dataapi/market/koyambedu/chartdatavalues"
DEFAULT_START = "2021-11-04"
DEFAULT_END = date.today().isoformat()
VEGETABLE_IDS = [
    "tomato",
    "onionbig", "onionsmall", "oniongreen", "shallot",
    "potato", "cabbage", "carrot",
    "frenchbeans", "broadbeans", "clusterbeans", "butterbeans",
    "brinjal", "brinjalbig", "drumsticks",
]
MAX_WINDOW_DAYS = 180


def fetch_window(session: requests.Session, start: date, end: date) -> dict:
    params = {"start": start.isoformat(), "end": end.isoformat(),
              "vegIds": ",".join(VEGETABLE_IDS)}
    last_error = None
    for attempt in range(1, 5):
        try:
            response = session.get(API_ROOT, params=params, timeout=90)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt < 4:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Unable to fetch {start} through {end}") from last_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--output-dir", default="data/external")
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    if end_date < start_date:
        raise SystemExit("--end must be on or after --start")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "AgriSight research data feasibility extraction/1.0",
        "Accept": "application/json",
        "Referer": PAGE_URL,
    })

    rows, api_limits = [], set()
    cursor = start_date
    windows = 0
    extracted_at = datetime.now(timezone.utc).isoformat()

    while cursor <= end_date:
        window_end = min(cursor + timedelta(days=MAX_WINDOW_DAYS - 1), end_date)
        payload = fetch_window(session, cursor, window_end)
        windows += 1
        if not isinstance(payload, dict) or "columns" not in payload or "data" not in payload:
            raise RuntimeError(f"Unexpected response for {cursor} through {window_end}")

        api_limits.add(payload.get("startDateLimit"))
        columns, series_items = payload.get("columns", []), payload.get("data", [])
        name_to_id = {
            str(item.get("vegName", "")).casefold(): item.get("vegId")
            for item in payload.get("columnMapping", [])
            if isinstance(item, dict)
        }
        series_by_id = {}
        for series in series_items:
            if isinstance(series, dict):
                veg_id = name_to_id.get(str(series.get("name", "")).casefold())
                if veg_id:
                    series_by_id[veg_id] = series

        for veg_id in VEGETABLE_IDS:
            series = series_by_id.get(veg_id, {})
            values = series.get("data", [])
            series_name = series.get("name") or veg_id
            for index, day_text in enumerate(columns):
                value = values[index] if index < len(values) else None
                if not isinstance(value, dict):
                    value = {}
                rows.append({
                    "date": day_text,
                    "veg_id": veg_id,
                    "vegetable_series": series_name,
                    "price_value": value.get("yValue"),
                    "chart_value": value.get("y"),
                    "retailprice_range": value.get("retailprice"),
                    "units": value.get("units"),
                    "query_start": cursor.isoformat(),
                    "query_end": window_end.isoformat(),
                    "source_page": PAGE_URL,
                    "extracted_at_utc": extracted_at,
                })
        print(f"Fetched {cursor} to {window_end}: {len(columns)} dates, "
              f"{len(series_items)} series", flush=True)
        cursor = window_end + timedelta(days=1)

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("The source returned no date rows.")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["price_value"] = pd.to_numeric(frame["price_value"], errors="coerce")
    frame["chart_value"] = pd.to_numeric(frame["chart_value"], errors="coerce")
    frame = frame.drop_duplicates(["date", "veg_id"], keep="last")
    frame = frame.sort_values(["veg_id", "date"]).reset_index(drop=True)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "koyambedu_vegetablemarketprice_history.csv"
    parquet_path = out_dir / "koyambedu_vegetablemarketprice_history.parquet"
    metadata_path = out_dir / "koyambedu_vegetablemarketprice_metadata.json"
    frame.to_csv(csv_path, index=False, date_format="%Y-%m-%d")
    frame.to_parquet(parquet_path, index=False)

    grouped = []
    for veg_id, part in frame.groupby("veg_id", sort=False):
        observed = part.dropna(subset=["price_value"])
        series_names = part["vegetable_series"].dropna()
        grouped.append({
            "veg_id": veg_id,
            "series": str(series_names.iloc[0]) if len(series_names) else veg_id,
            "calendar_rows": int(len(part)),
            "observed_price_rows": int(len(observed)),
            "first_observed_date": observed["date"].min().strftime("%Y-%m-%d") if len(observed) else None,
            "last_observed_date": observed["date"].max().strftime("%Y-%m-%d") if len(observed) else None,
            "units": sorted(observed["units"].dropna().astype(str).unique().tolist()),
        })

    metadata = {
        "source_page": PAGE_URL,
        "api_endpoint": API_ROOT,
        "requested_start": start_date.isoformat(),
        "requested_end": end_date.isoformat(),
        "api_reported_start_date_limits": sorted(x for x in api_limits if x),
        "query_windows": windows,
        "row_definition": "One row per calendar date and selected website series; missing API values are retained as null.",
        "price_fields": {
            "price_value": "API yValue field, the site's plotted history price.",
            "chart_value": "API y field, retained separately for audit.",
            "retailprice_range": "API display range string, retained without reinterpretation.",
            "units": "API units field (observed as 1kg in July 2023 Tomato test).",
        },
        "limitations": [
            "The site describes this as Koyambedu market history, but its page warns that retail-market and shopping-mall prices may vary by area.",
            "The site's independent collection method and price definition have not been verified.",
            "Do not combine with Agmarknet prices until units and wholesale/retail meaning are validated.",
            "Varieties are kept separate; do not aggregate onion or bean varieties without an explicit documented rule.",
        ],
        "extracted_at_utc": extracted_at,
        "series": grouped,
        "files": [csv_path.name, parquet_path.name],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Rows written: {len(frame):,}")
    print(f"CSV: {csv_path}")
    print(f"Parquet: {parquet_path}")
    print(f"Metadata: {metadata_path}")
    print("Series summary (IDs; full names are in metadata JSON):")
    for item in grouped:
        print(f"{item['veg_id']}: {item['observed_price_rows']} observed dates, {item['first_observed_date']} to {item['last_observed_date']}")


if __name__ == "__main__":
    main()
