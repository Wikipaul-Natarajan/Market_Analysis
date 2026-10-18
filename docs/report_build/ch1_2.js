const { d, P, C, blank, chapter, H1u, H2, H3, bullets, numbered, table, FONT } = require('./lib');
const { Paragraph, TextRun, AlignmentType, Table, TableRow, TableCell, WidthType, BorderStyle } = d;

const big = (t, size, bold = true, after = 120) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after, line: 300 },
  children: [new TextRun({ text: t, bold, font: FONT, size })] });

function titlePage() {
  return [
    big('ANNA UNIVERSITY', 32), big('CENTRE FOR DISTANCE AND ONLINE EDUCATION', 26), big('ONLINE MBA – BUSINESS ANALYTICS', 24, true, 600),
    big('A STUDY ON SHORT-TERM VEGETABLE PRICE FORECASTING IN TAMIL NADU: A MACHINE LEARNING AND MULTI-AGENT AI APPROACH FOR SUPPLY CHAIN DECISION-MAKING', 28, true, 240),
    big('A Secondary-Data Study of Statewide Agmarknet Prices and the Koyambedu Market Price Series', 24, false, 600),
    big('PROJECT REPORT', 26, true, 240),
    big('Submitted in partial fulfilment of the requirements for the award of the degree of', 22, false, 120),
    big('MASTER OF BUSINESS ADMINISTRATION', 26, true, 600),
    big('Submitted by', 22, false, 80), big('VIGNESH NATARAJAN', 26),
    big('Roll No. 24060BA0046  |  Registration No. 69124100162', 22, false, 600),
    big('BATCH CY24  |  2026', 24),
  ];
}

const sigTable = (rows) => new Table({ width: { size: 8448, type: WidthType.DXA }, columnWidths: [4224, 4224],
  borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE }, insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
  rows: rows.map(r => new TableRow({ children: r.map(t => new TableCell({ width: { size: 4224, type: WidthType.DXA },
    borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
    children: [new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: t, font: FONT, size: 24, bold: /Guide|Head|Examiner/.test(t) && !/:/.test(t) })] })] })) })) });

function bonafide() {
  return [H1u('Bonafide Certificate'),
    P('This is to certify that the project report entitled “A Study on Short-Term Vegetable Price Forecasting in Tamil Nadu: A Machine Learning and Multi-Agent AI Approach for Supply Chain Decision-Making” is a bonafide record of the project work carried out by **Vignesh Natarajan** (Roll No. 24060BA0046; Registration No. 69124100162), in partial fulfilment of the requirements for the award of the degree of Master of Business Administration (Business Analytics) of Anna University, Centre for Distance and Online Education.'),
    P('The project was completed under my guidance during the academic year 2025–2026. To the best of my knowledge, the work has not been submitted for the award of any other degree or diploma.'),
    ...blank(2),
    sigTable([['Project Guide', 'Head of Department / Programme Coordinator'], ['Name: ____________________', 'Name: ____________________'], ['Signature: ________________', 'Signature: ________________'], ['Date: _____________________', 'Seal:']]),
    ...blank(1),
    P('Submitted for the University project viva voce examination held on ________________ at ________________.'),
    ...blank(1),
    sigTable([['Internal Examiner', 'External Examiner'], ['Name: ____________________', 'Name: ____________________'], ['Signature: ________________', 'Signature: ________________']]),
  ];
}

function declaration() {
  return [H1u('Declaration'),
    P('I, **Vignesh Natarajan** (Roll No. 24060BA0046; Registration No. 69124100162), hereby declare that the project report entitled “A Study on Short-Term Vegetable Price Forecasting in Tamil Nadu: A Machine Learning and Multi-Agent AI Approach for Supply Chain Decision-Making”, submitted in partial fulfilment of the requirements for the degree of Master of Business Administration (Business Analytics), Anna University, Centre for Distance and Online Education, is a record of original work carried out by me under the guidance of my project guide.'),
    P('I further declare that the analysis is based on publicly available secondary data and on software written for this project; that all sources used have been acknowledged in the references; that the results reported are those produced by the code and data identified in Appendix D; and that this report has not been submitted, in whole or in part, for any other degree, diploma or similar title.'),
    ...blank(3),
    sigTable([['Place: Chennai', 'Signature of the Candidate'], ['Date: ________________', '(VIGNESH NATARAJAN)']]),
  ];
}

function acknowledgement() {
  return [H1u('Acknowledgement'),
    P('This project was carried out as part of the Online MBA (Business Analytics) programme, and I thank Anna University and its Centre for Distance and Online Education for making it possible.'),
    P('I am grateful to my project guide for academic direction, for the questions raised at the first and second reviews, and for constructive feedback that shaped the evaluation design of this study. I thank the faculty of the programme for the grounding in statistics, analytics and supply chain management on which this work draws.'),
    P('I acknowledge the maintainers of the public data sources used: the Agricultural Marketing Information Network (Agmarknet) of the Directorate of Marketing and Inspection, the Kaggle contributor who compiled the daily commodity price dataset, the Vegetable Market Price website for the Koyambedu history series attributed to the Koyambedu Vegetable Merchants’ Council, and Open-Meteo for historical weather data. I also acknowledge the open-source communities behind Python, pandas, statsmodels, Prophet, scikit-learn, XGBoost, SHAP and Streamlit.'),
    P('My family and colleagues supported me with patience and encouragement throughout, and I am grateful to them. Any errors of analysis or interpretation that remain are my own.'),
  ];
}

function abstract() {
  return [H1u('Abstract'),
    P('Vegetable prices in India are volatile because supply is seasonal, perishable and weather-sensitive. For an institutional buyer, the cost of a poorly timed purchase is direct. This study asks whether short-term price forecasts, and a rule-based multi-agent decision layer built on them, can support procurement timing for eight vegetables in Tamil Nadu: Tomato, Onion, Potato, Cabbage, Carrot, Beans, Brinjal and Drumstick.'),
    P('Two secondary datasets were analysed separately. The first is a Kaggle-hosted Agmarknet extract of 414,388 market-level records from 451 Tamil Nadu markets (24 January 2024 to 20 April 2026), aggregated to a daily statewide median. The second is a Koyambedu history-page series of 14,472 daily ₹/kg observations (4 November 2021 to 17 October 2026) attributed to the Koyambedu Vegetable Merchants’ Council. SARIMA, Prophet, Random Forest and XGBoost were compared with naive baselines under chronological validation; SHAP was used for interpretation; HAC regressions tested a Northeast Monsoon rainfall effect; and the procurement rules were backtested.'),
    P('The central finding is that simple baselines were not beaten. On the statewide 90-day holdout, Random Forest recorded 11.32% mean MAPE and XGBoost 13.98%, but yesterday’s price alone gave 4.20%; a strictly seven-day-ahead XGBoost gave 27.09%. On Koyambedu data across seven origins and 7-, 14- and 30-day horizons, the last observed price had the lowest WAPE (11.88%), followed by SARIMA (12.28%), while XGBoost (15.36%), Random Forest (16.63%) and Prophet (23.82%) were worse. No rainfall-anomaly coefficient was significant (p = 0.26–0.92), whereas prior seven-day momentum was significantly negative for all eight vegetables, indicating short-run mean reversion. The procurement rules beat an immediate purchase in only 30.4% of 56 backtest cases, and during the 2023 tomato episode they advised delay on 10, 17 and 24 June, just before prices rose from ₹27 to ₹97/kg.'),
    P('All four objectives were tested and answered. The study contributes a reproducible end-to-end pipeline with a nine-page dashboard; a horizon-sensitivity check that exposes next-day persistence masquerading as forecast skill; evidence of short-run mean reversion; a documented failure case for automated advice during a supply shock; and safeguards designed to stop a local AI writer from altering prices. For these series and horizons, naive benchmarks should be the procurement baseline, and the decision rules require a supply-shock override, uncertainty-scaled thresholds and a buyer pilot before operational use. No realized savings are claimed.'),
    P('**Keywords:** vegetable price forecasting; procurement; Agmarknet; Koyambedu; SARIMA; XGBoost; SHAP; naive benchmark; multi-agent decision support; Tamil Nadu'),
  ];
}

function abbreviations() {
  const rows = [['ADF', 'Augmented Dickey–Fuller (unit-root test)'], ['AIC', 'Akaike Information Criterion'], ['API', 'Application Programming Interface'],
    ['APMC', 'Agricultural Produce Market Committee'], ['CV', 'Coefficient of Variation'], ['EDA', 'Exploratory Data Analysis'], ['EMA', 'Exponential Moving Average'],
    ['HAC', 'Heteroskedasticity and Autocorrelation Consistent (standard errors)'], ['LLM', 'Large Language Model'], ['MAE', 'Mean Absolute Error'],
    ['MAPE', 'Mean Absolute Percentage Error'], ['NE / SW monsoon', 'Northeast / Southwest monsoon'], ['OLS', 'Ordinary Least Squares'], ['PIB', 'Press Information Bureau'],
    ['RF', 'Random Forest'], ['RMSE', 'Root Mean Squared Error'], ['SARIMA', 'Seasonal Autoregressive Integrated Moving Average'], ['SHAP', 'SHapley Additive exPlanations'],
    ['sMAPE', 'Symmetric Mean Absolute Percentage Error'], ['TN', 'Tamil Nadu'], ['TOP', 'Tomato, Onion and Potato'], ['WAPE', 'Weighted Absolute Percentage Error'],
    ['WF', 'Walk-forward (rolling-origin) evaluation'], ['XGBoost', 'Extreme Gradient Boosting']];
  return [H1u('List of Abbreviations'), ...table('Abbreviations used in this report', ['Abbreviation', 'Meaning'], rows, { widths: [1.2, 3], label: 'i' }).slice(1)];
}

function ch1() {
  const obj = numbered([
    '**S01 – Model comparison.** Measure how accurately SARIMA, Prophet, Random Forest and XGBoost forecast prices 7, 14 and 30 days ahead, judged mainly by RMSE and secondarily by MAPE, and set these results against naive benchmarks.',
    '**S02 – Monsoon effect.** Determine whether departures of Northeast Monsoon rainfall from normal help to explain short-term vegetable price changes at a statistically significant level.',
    '**S03 – AgriSight pipeline.** Build a four-agent pipeline that integrates data collection, price forecasting, market intelligence and procurement advice into a buyer-facing brief and dashboard.',
    '**S04 – Procurement case study.** Estimate the potential procurement cost effect of forecast-informed timing using the July–August 2023 tomato price episode as a retrospective case.']);
  const rq = numbered([
    'What coverage, quality and price behaviour do the statewide and Koyambedu data show for the eight vegetables?',
    'Do SARIMA, Prophet, Random Forest and XGBoost forecast more accurately than naive benchmarks at 7-, 14- and 30-day horizons?',
    'Which inputs contribute most to fitted machine-learning predictions, and what do those contributions imply about forecast skill?',
    'Is Northeast Monsoon rainfall anomaly associated with subsequent seven-day price returns after controlling for recent price momentum?',
    'Would the rule-based procurement advice have reduced purchase cost relative to buying immediately, in routine periods and during the 2023 tomato episode?']);
  return [
    ...chapter(1, 'Introduction'),
    H2('1.1 Background of the Study'),
    P('Vegetables are a large and volatile component of household and institutional food spending in India. Tomato, onion and potato carry only a small share of the CPI basket, yet they account for an outsized part of the swings in food and overall inflation. Their crop cycles are short, they spoil quickly, their cultivation is concentrated in a few regions, and their output depends heavily on the weather (Roy et al., 2024). In July 2023, consumers across India paid on average about ₹109.5 for a kilogram of tomatoes, and the tomato component of the CPI was more than three times its level a year earlier (Roy et al., 2024). Episodes of this kind are not isolated: onion and potato have shown similar boom-and-bust cycles in alternate years.'),
    P('For buyers who procure vegetables regularly, such as hotels, institutional kitchens, hospital and hostel caterers, food processors and retail chains, the question is practical: should a purchase be made now, deferred, or split? A modest improvement in timing, applied across a large and recurring purchase volume, could matter financially. Data-driven forecasting appears to offer that improvement, and recent advances in machine learning and AI agents have made sophisticated forecasting pipelines easy to build.'),
    P('This project, named **AgriSight**, builds such a pipeline for eight vegetables traded in Tamil Nadu and evaluates it critically. The emphasis of the final study is not only on whether a model can be fitted, but on whether its forecasts beat the simplest credible alternatives and whether the resulting procurement advice would actually have helped a buyer.'),
    H2('1.2 Industry Profile'),
    H3('1.2.1 Vegetable marketing in India'),
    P('Most vegetables in India move from farmers to consumers through regulated wholesale markets administered by state Agricultural Produce Market Committees (APMCs), with traders, commission agents, wholesalers and retailers in between. Value-chain studies estimate that farmers receive only about one-third of the consumer rupee for tomato, onion and potato, with the remainder apportioned along the chain (Roy et al., 2024). Prices are discovered daily through auctions and negotiation, and the Directorate of Marketing and Inspection publishes reported market prices through the Agricultural Marketing Information Network (Agmarknet).'),
    H3('1.2.2 Tamil Nadu markets and the Koyambedu complex'),
    P('Tamil Nadu has two distinct channels that appear in the data used here. The first is the network of regulated markets and Uzhavar Sandhai (farmers’ markets), the latter established by the Government of Tamil Nadu so that farmers can sell directly to consumers. In the statewide extract used in this study, Uzhavar Sandhai account for 90.7 per cent of all records, which is important for interpretation because their prices are closer to retail than to bulk wholesale. The second is the Koyambedu Wholesale Market Complex in Chennai, one of the largest wholesale markets for perishables in South India and the reference market for buyers in the Chennai region. Its daily prices are published by the Koyambedu Vegetable Merchants’ Council and redistributed by public websites.'),
    H3('1.2.3 Who uses short-term price forecasts'),
    P('The intended users of this study are procurement managers who buy in recurring cycles and can shift purchases by days or weeks: institutional caterers, hotel and restaurant groups, food processors, retail chains and aggregators. Their decision variables are timing, quantity and supplier; their constraints are shelf life, storage, cash flow and service level. A forecast is useful to them only if it improves on what they already know, which at minimum is today’s price.'),
    H2('1.3 Statement of the Problem'),
    P('Buyers have to decide when to purchase without knowing which way prices will move over the coming days and weeks. Machine-learning forecasts and AI-agent pipelines promise better information, but agricultural price series are short, noisy and subject to sudden supply shocks, and published forecast accuracy figures are often not compared with naive benchmarks or are computed in ways that leak future information. The problem addressed is therefore twofold: (a) to determine whether statistical and machine-learning models forecast Tamil Nadu vegetable prices better than naive benchmarks at procurement-relevant horizons; and (b) to determine whether a transparent rule-based decision layer built on those forecasts would have improved purchase outcomes.'),
    H2('1.4 Objectives of the Study'),
    P('**Primary objective.** To predict near-term vegetable prices in Tamil Nadu with four model families (SARIMA, Prophet, Random Forest and XGBoost) and to assess whether AgriSight, a four-agent pipeline that turns these forecasts into advice, gives procurement buyers useful decision support.'),
    P('**Secondary objectives.** The four secondary objectives approved at the first review are retained without change:'),
    ...obj.paras,
    H2('1.5 Research Questions and Hypotheses'),
    ...rq.paras,
    P('Two hypotheses were stated in the second review:'),
    ...bullets(['**H1:** Random Forest or XGBoost achieves lower walk-forward forecast error than SARIMA.',
      '**H2:** Abnormal Northeast Monsoon rainfall has a statistically significant effect on subsequent vegetable price changes.']),
    P('In the course of the study a third, implicit hypothesis became central and is tested explicitly: **H0 (benchmark):** none of the fitted models outperforms the last observed price at the evaluated horizons.'),
    H2('1.6 Scope of the Study'),
    bullets([
      '**Commodities:** Tomato, Onion, Potato, Cabbage, Carrot, Beans, Brinjal and Drumstick.',
      '**Geography:** Tamil Nadu statewide (451 markets, 36 districts) and, separately, the Koyambedu market in Chennai.',
      '**Period:** statewide prices from 24 January 2024 to 20 April 2026; Koyambedu prices from 4 November 2021 to 17 October 2026; Chennai weather from 1 January 2024 to 30 September 2026.',
      '**Horizons:** next-day (statewide holdout), and 7, 14 and 30 days (Koyambedu common-origin evaluation).',
      '**Decision layer:** deterministic, rule-based agents; an optional local language model and live news feed were implemented but not exercised in the reported runs.']).flat(),
    H2('1.7 Significance of the Study'),
    P('For practitioners, the study shows how to test a forecasting tool before trusting it, and identifies the benchmark a vendor or in-house model must beat. For the academic programme, it demonstrates a full analytics life cycle on real data: acquisition, cleaning, feature engineering, modelling, explanation, decision rules, backtesting and a deployable dashboard. Its methodological contribution is a horizon-sensitivity check that exposes how next-day information can make a model look far more accurate than it is at the horizon a buyer needs. Because the study reports results whether or not they support the original hypotheses, its negative findings are as informative as its positive ones: they tell buyers which tools not to rely on and which information to acquire instead.'),
    H2('1.8 Limitations of the Study (Summary)'),
    P('The data are secondary and their upstream collection was not audited. The statewide series mixes farmers’ markets and wholesale markets and contains a small number of apparent unit errors. The Koyambedu series does not state whether quotes are wholesale or retail. The weather record spans just two full monsoon seasons, and market-arrival volumes could not be obtained. Procurement results are counterfactual, not realized savings. These limitations are discussed in full in Section 5.5.'),
    H2('1.9 Chapter Scheme'),
    P('**Chapter 1** introduces the problem, industry context, objectives and scope. **Chapter 2** reviews the literature on vegetable price volatility, forecasting methods, forecast evaluation, explainability, AI agents and procurement decisions, and identifies the research gap. **Chapter 3** describes the research design, data, variables, models, evaluation protocols, statistical tools and decision rules. **Chapter 4** presents the analysis and interpretation. **Chapter 5** summarises findings, offers suggestions, discusses limitations and concludes. Appendices document the data dictionary, model settings, reproducibility record, code corrections and the dashboard.'),
  ];
}

function ch2() {
  const gap = [
    ['Roy et al. (2024)', 'All-India TOP, monthly CPI', 'ARDL, SARIMA-X', 'Supply balance-sheet variables improve monthly inflation forecasts', 'Monthly CPI; not daily market prices'],
    ['Padhi et al. (2023)', 'All-India TOP, daily 2011–2021', 'BEKK/DCC GARCH', 'Tomato volatility spills over to onion and potato', 'Volatility, not point forecasts'],
    ['Ajmal et al. (2024)', 'Selected states, monthly 2005–2021', 'Seasonal index, CDVI, ARCH-GARCH', 'Onion most volatile; strong seasonality', 'Descriptive; no forecast benchmark'],
    ['Tamilselvi & Mohan Naidu (2020)', 'Koyambedu arrivals and wholesale prices', 'SARIMA', 'SARIMA fits seasonal vegetable series', 'Monthly; single model family'],
    ['Mantaw et al. (2024)', 'Tamil Nadu groundnut', 'XGBoost', 'Boosting forecasts commodity prices well', 'Different crop; no naive comparison'],
    ['Manogna et al. (2025)', 'Indian agricultural commodities', 'Deep learning', 'Deep models improve on classical methods', 'Monthly/aggregate; different scope'],
    ['Makridakis et al. (2018a)', 'M3 competition series', 'Statistical vs ML', 'ML often less accurate than simple statistical methods', 'Not agricultural'],
    ['This study', 'TN statewide + Koyambedu, daily', 'SARIMA, Prophet, RF, XGBoost, naive; SHAP; HAC; backtest', 'Naive benchmarks unbeaten; rules need recalibration', 'Secondary data; short weather window'],
  ];
  return [
    ...chapter(2, 'Review of Literature'),
    P('This chapter reviews five bodies of work relevant to the study: the economics of vegetable price volatility in India; statistical and machine-learning forecasting methods; principles of forecast evaluation; model explanation and AI agents; and procurement decision-making under price uncertainty. It closes by identifying the research gap.'),
    H2('2.1 Vegetable Price Volatility in India'),
    P('Roy et al. (2024), in a Reserve Bank of India working paper, analyse tomato, onion and potato (TOP) prices using a monthly supply–demand balance sheet. They show that availability, or the availability-to-usage ratio, is significantly and negatively related to the CPI of all three vegetables after controlling for input costs, rainfall and wages, and that SARIMA-X models including balance-sheet variables forecast TOP inflation better than univariate SARIMA over 2- to 12-month horizons. Their value-chain analysis estimates farmers’ share of the consumer rupee at roughly one-third. The implication for this study is that supply volume, which is not available in either of the datasets used here, is likely the most informative missing predictor.'),
    P('Padhi, Shekhar and Handa (2023) study daily TOP prices from 2011 to 2021 using multivariate GARCH models and show that volatility originating in tomato spills over into onion and potato in both wholesale and retail markets. For onion and tomato, shocks pass mainly in one direction, from the wholesale level to the retail level, whereas for potato they travel both ways. This supports the use of cross-commodity features in the present models and suggests that wholesale and retail series should not be treated as interchangeable.'),
    P('Ajmal et al. (2024) examine monthly wholesale TOP prices across Indian states from 2005 to 2021 using seasonal indices, the Cuddy–Della Valle instability index and ARCH-GARCH models. They find a pronounced seasonal cycle, in which tomato is typically dearest in the second half of the year, and identify onion as the most volatile of the three crops. Birthal, Negi and Joshi (2019) attribute part of onion price volatility to irregular market arrivals and trading practices rather than climatic shocks alone, and Chand (2010) identifies weather-driven supply shocks as the most important driver of Indian food inflation episodes. Together these studies establish that vegetable price movements are seasonal, shock-prone and supply-driven, which makes short-horizon forecasting difficult without supply data.'),
    H2('2.2 Studies on Tamil Nadu and Koyambedu'),
    P('Tamilselvi and Mohan Naidu (2020) model monthly vegetable arrivals and wholesale prices at Koyambedu using SARIMA and report adequate fit for seasonal series. Their study is the closest market-specific precedent but uses monthly data, so its error figures are not directly comparable with the daily horizons used here. Mantaw et al. (2024) apply XGBoost to groundnut prices in Tamil Nadu and report favourable accuracy, illustrating the regional interest in gradient boosting, though for a storable crop and without a naive benchmark.'),
    H2('2.3 Statistical Time-Series Forecasting'),
    P('The Box–Jenkins approach models a series through autoregressive, differencing and moving-average terms, with seasonal extensions for repeating cycles (Box et al., 2015). Identification relies on stationarity assessment, commonly through the Augmented Dickey–Fuller (ADF) test (Dickey & Fuller, 1979), and model selection on information criteria such as AIC followed by residual diagnostics. Hyndman and Athanasopoulos (2021) emphasise that forecasting methods should be judged on genuine out-of-sample performance and recommend simple benchmarks, namely the naive (last value), seasonal naive and drift methods, as the reference against which more complex methods must justify themselves.'),
    P('Prophet (Taylor & Letham, 2018) represents a series as a sum of piecewise-linear trend, Fourier-based yearly and weekly seasonality, and holiday effects. It is designed for business series with strong calendar effects and long histories; with fewer than two to three years of data, annual seasonality is weakly identified and trend changepoints can extrapolate poorly.'),
    H2('2.4 Machine-Learning Forecasting'),
    P('Random Forests average many decision trees grown on bootstrap samples with random feature subsets, reducing variance (Breiman, 2001). Gradient boosting builds trees sequentially to correct residual errors; XGBoost adds regularisation and efficient computation (Chen & Guestrin, 2016). Applied to time series, these methods are typically trained on engineered features such as lagged values, rolling statistics and calendar indicators, which converts forecasting into supervised regression. Manogna, Dharmaji and Sarang (2025) report improvements from deep-learning models for Indian agricultural commodity prices.'),
    P('The evidence is not one-sided. In a large comparison on M3 competition series, Makridakis, Spiliotis and Assimakopoulos (2018a) found that popular machine-learning methods were frequently less accurate than simple statistical methods and were more computationally demanding. The subsequent M4 competition (Makridakis et al., 2018b) found that pure machine-learning methods performed poorly and that the best results came from combinations and hybrids. These findings motivate the inclusion of naive and statistical benchmarks in every comparison reported in this study.'),
    H2('2.5 Forecast Evaluation and Data Leakage'),
    P('Tashman (2000) reviews out-of-sample evaluation and recommends rolling-origin designs in which the forecast origin advances through time and the model is refitted using only information available at each origin. Bergmeir and Benítez (2012) discuss when cross-validation is valid for time series and caution against random splits. Hyndman and Koehler (2006) compare accuracy measures and show that MAPE is undefined or unstable near zero and penalises over- and under-forecasts asymmetrically; they recommend scale-free alternatives. Weighted absolute percentage error (WAPE), which divides total absolute error by total actual value, is widely used in demand forecasting because it is not dominated by low-price periods. Diebold and Mariano (1995) provide a test for whether accuracy differences between two forecasts are statistically significant.'),
    P('Kaufman et al. (2012) define leakage as the introduction of information into model training or evaluation that would not be legitimately available at prediction time, and show how it produces over-optimistic results. In time-series feature engineering, a common and subtle form is a mismatch between the information horizon of the features and the decision horizon of the user: features built from yesterday’s value allow a model to score well on next-day prediction, which is not the same task as forecasting a week ahead.'),
    H2('2.6 Statistical Inference with Autocorrelated Data'),
    P('Daily price returns computed over overlapping windows are serially correlated, which makes ordinary least-squares standard errors unreliable. Newey and West (1987) propose heteroskedasticity- and autocorrelation-consistent (HAC) standard errors that remain valid under such dependence. HAC inference is used in this study for the monsoon association test.'),
    H2('2.7 Explainable Machine Learning'),
    P('SHAP (Lundberg & Lee, 2017) attributes a model’s prediction to its input features using Shapley values from cooperative game theory, with an efficient exact algorithm for tree ensembles. Molnar (2022) stresses that such attributions describe how a fitted model uses its inputs and do not establish causal effects; correlated features can share or swap attribution. In this study, SHAP is used diagnostically: a large share of attribution on yesterday’s price is evidence that a model is mainly exploiting persistence.'),
    H2('2.8 AI Agents in Analytical Workflows'),
    P('Large-language-model-based autonomous agents, systems that plan, call tools and coordinate across roles, are surveyed by Wang et al. (2024). Domain applications include agricultural reasoning with code-executing agents that ground their answers in tools and data (Zhang et al., 2026). These works motivate AgriSight’s four-role design. However, most reported systems are evaluated on task completion rather than on the economic value of their recommendations; this study evaluates AgriSight’s advice against realized prices.'),
    H2('2.9 Procurement Decisions under Price Uncertainty'),
    P('Supply chain texts frame procurement timing as a trade-off between purchase price, holding cost, perishability and service level (Chopra & Meindl, 2016; Silver, Pyke & Thomas, 2017). For perishables, the scope to buy ahead is limited by shelf life, and the value of a forecast depends on its accuracy relative to the buyer’s default, the cost of being wrong, and the buyer’s ability to act. A forecast that is right on average but wrong at turning points can be costly precisely when it matters most.'),
    H2('2.10 Research Gap'),
    P('Table 2.1 summarises the most relevant studies. Indian research on vegetable prices has concentrated on monthly CPI inflation, volatility transmission and seasonal patterns, while machine-learning studies of agricultural prices commonly report accuracy without comparison to naive benchmarks or under evaluation designs whose information horizon is unclear. Few studies evaluate the procurement consequences of forecast-based advice, and none identified for Tamil Nadu vegetables do so on daily data across matched horizons. This study addresses that gap by comparing statistical and machine-learning models with naive benchmarks at procurement-relevant horizons, by checking whether reported accuracy reflects genuine forecast skill, and by backtesting the decision rules on realized prices, including a major price shock.'),
    ...table('Summary of reviewed studies and research gap', ['Study', 'Data / setting', 'Method', 'Key finding', 'Gap relative to this study'], gap,
      { widths: [1.3, 1.4, 1.2, 1.8, 1.6], size: 17, align: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT], source: 'Compiled by the author from the cited studies.' }),
  ];
}

module.exports = { titlePage, bonafide, declaration, acknowledgement, abstract, abbreviations, ch1, ch2, obj: null };
