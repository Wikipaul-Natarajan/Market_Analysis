# Observed procurement advice validation

**Status: exploratory counterfactual.** This backtest applies the current deterministic risk and action thresholds in `scripts/09_agrisight_agents.py` to stored XGBoost 14-day observed forecasts. Daily prices are copied from the published site series. The observations are attributed to the Council as reported by the project. API unit is 1kg; this report does not claim independently audited wholesale rates. Costs are counterfactual comparisons, not realized savings.

## Source and assumptions

Price source citation: Vegetable Market Price, "Koyambedu Market Price History," https://vegetablemarketprice.com/market/koyambedu/history (daily yValue history retrieved by scripts/00_download_koyambedu_history.py). Data are attributed to the Koyambedu Vegetable Merchants' Council.

## Counterfactual assumptions

- Each case represents a fixed 100 kg lot; buy-now baseline purchases the whole lot at the origin price.
- PROCURE NOW and HOLD buy the lot at origin; DELAY buys it at the 14-day outcome; PARTIAL PROCUREMENT and HEDGE split the lot equally between origin and day 14.
- The action labels and risk thresholds reproduce the existing advice rules. The fixed-lot translation is a backtest convention, not an operational procurement policy. In particular, DELAY is evaluated at day 14 although the production wording says reassess in 7 days.
- Excludes storage, transport, spoilage, inventory, quantity constraints, quality differences, and stockout/service costs. It does not establish causal savings or forecast validity.

## Results

- Evaluated cases: 56 (commodity × forecast origin).
- Cases with positive counterfactual cost difference vs buying immediately: 30.4%.
- Mean counterfactual cost difference per fixed lot: INR 66.07.
- Total counterfactual cost difference across these non-independent test cases: INR 3700.00.
- Review action-level counts and means in `koyambedu_procurement_advice_summary.csv`; case-level calculations are in `koyambedu_procurement_advice_backtest.csv`.

## Action breakdown

| advice_action       |   cases |   mean_counterfactual_difference_inr |   median_counterfactual_difference_inr |
|:--------------------|--------:|-------------------------------------:|---------------------------------------:|
| DELAY PROCUREMENT   |      14 |                             278.571  |                                    100 |
| HEDGE               |      10 |                              -5      |                                     25 |
| HOLD                |       9 |                               0      |                                      0 |
| PARTIAL PROCUREMENT |       9 |                             -16.6667 |                                      0 |
| PROCURE NOW         |      14 |                               0      |                                      0 |

These calculations are fixed-lot counterfactuals. Realized procurement outcomes require buyer transactions, stock and operating costs, and operational constraints.
