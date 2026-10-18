# Koyambedu Research Analysis — AgriSight Koyambedu

**Status: exploratory secondary-data analysis.** This is an exploratory analysis of genuine daily secondary observations retrieved from the Koyambedu history API and attributed to the Koyambedu Vegetable Merchants' Council. The site API identifies the unit as 1kg; no interpolation is applied.

## Data and scope

- Eight separate published series; 14,472 daily observed rows, 2021-11-04 to 2026-10-17.
- All eight series copy the website `yValue` source observation directly. Tomato values from 2023-07-03 through 2023-08-22 are copied directly from daily source responses; no interpolation is used.
- No varieties were combined. French Beans to Beans mapping remains provisional.
- API unit label is 1kg; the quote's wholesale/retail basis and Council data chain are unverified.
- Weather is observed Chennai data only from 2024 onward; no weather values were fabricated.

## Forecast comparison

Models were evaluated on common expanding-window origins (2025-01-01, 2025-04-01, 2025-07-01, 2025-10-01, 2026-01-01, 2026-04-01, 2026-07-01), the same eight commodities, and 7-, 14-, and 30-day direct horizons. At each origin, only price history available on or before that date was used. Metrics aggregate stored predictions across all origins, series, and horizons. WAPE and MAE are emphasized because MAPE can over-weight low-price periods. Results are exploratory and source-qualified.

| model          |   n_predictions |   rmse_inr_per_kg |   mae_inr_per_kg |   mape_pct |   smape_pct |   wape_pct |   origins |   commodities | horizons   |
|:---------------|----------------:|------------------:|-----------------:|-----------:|------------:|-----------:|----------:|--------------:|:-----------|
| NaiveLast      |             168 |              9.99 |             4.89 |      12.28 |       11.57 |      11.88 |         7 |             8 | 7,14,30    |
| SARIMA         |             168 |              9.83 |             5.05 |      12.81 |       12.01 |      12.28 |         7 |             8 | 7,14,30    |
| SeasonalNaive7 |             168 |             10.07 |             5.25 |      13.40 |       12.47 |      12.76 |         7 |             8 | 7,14,30    |
| XGBoost        |             168 |             10.82 |             6.32 |      14.35 |       13.66 |      15.36 |         7 |             8 | 7,14,30    |
| RandomForest   |             168 |             11.95 |             6.84 |      15.39 |       14.62 |      16.63 |         7 |             8 | 7,14,30    |
| Prophet        |             168 |             15.64 |             9.80 |      23.46 |       22.56 |      23.82 |         7 |             8 | 7,14,30    |

The lowest-WAPE method on this selected website panel is **NaiveLast** (11.88% WAPE), with **168** scored predictions. This ranks methods only on the selected published site series; it does not establish out-of-source market accuracy. Per-series/per-horizon predictions are in `koyambedu_model_predictions.csv`; per-commodity metrics are in `koyambedu_model_metrics_by_commodity.csv`.

### Run notes

- None.

## Northeast Monsoon

The descriptive table joins observed weather and prices in `koyambedu_monsoon_descriptive.csv` by joining observed weather to observed monthly price summaries for October–December 2024 and 2025. The weather file contains only two complete Northeast Monsoon seasons for this period and no long climatological baseline. Findings remain descriptive/limited evidence; no significance or causal claim is made. This objective remains open for the real study.

Observed rainfall totals in the available complete seasons (mm): {"2024": 846.7, "2025": 965.5}.

## Tomato price-episode findings

The Tomato observations move from ₹80/kg on 2023-07-03 to an observed peak of ₹160/kg on 2023-08-01 (100.0%), then reaches ₹49/kg on 2023-08-22. These are direct daily website values with no interpolation; the wholesale price basis is not independently audited. The proposal's ₹200/kg figure is not established as Koyambedu wholesale by this analysis.

No realized procurement savings are calculated: buyer transaction records, purchasing quantities, and a decision baseline are unavailable. A price spike alone cannot support a savings claim.

## Source citation

Vegetable Market Price. "Koyambedu Market Price History." https://vegetablemarketprice.com/market/koyambedu/history. Accessed on the extraction date; daily yValue fields were retained unchanged. The data are attributed to the Koyambedu Vegetable Merchants' Council.

## Conclusion and limitations

This run demonstrates that the data pipeline can produce aligned multi-horizon forecasts and reports for eight series. It does **not** complete the empirical research analysis. Before thesis claims, verify quote basis and source attribution; obtain historical rainfall covering the chosen price period; predefine the monsoon index and time-series inference; validate mappings; rerun the common evaluation protocol; and define procurement inputs before calculating hypothetical savings.
