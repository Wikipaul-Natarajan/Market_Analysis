# AgriSight POC

## Environment and inputs

Install dependencies using pip install -r requirements.txt. Run commands from the project root. Pipeline Python files are organized under `scripts/`; the shared helper writes data and outputs at the project root.

Use scripts/01_download_kaggle_prices.py to download only the 2024, 2025, and optionally 2026 annual files from the linked Kaggle dataset, then filter rows locally to Tamil Nadu, the eight target vegetables, and dates from 2024 onward. Kaggle provides annual files, so selected source files are downloaded first and then filtered in chunks. If the Kaggle CLI is unavailable, place year CSVs under data/raw/kaggle_years/ or its csv subfolder and the script will filter those local copies. Dataset source: https://www.kaggle.com/datasets/khandelwalmanas/daily-commodity-prices-india. Configure the official Kaggle CLI using KAGGLE_API_TOKEN or the Kaggle API credentials file, then set KAGGLE_DATASET/KAGGLE_YEARS in .env. The visible Kaggle notebook input currently lists CSVs through 2025; 2026 is attempted optionally and reported if unavailable. Weather extends through September 2026, but that does not extend the price series. scripts/01_download_agmarknet_legacy.py is retained only as the old live-scraper path and is not part of the main run.

To enable the optional data.gov.in import in script 02, set DATA_GOV_IN_API_KEY and AGMARKNET_RESOURCE_ID. Resource ID and API field filters should be checked against the currently published dataset. Offline APMC*.csv, commodity*.csv, and agmarknet*.csv files are also accepted.

Script 00 retrieves daily Chennai weather from the Open-Meteo Historical Weather API (archive-api.open-meteo.com/v1/archive) for 2024-01-01 through 2026-09-30 and saves data/external/weather_chennai.parquet with arrival_date, precipitation, temp_max, temp_avg, and related columns. To refresh or change coordinates/dates, set CHENNAI_LATITUDE, CHENNAI_LONGITUDE, WEATHER_START_DATE, and WEATHER_END_DATE. The full documented feature, ML, SHAP, agent, and dashboard path requires this weather file, including precipitation (or rain) and temp_max columns; temp_avg supplies the cold_day flag. Price-only EDA and SARIMA/Prophet stages can run without it, but downstream ML stages require complete configured feature columns.

Run scripts/00_download_weather_openmeteo.py and scripts/01_download_kaggle_prices.py, then run scripts/02_process_agmarknet.py → scripts/03_eda.py → scripts/04_feature_engineering.py → scripts/05_sarima_baseline.py → scripts/06_prophet_model.py → scripts/07_ml_models.py → scripts/08_shap_analysis.py → scripts/09_agrisight_agents.py → streamlit run scripts/10_dashboard.py.

The file agmarknet_tn_2010_2025.csv, if supplied, is external and not produced by script 01. The dashboard labels the 2024 cutoff as an input-window choice; it does not infer historical market reporting gaps from this filtered dataset.

## Forecasting and calendar notes

The workflow saves tables, reports, plots, and model pickles beneath data/processed and outputs. Keep the exact artifacts together when moving between stages; downstream scripts load the live summary CSVs.

Festival dates vary by lunar calendar and Ramadan end may depend on local moon sighting. Review holiday dates in script 06 for the target year/location. Synthetic agent/dashboard forecasts carry non-forecastable weather and market-count inputs forward from the last observation as described in the UI.
