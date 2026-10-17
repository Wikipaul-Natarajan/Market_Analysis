# Proposal objective evaluation outputs

Source disposition: **SECONDARY_DATA_KOYAMBEDU_MERCHANTS_COUNCIL**. These outputs are exploratory price-series accuracy results and must not be represented as realized procurement savings.

## Matched horizon model evaluation

Common origin dates: 2025-08-23, 2025-12-21, 2026-04-20, 2026-08-18. Horizons: 7, 14 and 30 days. Models use the same origin and target dates; SeasonalNaive is included as a baseline. See `common_horizon_metrics.csv` and row-level `common_horizon_predictions.csv`.

The published benchmark is monthly and does not provide directly comparable daily 7/14/30-day forecasts; cross-study numeric comparison is therefore withheld.

## Monsoon association

Rainfall anomaly is standardized against the same calendar month within the local weather file, not a long-run climatology. HAC regression uses seven-day price return and controls for prior seven-day price momentum; market arrival volume is absent. The short local weather record (two complete Northeast Monsoon seasons) means p-values are exploratory and do not fulfill the proposal’s claim of a statistically established monsoon effect.

Market arrivals are not available in the local price panel.

## Procurement scenario

A rule-based 14-day XGBoost counterfactual was run on the local Tomato candidate series. It assumes a normalized one-quote-unit purchase, compares the advice timing with buying entirely at the origin, and omits storage, transport, spoilage, quality, stockouts and inventory constraints. The observations are attributed to the Koyambedu Vegetable Merchants' Council. The API unit is 1kg; this analysis does not independently establish wholesale transaction basis or realized economic value/savings.

Source citation: Vegetable Market Price. Koyambedu Market Price History. https://vegetablemarketprice.com/market/koyambedu/history (daily API values, accessed at extraction). The API unit is labeled 1kg. Procurement outputs are counterfactuals, not realized savings.
