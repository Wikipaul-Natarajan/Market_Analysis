# Koyambedu History API Provenance and Field-Meaning Review

**Assessment date:** 2026-10-17

**Disposition:** Treat the values as genuine daily secondary observations published by the Koyambedu history page and attributed by the project to the Koyambedu Vegetable Merchants' Council. The API returns the daily values directly; no interpolation is applied to the Tomato July-August 2023 window. Keep price-series findings distinct from claims about independently audited wholesale transactions.

## Scope

Reviewed the local extractor, refreshed source metadata and CSV, derived eight-series panel, Koyambedu history page, the user's direct API spot check, and dated press coverage of the July 2023 Tomato event. This is a provenance and cross-check review, not a row-by-row audit of every source record.

## What the local files establish

- The extractor calls the history API for the Koyambedu-labeled page and retains the source price value and metadata.
- The 2026-10-17 extraction contains 27,135 date-series rows across 15 site series from 2021-11-04 through 2026-10-17. The API reports 30 null prices.
- The derived panel selects eight separate series and contains 14,472 populated values from 2021-11-04 through 2026-10-17.
- Values are copied from source yValue/price_value without interpolation. The unit field is 1kg.
- The project attributes the records to the Koyambedu Vegetable Merchants' Council. The public history URL is the retrieval citation; the project should archive any Council correspondence or source documentation used to verify attribution.

## Tomato daily-window check

The direct API check for 2023-07-03 through 2023-08-22 returns 51 daily observations with no gap in the selected series. Values confirmed by the project include:

| Date | Source value |
|---|---:|
| 2023-07-03 | INR 80/kg |
| 2023-07-14 | INR 125/kg |
| 2023-08-01 | INR 160/kg (window peak) |
| 2023-08-22 | INR 49/kg |

The full event summary is saved in outputs/reports/koyambedu_tomato_event_summary.json. These are direct API observations; no interpolation is needed. Dated news reports contain different snapshots on several dates. Those differences should be retained as a price-basis and independent-consistency limitation, not resolved by overwriting source observations.

## Citation

Vegetable Market Price. "Koyambedu Market Price History." https://vegetablemarketprice.com/market/koyambedu/history. Daily history API accessed 2026-10-17. Extracted by scripts/00_download_koyambedu_history.py.

The project attributes the series to the Koyambedu Vegetable Merchants' Council. Record the supporting Council provenance alongside the cited retrieval page in the final thesis.

## Use and interpretation

1. Treat the values as genuine secondary observations from the published history API and retain the API source values unchanged.
2. Describe the series as Koyambedu history-page observations. State the API's 1kg unit. Claims about a particular wholesale transaction price require supporting source documentation.
3. Keep the series mappings explicit: French Beans is a provisional Beans proxy; Onion uses Big Onion; regular Brinjal is not combined with Big Brinjal.
4. Procurement cost comparisons are counterfactual model analyses. They do not establish realized procurement savings without buyer transactions, quantity, operating costs, and constraints.

| Dimension | Result |
|---|---|
| API extraction coverage and row structure | Complete for retrieved extraction window; 30 null source prices in the 15-series raw extract |
| Koyambedu page label | Present in the source page/API |
| Daily Tomato rows, 2023-07-03 to 2023-08-22 | 51 direct observations; no gap |
| API unit | 1kg |
| Council attribution | Attributed by the project; supporting source record should be archived with the thesis |
| Wholesale transaction basis | Not specified as a separate field by the retrieved API |
| Other vegetable mapping | Retain documented mapping limitations |
