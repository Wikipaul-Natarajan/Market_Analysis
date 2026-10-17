# Koyambedu published price history panel

This secondary-data panel copies each selected daily `price_value` (extracted API `yValue`) without changing it. It contains 14,472 rows across eight selected site series, from 2021-11-04 through 2026-10-17.

- CSV: `koyambedu_prices_daily.csv`
- History page: https://vegetablemarketprice.com/market/koyambedu/history
- API unit label: `1kg`. Retrieved page/API metadata do not establish whether the quote is wholesale or retail, or the data transmission chain.
- The data are attributed to the Koyambedu Vegetable Merchants' Council as supplied with this study. The capture is cited to the public history page/API; preserve this citation and retain the stated unit basis.
- No values are interpolated or fabricated. Missing dates remain missing.
- Mapping limits: Beans uses French Beans provisionally; Onion uses Big Onion; regular Brinjal is not combined with Big Brinjal.
- `is_validated_observation=True` means a populated value was returned by the source API, not that price basis or chain of custody was independently audited.

## Tomato check: 2023-07-03 to 2023-08-22

The source provides 51 daily rows. Values: 2023-07-03 = 80.00/kg; peak = 160.00/kg on 2023-08-01; 2023-08-22 = 49.00/kg. These are site-reported values, not independently audited wholesale prices.

## Citation

Vegetable Market Price. "Koyambedu Market Price History." https://vegetablemarketprice.com/market/koyambedu/history. Accessed 2026-10-17. Historical values retrieved from its daily-history API; extraction: `scripts/00_download_koyambedu_history.py`.
