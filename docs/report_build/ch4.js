const { d, P, chapter, H2, H3, bullets, table, figure } = require('./lib');
const { AlignmentType } = d;
const F = require('./facts.json');
const L = AlignmentType.LEFT;
const n0 = v => Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 });
const n2 = v => Number(v).toFixed(2);
const ORDER8 = ['Beans', 'Brinjal', 'Cabbage', 'Carrot', 'Drumstick', 'Onion', 'Potato', 'Tomato'];
const pct = v => `${n2(v)}%`;
const money = v => `${Number(v) < 0 ? '−' : ''}₹${n2(Math.abs(Number(v)))}`;

function ch4() {
  // ---------- statewide descriptive
  const desc = { Beans: [48382, 506, 6979, 7000, 2032, 110, 16000, 29], Brinjal: [55050, 504, 4048, 4000, 1028, 50, 6400, 25], Cabbage: [49072, 504, 2723, 2500, 790, 48, 5000, 29],
    Carrot: [49130, 504, 6061, 6000, 2010, 70, 12500, 33], Drumstick: [50268, 504, 8240, 7000, 5103, 100, 21500, 62], Onion: [59560, 503, 3993, 3250, 1543, 45, 7000, 39],
    Potato: [47305, 504, 4078, 4000, 951, 48, 5500, 23], Tomato: [55621, 512, 2774, 2500, 1331, 40, 6500, 48] };
  const descRows = ORDER8.map(c => [c, ...desc[c].map((v, i) => i === 7 ? `${v}%` : n0(v))]);
  descRows.push(['Total / range', '414,388', '4,041', '', '', '', '', '', '23–62%']);

  // ---------- ADF
  const adf = [['Beans', -3.99, '0.0014', 5], ['Brinjal', -4.37, '0.0003', 4], ['Cabbage', -4.82, '<0.0001', 1], ['Carrot', -4.66, '0.0001', 2],
    ['Drumstick', -5.63, '<0.0001', 4], ['Onion', -5.15, '<0.0001', 2], ['Potato', -4.43, '0.0003', 2], ['Tomato', -6.25, '<0.0001', 6]]
    .map(r => [r[0], n2(r[1]), r[2], r[3], 'Reject unit root']);

  // ---------- statewide models
  const sar = Object.fromEntries(F.sarima.map(r => [r.commodity, r]));
  const pro = Object.fromEntries(F.prophet.map(r => [r.commodity, r]));
  const ml = {}; F.ml.forEach(r => { ml[r.commodity] = ml[r.commodity] || {}; ml[r.commodity][r.model] = r; });
  const sw = ORDER8.map(c => [c, (n => `(${n[0]},${n[1]},${n[2]})(${n[3]},${n[4]},${n[5]})₇`)(sar[c].order.match(/\d+/g)),
    n2(sar[c].mape), n2(sar[c].walk_forward_mape), n2(pro[c].mape), n2(ml[c].RF.mape), n2(ml[c].XGBoost.mape), n2(sar[c].naive_mape)]);
  const mean = k => (ORDER8.reduce((a, c) => a + k(c), 0) / 8);
  sw.push(['Mean', '', n2(mean(c => sar[c].mape)), n2(mean(c => sar[c].walk_forward_mape)), n2(mean(c => pro[c].mape)), n2(mean(c => ml[c].RF.mape)), n2(mean(c => ml[c].XGBoost.mape)), n2(mean(c => sar[c].naive_mape))]);
  const rmse = ORDER8.map(c => [c, n0(sar[c].walk_forward_rmse), n0(pro[c].rmse), n0(ml[c].RF.rmse), n0(ml[c].XGBoost.rmse), n0(ml[c].RF.mae), n0(ml[c].XGBoost.mae)]);

  // ---------- horizon sensitivity
  const hs = {}; F.hs.forEach(r => { hs[r.commodity] = hs[r.commodity] || {}; hs[r.commodity][r.variant] = r.mape_pct; });
  const V = ['Naive_t-1', 'Naive_t-7', 'XGB_original', 'XGB_no_own_lag1', 'XGB_strict_7day'];
  const hsRows = ORDER8.map(c => [c, ...V.map(v => n2(hs[c][v]))]);
  const hm = Object.fromEntries(F.hs_mean.map(r => [r.variant, r.mape_pct]));
  hsRows.push(['Mean', ...V.map(v => n2(hm[v]))]);

  // ---------- SHAP
  const own = Object.fromEntries(F.shap_own.map(r => [r.c, r.v]));
  const nice = f => f.replace(/cross_(\w+)_lag1/, '$1 price (t-1)').replace('position_52w', '52-week position').replace('rolling_mean_7', '7-day mean').replace('rolling_max_7', '7-day max')
    .replace('ema_7', '7-day EMA').replace('ema_14', '14-day EMA').replace('lag_14', 'Price t-14').replace('rain_30d_sum', '30-day rainfall').replace('temp_max', 'Max temperature');
  const shapRows = F.shap.map(r => [r.commodity, nice(r.top1), nice(r.top2), nice(r.top3), `${n2(own[r.commodity])}%`]);

  // ---------- Koyambedu
  const kd = [['French Beans (Beans)', 55.9, 54, 21.2, 20, 185, 38.0], ['Brinjal', 31.0, 31, 8.3, 17, 84, 26.6], ['Cabbage', 24.5, 25, 6.0, 10, 50, 24.3], ['Carrot', 43.5, 42, 10.1, 22, 74, 23.3],
    ['Drumsticks', 80.7, 70, 41.2, 30, 270, 51.1], ['Onion Big (Onion)', 31.6, 29, 10.9, 16, 69, 34.6], ['Potato', 29.7, 29, 5.7, 14, 49, 19.2], ['Tomato', 31.7, 26, 18.9, 10, 160, 59.4]]
    .map(r => [r[0], '1,809', r[1].toFixed(1), r[2], r[3].toFixed(1), r[4], r[5], `${r[6].toFixed(1)}%`]);
  const ko = F.k_overall.map(r => [r.model, r.n_predictions, n2(r.mae_inr_per_kg), n2(r.rmse_inr_per_kg), n2(r.mape_pct), n2(r.smape_pct), n2(r.wape_pct)]);
  const kh = F.k_h.map(r => [r.model, n2(r['7']), n2(r['14']), n2(r['30'])]);
  const kb = {}; F.k_by.forEach(r => { kb[r.commodity] = kb[r.commodity] || {}; kb[r.commodity][r.model] = r.wape_pct; });
  const KM = ['NaiveLast', 'SeasonalNaive7', 'SARIMA', 'Prophet', 'RandomForest', 'XGBoost'];
  const kbRows = Object.keys(kb).sort().map(c => { const best = KM.reduce((a, m) => kb[c][m] < kb[c][a] ? m : a, KM[0]);
    return [c, ...KM.map(m => m === best ? `**${n2(kb[c][m])}**` : n2(kb[c][m]))]; });
  const mh = {}; F.mh.forEach(r => { mh[r.model] = mh[r.model] || {}; mh[r.model][r.horizon_days] = r; });
  const mhRows = ['SeasonalNaive', 'SARIMA', 'RF', 'XGBoost', 'Prophet'].map(m => [m === 'SeasonalNaive' ? 'Naive (last value)' : m === 'RF' ? 'Random Forest' : m,
    ...[7, 14, 30].map(h => n2(mh[m][h].mape_pct)), ...[7, 14, 30].map(h => n2(mh[m][h].mae))]);

  // ---------- HAC
  const hac = F.hac.map(r => [r.commodity, r.n, n2(r.rain_anomaly_coef), n2(r.rain_anomaly_hac_se), r.rain_anomaly_pvalue.toFixed(3), r.price_momentum_coef.toFixed(3),
    r.price_momentum_pvalue < 0.001 ? '<0.001' : r.price_momentum_pvalue.toFixed(3), r.r_squared.toFixed(3)]);

  // ---------- Agents
  const ag = F.agents.map(r => [r.commodity, n0(r.current_price), n0(r.forecast_7d), n0(r.forecast_14d), `${r.forecast_14d_change_pct >= 0 ? '+' : ''}${r.forecast_14d_change_pct.toFixed(1)}%`,
    r.risk_score.toFixed(1), r.risk, r.action, r.signal]);
  const br = [['Beans', 7600, 7333, 7336, -3.5], ['Brinjal', 3500, 3374, 3373, -3.6], ['Cabbage', 2250, 2235, 2236, -0.6], ['Carrot', 3750, 3882, 3951, 5.4],
    ['Drumstick', 3750, 3835, 3818, 1.8], ['Onion', 2500, 2492, 2486, -0.5], ['Potato', 2800, 2862, 2854, 1.9], ['Tomato', 2750, 2602, 2467, -10.3]]
    .map(r => [r[0], n0(r[1]), n0(r[2]), n0(r[3]), `${r[4] > 0 ? '+' : ''}${r[4].toFixed(1)}%`, 'ABSTAIN_STALE_DATA']);

  // ---------- Backtest + crisis
  const bt = F.bt_sum.map(r => [r.advice_action, r.cases, money(r.mean_counterfactual_difference_inr), money(r.median_counterfactual_difference_inr)]);
  const cr = F.crisis.map(r => [r.origin, n2(r.current_source_value), n2(r.predicted_source_value), n2(r.actual_source_value), r.action, r.risk, n2(r.scenario_difference_vs_buy_now_source_units)]);
  const crTot = F.crisis.reduce((a, r) => a + r.scenario_difference_vs_buy_now_source_units, 0);


  // ---------- proposal-alignment analyses (script 18)
  const pr = F.pa_shap.map(r => [r.commodity, `${n2(r.lag_1_share_pct)}%`, `${r.ne_monsoon_deviation_rank} of ${r.n_features}`, `${n2(r.ne_monsoon_deviation_share_pct)}%`,
    `${r.rain_anomaly_7d_rank} of ${r.n_features}`, `${n2(r.all_weather_share_pct)}%`]);
  const dl = F.pa_delta.map(r => [`${r.horizon_days} days`, r.forecasts, n2(r.naive_wape), n2(r.xgb_price_only_wape), n2(r.xgb_with_weather_wape),
    `${r.delta_wape_pts >= 0 ? '+' : ''}${n2(r.delta_wape_pts)}`, r.dm_p.toFixed(3), r.dm_vs_naive_p.toFixed(3)]);
  const c30 = F.pa_crisis.filter(r => r.horizon_days === 30).map(r => [r.origin, n2(r.price_at_origin), n2(r.forecast), n2(r.actual_at_target),
    `${r.forecast_change_pct >= 0 ? '+' : ''}${r.forecast_change_pct.toFixed(0)}%`, r.risk, r.action, n2(r.result_vs_buy_now_inr_per_kg)]);
  const pv = [14, 30].map(h => { const v = F.pa_value[String(h)], s = F.pa_crisis_sum.find(r => r.horizon_days === h), ru = F.pa_rule[String(h)];
    return [`${h} days`, `${v.rise_signals_correct} of ${v.rise_signals}`, money(v.forward_buy_value_total), `${v.fall_signals_correct} of ${v.fall_signals}`,
      money(v.deferral_value_total), `**${money(v.net_signal_value)}**`, money(s.cumulative_result), money(ru.direction_only)]; });

  return [
    ...chapter(4, 'Data Analysis and Interpretation'),
    P('This chapter presents the results in the order of the research questions: the data and their quality (Sections 4.1–4.4), statewide forecasting and its diagnosis (4.5–4.7), Koyambedu multi-horizon evaluation (4.8–4.10), the monsoon and weather-context tests (4.11), the multi-agent decision layer (4.12), the procurement backtest and tomato case study (4.13–4.14), and a summary of hypotheses and objectives (4.15–4.16). All figures and tables come from a single end-to-end run of the analysis pipeline (Appendices 3 and 4).'),

    H2('4.1 Profile of the Statewide Data'),
    P('The statewide extract contains 414,388 market-level records for the eight vegetables from 451 markets in 36 districts between 24 January 2024 and 20 April 2026, with no missing values in any field. After aggregation to the daily statewide median and construction of 30-day lag features, the modelling table contains 4,041 commodity-days (about 504 days per vegetable) and 62 columns.'),
    ...table('Statewide records and daily median modal price (₹/quintal)', ['Commodity', 'Market records', 'Days', 'Mean', 'Median', 'Std. dev.', 'Min', 'Max', 'CV'], descRows,
      { widths: [1.2, 1.1, 0.7, 0.8, 0.8, 0.8, 0.6, 0.8, 0.6], size: 18, source: 'Author’s analysis of the statewide data.' }),
    ...figure('report/fig_4_1_records.png', 'Statewide market-level records by commodity and market type', { source: 'Author’s analysis.' }),
    P('**Interpretation.** Drumstick (CV 62%) and Tomato (48%) are the most volatile series and Potato (23%) and Brinjal (25%) the least, consistent with the perishability ranking expected from the literature. The most important structural fact is shown in Figure 4.1: **90.7% of all records come from Uzhavar Sandhai**, the state’s farmers’ markets, and only 9.3% from other regulated markets. A “statewide median” in this dataset is therefore largely a farmers’-market price. It is closer to a retail price than to the bulk wholesale price a procurement buyer pays, and this conditions every downstream use of Track A.'),

    H2('4.2 Data Quality Assessment'),
    ...table('Data quality checks on the statewide data', ['Check', 'Result', 'Treatment'], [
      ['Missing values', 'None in any of 10 fields', 'None needed'],
      ['Duplicate date–market–commodity keys', 'Removed during cleaning', 'Last record kept'],
      ['Extreme values > ₹100,000/quintal', '3 records (Drumstick ₹180,000; Tomato ₹353,000 and ₹404,000)', 'Removed and logged'],
      ['Implausibly low values < ₹300/quintal', '11,344 records (2.74%), 7,562 of them in June 2024', 'Not removed; flagged as likely per-kg entries'],
      ['Commodity-days affected by low values', '104 of 4,041 (12 per vegetable; 20 for Tomato)', 'Inflate holdout errors when in the test window'],
      ['Rolling z-score anomalies (Tomato, |z| > 2.5)', '34 days', 'Retained; genuine spikes and data errors'],
      ['Calendar gaps', 'Up to 3 missing days forward-filled; longer gaps left missing', 'Rows with incomplete features dropped'],
    ], { widths: [2.0, 2.6, 2.0], size: 18, align: [L, L, L], source: 'Author’s analysis.' }),
    P('**Interpretation.** The data are complete but not clean. The cluster of values below ₹300 per quintal in June–July 2024, when the same vegetables otherwise trade at ₹2,000–8,000, is consistent with prices entered per kilogram in a per-quintal field. These days appear as sharp troughs in Figure 4.2. They also strengthen the cross-commodity correlations, because all eight series fall together on those days. They should be corrected at source before any operational use.'),
    ...figure('report/fig_4_5_tomato_anomalies.png', 'Tomato daily statewide median with rolling-z anomalies and suspected unit errors', { source: 'Author’s analysis.' }),

    H2('4.3 Price Behaviour: Trend, Seasonality and Co-movement'),
    ...figure('report/fig_4_2_monthly_trends.png', 'Monthly median of daily statewide modal price by commodity', { maxH: 600, source: 'Author’s analysis.' }),
    ...figure('report/fig_4_3_seasonal_index.png', 'Seasonal price index by calendar month (annual mean = 100)', { source: 'Author’s analysis.' }),
    P('**Interpretation of seasonality.** Over the 27 months available, most vegetables were cheapest between March and May and dearest in the second half of the year. Tomato’s index ranges from 63 in March to 149 in October, Onion’s from 63 in April to 147 in October, and Carrot and Potato peak in August (136 and 117). Drumstick shows the widest swing, from 50 in March to 191 in January. With only about two observations of each calendar month, these indices are indicative rather than stable estimates, but they agree with the national pattern reported by Ajmal et al. (2024) and Roy et al. (2024), which describes tomato as dearest in the second half of the year and onion as peaking towards the end of the year.'),
    ...figure('report/fig_4_4_correlation.png', 'Correlation of monthly median prices across commodities', { width: .8, source: 'Author’s analysis.' }),
    P('**Interpretation of co-movement.** Brinjal, Cabbage, Carrot and Potato move closely together (r = 0.90–0.93), and Tomato and Onion correlate at 0.80 with each other and with Potato. Drumstick is largely independent of the others (r = 0.27–0.51), consistent with its distinct tree-crop supply cycle. Part of the high co-movement reflects the common unit-error days noted in Section 4.2. Nonetheless, the pattern supports the use of cross-commodity features and matches the horizontal volatility transmission found by Padhi et al. (2023).'),

    H2('4.4 Stationarity Testing'),
    ...table('Augmented Dickey–Fuller test on daily statewide median price', ['Commodity', 'ADF statistic', 'p-value', 'Lags used', 'Decision (5%)'], adf,
      { widths: [1.3, 1.2, 1.0, 0.9, 1.6], source: 'Author’s analysis.' }),
    P('**Interpretation.** The null hypothesis of a unit root is rejected for all eight series at the 1% level. Over this window the daily prices are mean-reverting around a level rather than drifting like a random walk. This is consistent with the SARIMA order selection in Table 4.4, where *d* = 0 was chosen for every commodity, and with the negative momentum coefficients found in Section 4.11.'),

    H2('4.5 Statewide Forecasting Results'),
    ...table('Statewide 90-day holdout MAPE (%) by commodity and model', ['Commodity', 'SARIMA order', 'SARIMA static', 'SARIMA 7-day WF', 'Prophet', 'Random Forest', 'XGBoost', 'Naive (static)'], sw,
      { widths: [1.1, 1.5, 0.9, 0.9, 0.8, 0.9, 0.8, 0.9], size: 17, source: 'Author’s analysis (protocols A1 and A2). “Naive (static)” repeats the last training value for all 90 days.' }),
    ...table('Statewide holdout RMSE and MAE (₹/quintal)', ['Commodity', 'SARIMA WF RMSE', 'Prophet RMSE', 'RF RMSE', 'XGBoost RMSE', 'RF MAE', 'XGBoost MAE'], rmse,
      { widths: [1.2, 1, 1, 0.9, 1, 0.9, 1], size: 18, source: 'Author’s analysis.' }),
    ...figure('report/fig_4_6_statewide_models.png', 'Statewide 90-day holdout MAPE by commodity and model', { source: 'Author’s analysis.' }),
    P('**Interpretation.** Three conclusions follow, but they must be read with the protocol differences in Table 3.4 in mind.'),
    ...bullets([
      '**Static forecasts are poor.** A single 90-day SARIMA forecast averages 32.60% MAPE and Prophet 19.33%. Over a full quarter both models largely extrapolate a level or trend that the market then departs from, with errors above 50% for Carrot, Drumstick and Tomato under SARIMA.',
      '**Frequent refitting matters more than model class.** Refitting SARIMA every seven days cuts its error to 10.46%, better than both tree models on average. Random Forest (11.32%) beat XGBoost (13.98%) for all eight commodities.',
      '**Note on second-review figures.** The tree-model error presented at the second review (6.28%) came from an earlier feature build and could not be reproduced. The figures above are the reproducible results and supersede it.']),
    P('More importantly, Protocol A2 scores **next-day** predictions, because the newest price information in the features is from the previous day (Section 3.4). Whether a 10–14% next-day error is good can only be judged against a next-day benchmark. Section 4.6 provides that benchmark.'),

    H2('4.6 Horizon Sensitivity: Is the Statewide Accuracy Real Forecasting Skill?'),
    P('Protocol A3 reruns A2 on the identical 90-day test window and adds two naive benchmarks and two altered XGBoost feature sets: one without the model’s own previous-day price, and one in which every price and cross-commodity feature is rebuilt from information at least seven days old, which is a genuine seven-day-ahead forecast.'),
    ...table('Horizon sensitivity on the statewide 90-day test window: MAPE (%)', ['Commodity', 'Naive: yesterday', 'Naive: 7 days ago', 'XGBoost (original features)', 'XGBoost w/o own t-1', 'XGBoost strict 7-day'], hsRows,
      { widths: [1.2, 1, 1, 1.1, 1.1, 1.1], size: 18, source: 'Author’s analysis (protocol A3).' }),
    ...figure('report/fig_4_7_horizon_sensitivity.png', 'Mean MAPE of naive benchmarks and XGBoost variants on the same test window', { source: 'Author’s analysis.' }),
    ...figure('report/fig_4_8_tomato_holdout.png', 'Tomato statewide holdout: actual price, Random Forest, XGBoost and yesterday’s price', { source: 'Author’s analysis.' }),
    P('**Interpretation.** This is the pivotal result of Track A. **Simply using yesterday’s price gives 4.20% mean MAPE**, beating XGBoost (13.71%) for every one of the eight commodities. Even the price from seven days earlier (9.10%) beats the tree models’ next-day predictions. When XGBoost is forced to forecast genuinely seven days ahead, its error rises to 27.09%, three times the seven-day naive benchmark, with especially poor results for Drumstick (94.71%) and Tomato (41.59%).'),
    P('The tree models therefore do not add forecasting skill on this data; they add noise to a persistence signal. Two causes are likely. First, the daily statewide median is a noisy aggregate of about 80–160 reporting markets whose composition changes day to day. Second, with only about 400 training days per commodity and 38 features, the models overfit transient patterns. For a procurement buyer the practical lesson is that the minimum benchmark for any vendor or in-house forecast is the latest observed price at the horizon of the decision.'),

    H2('4.7 Model Explanation with SHAP'),
    ...table('Top three SHAP drivers and share of attribution from own previous-day price', ['Commodity', 'Driver 1', 'Driver 2', 'Driver 3', 'Own t-1 share of |SHAP|'], shapRows,
      { widths: [1.1, 1.6, 1.5, 1.5, 1.1], size: 18, align: [L, L, L, L, AlignmentType.CENTER], source: 'Author’s analysis (XGBoost refit on all eligible rows).' }),
    ...figure('report/fig_4_9_shap.png', 'SHAP attribution: top features averaged over the eight models, and share from the own previous-day price', { source: 'Author’s analysis.' }),
    P('**Interpretation.** The position of the previous day’s price within its 52-week range is the most important feature on average, and each commodity’s **own previous-day price** (entered through the cross-commodity block) is the top driver for Beans, Brinjal, Carrot and Drumstick, accounting for 17–37% of total attribution in those models. Weather features appear in the top three only for Brinjal (30-day rainfall) and Drumstick (maximum temperature), and calendar and festival flags do not appear at all. In other words, the fitted models mostly encode “tomorrow will look like today, relative to the past year”. This agrees with the horizon-sensitivity result: the information that drives the predictions is persistence, which a naive forecast captures more cleanly. SHAP values describe model behaviour and are not causal effects (Molnar, 2022).'),

    H2('4.8 Profile of the Koyambedu Series'),
    ...table('Koyambedu daily price series (₹/kg), 4 Nov 2021 – 17 Oct 2026', ['Series (study commodity)', 'Days', 'Mean', 'Median', 'Std. dev.', 'Min', 'Max', 'CV'], kd,
      { widths: [1.8, 0.7, 0.7, 0.7, 0.8, 0.6, 0.6, 0.7], size: 18, source: 'Author’s analysis of Vegetable Market Price (n.d.).' }),
    ...figure('report/fig_4_10_koyambedu_panel.png', 'Koyambedu history-page daily prices by series', { maxH: 600, source: 'Author’s analysis.' }),
    P('**Interpretation.** The Koyambedu panel is complete (1,809 consecutive days for each series, no gaps) and covers almost five years, including the 2023 tomato episode that the statewide data cannot reach. Tomato is again the most volatile series (CV 59.4%), followed by Drumsticks (51.1%) and French Beans (38.0%). Between 3 July and 22 August 2023 the Tomato series contains 51 daily observations, rising from ₹80/kg to a peak of ₹160/kg on 1 August (+100%) before falling to ₹49/kg on 22 August (−69.4%). Prices in this panel are in ₹/kg and are not directly comparable with the ₹/quintal statewide series.'),

    H2('4.9 Koyambedu Multi-Horizon Model Comparison (Protocol B1)'),
    P('Six methods were evaluated at the same seven quarterly origins from 1 January 2025 to 1 July 2026, for 7-, 14- and 30-day horizons and all eight series, giving 168 scored forecasts per method.'),
    ...table('Koyambedu model comparison pooled over origins, series and horizons (₹/kg)', ['Model', 'Forecasts', 'MAE', 'RMSE', 'MAPE %', 'sMAPE %', 'WAPE %'], ko,
      { widths: [1.5, 0.9, 0.8, 0.8, 0.9, 0.9, 0.9], source: 'Author’s analysis (protocol B1).' }),
    ...table('Koyambedu WAPE (%) by forecast horizon', ['Model', '7 days', '14 days', '30 days'], kh,
      { widths: [1.6, 1, 1, 1], source: 'Author’s analysis.' }),
    ...figure('report/fig_4_12_koyambedu_horizon.png', 'Koyambedu WAPE by forecast horizon and model', { source: 'Author’s analysis.' }),
    ...table('Koyambedu WAPE (%) by series and model (lowest in bold)', ['Series', 'Naive', 'Seasonal naive', 'SARIMA', 'Prophet', 'Random Forest', 'XGBoost'], kbRows,
      { widths: [1.3, 0.8, 1.0, 0.8, 0.8, 1.0, 0.9], size: 18, source: 'Author’s analysis.' }),
    P('**Interpretation.** At procurement-relevant horizons the **last observed price is the best single forecast** (11.88% WAPE), with SARIMA a close second (12.28%). Both tree models and Prophet are worse at every horizon. The ranking is stable across horizons: at 7 days the naive, seasonal-naive and SARIMA forecasts are all near 8%, and by 30 days all methods converge at 18–25%. The tree models win only for Brinjal (Random Forest, 4.30%) and Carrot (XGBoost, 8.42%), both low-volatility series. The naive forecast or SARIMA wins for the volatile ones (Tomato, Drumsticks, Onion, French Beans). The seasonal naive equals the naive forecast at 7 and 14 days by construction (Table 3.3), so its separate contribution appears only at 30 days, where it is worse. These results are consistent with the M-competition evidence that complex methods frequently fail to beat simple ones (Makridakis et al., 2018a).'),

    H2('4.10 Matched-Horizon Robustness Check (Protocol B2)'),
    ...table('Koyambedu matched-horizon evaluation, 4 origins: mean MAPE (%) and MAE (₹/kg)', ['Model', 'MAPE 7d', 'MAPE 14d', 'MAPE 30d', 'MAE 7d', 'MAE 14d', 'MAE 30d'], mhRows,
      { widths: [1.6, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8], size: 18, source: 'Author’s analysis (protocol B2).' }),
    P('**Interpretation.** A second, independent set of four origins (23 August 2025 to 18 August 2026) gives the same ordering: the naive forecast is lowest at all three horizons (8.58%, 12.94% and 17.31% MAPE), SARIMA is close behind, and Prophet is worst. With only four origins the differences between the naive forecast, SARIMA and the tree models at 30 days are small and would not pass a formal significance test. The consistent conclusion across B1 and B2 is that **no model reliably beats the naive benchmark**, which answers research question 2 and leaves benchmark hypothesis H0 unrejected.'),

    H2('4.11 Northeast Monsoon and Weather Context'),
    H3('4.11.1 Regression test of the monsoon effect'),
    P(`Observed Chennai rainfall during the October–December Northeast Monsoon was 846.7 mm in 2024 and 965.5 mm in 2025, the only two complete seasons in the weather file. The HAC regression of Section 3.7 was estimated for each Koyambedu series on 1,000 overlapping daily observations.`),
    ...table('HAC regression of forward 7-day price return on rainfall anomaly and prior momentum', ['Commodity', 'n', 'β₁ rain', 'HAC s.e.', 'p (β₁)', 'β₂ momentum', 'p (β₂)', 'R²'], hac,
      { widths: [1.1, 0.6, 0.8, 0.8, 0.7, 1.0, 0.7, 0.6], size: 18, source: 'Author’s analysis; Newey–West standard errors with 7 lags.' }),
    ...figure('report/fig_4_13_monsoon_hac.png', 'Rainfall-anomaly coefficients with 95% HAC intervals, and price-momentum coefficients', { source: 'Author’s analysis.' }),
    P('**Interpretation.** No rainfall-anomaly coefficient is significant: p-values range from 0.262 (Tomato) to 0.921 (Potato), and every 95% interval spans zero. **H2 is not supported.** This is not evidence that weather does not matter. The weather record covers only two monsoon seasons, rainfall is measured in Chennai rather than in the producing districts that supply Koyambedu, and arrival volumes, the channel through which weather would act according to Roy et al. (2024), were unavailable.'),
    P('By contrast, **prior seven-day momentum is negative and significant for all eight series** (coefficients −0.09 to −0.39, all p < 0.03): a price that has risen over the past week tends to fall back over the next week, and vice versa. This short-run mean reversion is the same property detected by the ADF tests in Section 4.4. It is a genuine and usable finding for buyers: after a sharp weekly rise, waiting has on average been rewarded, except during sustained supply shocks of the kind examined in Section 4.14. The low R² values (0.01–0.15) show that most weekly variation remains unexplained.'),
    H3('4.11.2 SHAP ranking of the Northeast Monsoon deviation index'),
    P('As the proposal specified, a seven-day XGBoost model was fitted to each Koyambedu series with sixteen features: ten price features (prices at the origin and earlier, rolling means and spread, momentum and season of the target date) and six weather features (7- and 30-day rainfall, maximum temperature, a seven-day rainfall anomaly, the Northeast Monsoon deviation index and a season flag), using January 2024 to September 2026, the period covered by the weather record. Market arrival volume could not be included. Table 4.14 ranks the features by share of mean absolute SHAP value.'),
    ...table('SHAP ranking of the Northeast Monsoon deviation index against price features (Koyambedu, 7-day XGBoost)', ['Series', 'Price at origin: share', 'NE Monsoon deviation: rank', 'NE Monsoon deviation: share', 'Rainfall anomaly: rank', 'All six weather features: share'], pr,
      { widths: [1.0, 1.0, 1.1, 1.1, 1.0, 1.2], size: 17, source: 'Author’s analysis; 975 daily observations per series.' }),
    ...figure('report/fig_pa_shap_beeswarm_tomato.png', 'Tomato: SHAP beeswarm for the Koyambedu 7-day XGBoost model', { source: 'Author’s analysis.' }),
    ...figure('report/fig_pa_shap_dependence_tomato.png', 'Tomato: SHAP dependence plots for the top three features', { source: 'Author’s analysis.' }),
    P('**Interpretation.** The price at the forecast origin is the strongest feature for **all eight** vegetables, accounting for 23–51% of attribution. The Northeast Monsoon deviation index ranks between 12th and 15th of 16 features and contributes at most 1.7%; all six weather features together contribute 6–20%. For Tomato (Figures 4.13 and 4.14) the top three features are the price at the origin (42.1%), the seven-day mean price (13.8%) and the season of the target date (11.3%), and their dependence plots show a near-linear persistence effect and a seasonal step. Consistent with the regression test, the SHAP ranking places monsoon deviation well behind price history, answering the proposal’s question of which predictor is strongest.'),
    H3('4.11.3 Delta-accuracy test: does weather context improve the forecast?'),
    P('The proposal’s AgriSight evaluation asked whether adding real-time context to XGBoost measurably improves accuracy on a six-month held-out period. Historical policy news is not archived, so the context tested is the weather information that the live pipeline supplies, observed up to each forecast date. At 27 weekly origins from April to September 2026, two XGBoost models were trained on data available at each origin, one with the ten price features and one with the six weather features added, and scored at 7, 14 and 30 days (protocol C1).'),
    ...table('Delta-accuracy test: WAPE (%) on the six-month holdout, Koyambedu, 8 series', ['Horizon', 'Forecasts', 'Naive', 'XGBoost (prices)', 'XGBoost + weather', 'Gain from weather (pts)', 'DM p: weather vs prices', 'DM p: weather vs naive'], dl,
      { widths: [0.8, 0.8, 0.7, 0.9, 0.9, 0.9, 0.9, 0.9], size: 16, source: 'Author’s analysis (protocol C1). DM = Diebold–Mariano test on absolute errors with HAC standard errors.' }),
    ...figure('report/fig_pa_delta_accuracy.png', 'Delta-accuracy test: naive, XGBoost on prices, and XGBoost with weather context', { source: 'Author’s analysis.' }),
    P('**Interpretation.** Weather context made no significant difference at any horizon. At 7 and 14 days the two XGBoost models are practically identical (DM p = 0.166 and 0.981). At 30 days weather lowers WAPE by 1.77 points, from 20.49% to 18.72%, but the difference is not significant (p = 0.101). The naive forecast remains the most accurate at every horizon and is significantly better than the context-enriched model at 7 and 14 days (p = 0.011 and 0.026). The proposal’s question therefore receives a clear answer: on this evidence, real-time weather context does not add measurable forecast value, although the 30-day result suggests a possible small benefit that a longer weather record could confirm or rule out.'),

    H2('4.12 Multi-Agent Decision Layer Outputs'),
    H3('4.12.1 Deterministic agent pipeline'),
    ...table('AgriSight agent recommendations at the last statewide date (20 April 2026, ₹/quintal)', ['Commodity', 'Current', '7-day', '14-day', 'Change', 'Risk score', 'Risk', 'Action', 'Signal'], ag,
      { widths: [1.0, 0.8, 0.8, 0.8, 0.8, 0.7, 0.8, 1.5, 0.7], size: 16, source: 'Author’s analysis.' }),
    P('**Interpretation.** Seven commodities receive HOLD and Tomato receives DELAY PROCUREMENT with a HIGH risk score of 56.1. The run also exposes three design weaknesses in this pipeline that matter for interpreting its advice. (i) **The 7-day and 14-day forecasts are identical for every commodity**, because the pipeline reuses the latest row’s price features and changes only calendar fields, so the “14-day forecast” is not a 14-day forecast. (ii) **The action and signal disagree for Tomato**: the action says DELAY while the signal field says BUY, because the signal is defined from the buyer’s viewpoint of a falling price while the action uses procurement wording; a single vocabulary is needed. (iii) The field labelled “estimated savings per quintal” is |forecast change| × current price, which is not a saving.'),
    ...figure('report/fig_4_15_risk_matrix.png', 'Market Intelligence agent risk matrix (colour = risk level; size = forecast change)', { width: .85, source: 'Author’s analysis.' }),
    H3('4.12.2 Four-role pipeline with freshness gate'),
    ...table('AgriSight four-role brief, offline run (₹/quintal)', ['Commodity', 'Current', '7-day', '14-day', 'Change', 'Signal'], br,
      { widths: [1.1, 0.9, 0.9, 0.9, 0.9, 1.9], size: 18, source: 'Author’s analysis.' }),
    P('The four-role pipeline corrects the first weakness by forecasting recursively day by day, so its 7- and 14-day values differ (for example, Tomato falls from ₹2,750 to ₹2,602 at 7 days and ₹2,467 at 14 days). Because the latest statewide price is from 20 April 2026, 181 days before the run, the freshness gate correctly marks **every** commodity ABSTAIN_STALE_DATA instead of issuing advice on stale data.'),
    H3('4.12.3 Live context and local language-model writer'),
    P('The four-role pipeline has two optional components. A **live mode** adds a seven-day Chennai weather forecast (Open-Meteo) and official agriculture news from the Press Information Bureau RSS feed to the buyer brief; the forecast is summarised as total rainfall, wettest day, number of rainy days and maximum temperature, and news items are filtered for agriculture and price relevance. A **language-model writer** rewrites the brief in plain prose using a model running on the buyer’s own computer. Two safeguards are built into the writer: it may only use a model on the buyer’s own computer, never an external service, and its rewrite is accepted only if every price, forecast, percentage change and weather figure in the original brief is reproduced exactly and no new figure appears; otherwise the unedited brief is used. If a weather or news service is unavailable, the pipeline records this in the brief and still delivers the price forecasts. Both components are implemented; their run against the live services is pending and is listed as a limitation in Section 5.5. Even when they are run, all signals will remain ABSTAIN_STALE_DATA until the statewide price data are refreshed, because weather and news do not update prices.'),
    H3('4.12.4 Dashboard'),
    P('The Streamlit dashboard presents the outputs on nine pages: Agent Recommendations, Price Forecast, Model Trust, Price Movers, Market Trends and Seasonality, SHAP Explainability, Research and Scenario Validation, Dataset Snapshot and Data Quality. All nine pages were tested automatically and render without errors. Figures 4.17 and 4.18 show two pages; further screenshots are in Appendix 5.'),
    ...figure('dashboard/dash_recommendations.png', 'Dashboard: Agent Recommendations page', { width: .95, source: 'Screenshot of the AgriSight dashboard.' }),
    ...figure('dashboard/dash_research.png', 'Dashboard: Koyambedu Research and Procurement Backtest page', { width: .95, source: 'Screenshot of the AgriSight dashboard.' }),

    H2('4.13 Procurement Advice Backtest'),
    ...table('Procurement backtest: counterfactual result versus buying immediately (₹ per 100 kg lot)', ['Advice action', 'Cases', 'Mean difference', 'Median difference'], bt,
      { widths: [2.2, 0.8, 1.4, 1.4], source: 'Author’s analysis. Positive = advice cheaper than buying at the origin.' }),
    ...figure('report/fig_4_14_backtest.png', 'Mean counterfactual result by advice action', { source: 'Author’s analysis.' }),
    P(`**Interpretation.** Across 56 cases the advice was cheaper than buying immediately in **${F.bt.pos}%** of cases, more expensive in ${F.bt.neg}%, and identical in the remaining 50% (PROCURE NOW and HOLD buy at the origin by definition). The mean result is ₹${n2(F.bt.mean)} per 100 kg lot. Almost all of the gain comes from 14 DELAY decisions (mean ₹278.57, median ₹100), while HEDGE and PARTIAL PROCUREMENT were slightly loss-making. This is consistent with the mean reversion found in Section 4.11: delaying after a forecast fall has usually paid. However, the cases are not independent (they share origins), the lot convention evaluates DELAY at day 14 although the advice text says “reassess in 7 days”, and handling costs are excluded.`),
    P('A robustness check exposed a further weakness. Rerunning the identical pipeline with different library versions changed the stored XGBoost forecasts slightly, and **8 of the 56 actions (14%) changed category**: for example, Cabbage on 1 October 2025 moved from DELAY (−5.05% forecast change) to HEDGE (−3.66%). The headline rate moved from 28.6% to 30.4%. Hard ±3% and ±5% thresholds applied to forecasts whose typical error is 10–15% make the advice unstable. Thresholds should be expressed relative to forecast uncertainty.'),

    H2('4.14 Case Study: The 2023 Tomato Price Episode (Objective S04)'),
    P('The rules were applied at 13 weekly origins from 1 April to 24 June 2023, before and at the start of the episode, with a 14-day XGBoost model retrained at each origin on data up to that date.'),
    ...table('Tomato 2023 retrospective scenario: advice at weekly origins (₹/kg; one-unit purchase)', ['Origin', 'Price at origin', 'Forecast day 14', 'Actual day 14', 'Action', 'Risk', 'Result vs buy-now'], cr,
      { widths: [1.1, 0.9, 0.9, 0.9, 1.7, 0.8, 1.0], size: 17, source: 'Author’s analysis. Negative = advice more expensive than buying at the origin.' }),
    ...figure('report/fig_4_11_tomato_2023.png', 'Tomato 2023: rule-based advice at weekly origins against observed Koyambedu prices', { source: 'Author’s analysis.' }),
    P(`**Interpretation.** This is the most consequential finding for procurement. From April to May, when prices were low, the advice made only small differences (between −₹7 and +₹11/kg per decision, mostly ±₹1.50). As the shock began, the model forecast **falling** prices on 10, 17 and 24 June 2023 (₹24.59, ₹29.85 and ₹43.84 against origin prices of ₹27, ₹38 and ₹70) and advised DELAY three weeks in a row. Actual day-14 prices were ₹70, ₹80 and ₹97/kg, so the delays cost ₹43, ₹42 and ₹27/kg relative to buying immediately. Over the 13 origins the cumulative result is **−₹${Math.abs(crTot).toFixed(0)}/kg** for a one-kilogram-per-week buyer: the advice would have increased cost.`),
    P('The mechanism is clear. Models trained on mean-reverting history forecast reversion after a rise, and that is usually correct (Section 4.11). In a sustained supply shock it is exactly wrong. The 14-day model did not anticipate the shock; Section 4.14.1 shows that the 30-day horizon specified in the proposal behaved differently.'),
    H3('4.14.1 The 30-day forecast specified in the proposal'),
    P('The proposal asked for the economic value of the **30-day** forecast in the three months before July 2023. The scenario was therefore rerun with a 30-day direct XGBoost model at the same 13 weekly origins (protocol C2), together with a 14-day model on the same feature set for comparison.'),
    ...table('Tomato 2023: advice from 30-day forecasts at weekly origins (₹/kg)', ['Origin', 'Price', 'Forecast day 30', 'Actual day 30', 'Forecast change', 'Risk', 'Action', 'Result vs buy-now'], c30,
      { widths: [1.0, 0.7, 0.9, 0.9, 0.9, 0.8, 1.6, 0.9], size: 16, source: 'Author’s analysis (protocol C2). Negative = advice more expensive than buying at the origin.' }),
    ...figure('report/fig_pa_tomato_30day.png', 'Tomato 2023: advice from 30-day forecasts at weekly origins', { source: 'Author’s analysis.' }),
    ...table('Economic value of the forecast signal in the three months before July 2023 (₹/kg, one unit per signal)', ['Horizon', 'Rise signals correct', 'Forward-buying value', 'Fall signals correct', 'Deferral value', 'Net signal value', 'Rules as designed', 'Direction-only rule'], pv,
      { widths: [0.8, 0.9, 1.0, 0.9, 0.9, 0.9, 0.9, 0.9], size: 16, source: 'Author’s analysis. Forward-buying value = price at the target date minus price at the origin when a rise above 5% is forecast; deferral value = price at the origin minus price at the target date when a fall below −5% is forecast. Rule results are relative to buying immediately.' }),
    P('**Interpretation.** The 30-day forecast **did carry an early warning**. From 29 April 2023 it forecast rises of more than 100%, two months before the crisis, and 7 of its 9 rise signals were correct. A buyer who used each rise signal to lock in the next month’s price, for example through a supplier contract (tomatoes cannot be stored for 30 days), would have avoided about ₹259/kg of cost over the period; net of the two wrong late-June fall signals, the signal was worth about **₹170/kg**. The 14-day signal had no net value (−₹27/kg). The model learned the seasonal mid-year rise from the 2022 history, which explains why the longer horizon saw it.'),
    P('The decision rules, however, destroyed this value. Because the risk score adds 1.2 × the forecast change, every large forecast rise produced a HIGH risk rating, and the rules then chose PARTIAL PROCUREMENT instead of PROCURE NOW; two late-June fall forecasts then triggered DELAY just before the peak. The result was −₹219/kg relative to buying immediately. A rule that simply bought on any forecast rise and deferred only on a forecast fall would have reduced the loss to −₹89/kg. **Objective S04 is therefore answered with a qualified result**: the 30-day forecast had economic value as an early-warning signal in this episode, but the rule design turned it into a loss. The decision layer must separate forecast direction from risk and add a shock override (for example, never delay when price has risen for two consecutive weeks). This is one episode, and forward-contract costs are not included, so the value is indicative rather than a savings estimate.'),

    H2('4.15 Summary of Hypothesis Testing'),
    ...table('Results of hypothesis testing', ['Hypothesis', 'Evidence', 'Result'], [
      ['H1: RF or XGBoost has lower walk-forward error than SARIMA', 'Statewide: SARIMA 7-day WF 10.46% vs RF 11.32% and XGBoost 13.98% (RF better for 4 of 8). Koyambedu: SARIMA WAPE 12.28% vs XGBoost 15.36% and RF 16.63%', 'Not supported'],
      ['H2: NE Monsoon rainfall anomaly significantly predicts price movement', 'No β₁ significant (p = 0.262–0.921); SHAP rank of the NE Monsoon deviation index 12th–15th of 16; weather context gives no significant gain (DM p = 0.10–0.98)', 'Not supported (short weather record)'],
      ['H0: No model beats the last observed price', 'Statewide naive 4.20% vs best model 11.32%; Koyambedu naive WAPE 11.88% lowest; B2 naive lowest at all horizons', 'Not rejected'],
    ], { widths: [2.2, 3.4, 1.3], size: 18, align: [L, L, L], source: 'Sections 4.5–4.11.' }),

    H2('4.16 Status of Study Objectives'),
    ...table('Objective-by-objective status', ['Objective', 'What was done', 'Status'], [
      ['S01 Model comparison at 7/14/30 days', 'Protocols B1 (7 origins) and B2 (4 origins) on Koyambedu with naive benchmarks; statewide holdout plus horizon check', 'Achieved; result negative for complex models'],
      ['S02 NE Monsoon significance', 'HAC regressions for 8 series; SHAP ranking of the NE Monsoon deviation index with beeswarm and dependence plots', 'Achieved; effect not detected'],
      ['S03 Four-agent AgriSight pipeline', 'Deterministic agent pipeline and four-role pipeline with freshness gate; nine-page dashboard; live news, weather and local language-model writer implemented', 'Achieved as prototype; live run pending'],
      ['S04 2023 tomato procurement case', '13-origin scenario with the 30-day forecast specified in the proposal, and a 14-day comparison', 'Achieved; 30-day signal worth ₹170/kg net, but the rules turned it into a ₹219/kg loss'],
      ['Deliverable: delta-accuracy test', 'XGBoost with vs without weather context, six-month holdout, DM tests', 'Achieved; no significant gain'],
      ['Primary: useful procurement decision support', 'Backtest: 30.4% of cases better than buy-now; unstable thresholds; no shock override', 'Not yet established'],
    ], { widths: [1.9, 3.3, 1.6], size: 18, align: [L, L, L], source: 'Chapter 4.' }),
  ];
}
module.exports = { ch4 };
