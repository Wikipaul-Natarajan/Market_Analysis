# AgriSight end-to-end rerun — 18 Oct 2026

Unzip at the repository root (paths mirror the repo). Or apply the git patch for tracked files.

## Code
- scripts/03_eda.py — ADF result unpacking fixed (test now runs; all 8 series stationary).
- scripts/10_dashboard.py — Research page rewritten for real koyambedu_* outputs (previously crashed); all 9 pages pass AppTest.
- scripts/12, 13, 14 — syntax/encoding fixes and input fallbacks (see step-1 CHANGES.md).
- scripts/16_horizon_sensitivity.py (new) — naive and strict 7-day checks for statewide models.
- scripts/17_report_figures.py (new) — 16 labelled figures for the report.

## Run order used
02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 12 → 13 → 14 → 15 → 16 → 17, then `streamlit run scripts/10_dashboard.py`.
00, 01 and 11 need network access; their committed outputs were used.

## Environment
Python 3.12.3, pandas 3.0.2, numpy 2.4.4, statsmodels 0.15.0, prophet 1.5.0, scikit-learn 1.8.0,
xgboost 3.4.1, shap 0.54.1, matplotlib 3.10.8, streamlit 1.66.0. Pin these in requirements.txt.

## Headline results
- Statewide 90-day holdout MAPE: SARIMA static 32.60, SARIMA 7-day WF 10.46, Prophet 19.33, RF 11.32, XGBoost 13.98.
- Same window: naive (yesterday) 4.20; naive (t-7) 9.10; XGBoost strict 7-day 27.09.
- Koyambedu WAPE (7 origins): Naive 11.88, SARIMA 12.28, SeasonalNaive7 12.76, XGBoost 15.36, RF 16.63, Prophet 23.82.
- Monsoon rainfall p = 0.26–0.92 (none significant); momentum negative and significant for all 8.
- Backtest: 30.4% of 56 cases better than buy-now; 2023 tomato scenario −₹120/kg cumulative.

## Script 15 live / local-LLM update
- Live fetches send a User-Agent and record failures as statuses (original code crashed with HTTP 403 against a feed that blocks default clients).
- News items are HTML-stripped, de-duplicated and capped; the weather forecast is summarised numerically in the brief.
- Local-LLM writer: refuses non-local endpoints; accepts a rewrite only if all price/forecast/weather numbers are preserved and none invented, otherwise uses the template.
- Endpoints configurable via AGRI_WEATHER_URL, AGRI_PIB_RSS, AGRI_OLLAMA_URL, AGRI_OLLAMA_MODEL, AGRI_OLLAMA_TIMEOUT, AGRI_MAX_NEWS.
- tests/fixture_server.py + tests/test_live_paths.py: 4/4 scenarios pass. Offline output unchanged.
- RUN_LIVE.md: steps for the real live run on Windows.

## Proposal alignment (script 18)
- SHAP ranking of a Northeast Monsoon deviation index against price features (Koyambedu, 7-day XGBoost), with beeswarm and dependence plots.
- Delta-accuracy test: XGBoost with vs without weather context, 27 weekly origins Apr–Sep 2026, Diebold–Mariano tests.
- Tomato 2023 scenario with the 30-day forecast specified in the proposal, plus signal-value and rule comparison.
- Report: approved proposal title restored; deviations table (Section 3.12); new Sections 4.11.2, 4.11.3 and 4.14.1.
