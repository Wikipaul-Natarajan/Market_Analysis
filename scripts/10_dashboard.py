"""Launch with: streamlit run scripts/10_dashboard.py"""
import html
import json
import pickle
import re

import pandas as pd
import streamlit as st

from agrisight_common import PROC, REPORT, MODELS, FIG

st.set_page_config(page_title='AgriSight', page_icon='🌱', layout='wide')

CSS = """
<style>
.risk-badge{display:inline-block;padding:4px 11px;border-radius:999px;font-size:.78rem;font-weight:750;letter-spacing:.03em;margin:2px}
.risk-HIGH{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5}
.risk-MEDIUM{background:#fef3c7;color:#92400e;border:1px solid #fcd34d}
.risk-LOW{background:#dcfce7;color:#166534;border:1px solid #86efac}
.cardfull-PROCURE-NOW,.cardfull-PARTIAL-PROCUREMENT,.cardfull-HEDGE,.cardfull-HOLD,.cardfull-DELAY-PROCUREMENT{border-radius:18px;padding:20px 22px;margin:10px 0;box-shadow:0 6px 20px #0f172a18;color:#172033}
.cardfull-PROCURE-NOW{background:linear-gradient(130deg,#dcfce7 0%,#bbf7d0 55%,#86efac 100%)}
.cardfull-PARTIAL-PROCUREMENT{background:linear-gradient(130deg,#fffbeb 0%,#fde68a 60%,#fcd34d 100%)}
.cardfull-HEDGE{background:linear-gradient(130deg,#eff6ff 0%,#bfdbfe 60%,#93c5fd 100%)}
.cardfull-HOLD{background:linear-gradient(130deg,#f8fafc 0%,#e2e8f0 60%,#cbd5e1 100%)}
.cardfull-DELAY-PROCUREMENT{background:linear-gradient(130deg,#fff1f2 0%,#fecdd3 60%,#fda4af 100%)}
.card-title{font-size:1.16rem;font-weight:800;margin-bottom:5px}.card-action{font-size:.78rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;opacity:.8}
.card-trigger{margin:12px 0 14px;line-height:1.5}.card-details{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px;font-size:.9rem}.card-details b{font-weight:750}
.hero-card{background:linear-gradient(145deg,#f8fafc,#eef2ff);border:1px solid #dbe3ef;border-radius:16px;padding:18px 20px;min-height:112px;box-shadow:0 4px 14px #0f172a0c}
.big{font-size:1.8rem;font-weight:850;line-height:1.2;color:#172554;margin-top:8px}.lbl{font-size:.88rem;font-weight:700;color:#475569}
.mover-card{background:#fff;border:1px solid #dbe3ef;border-radius:14px;padding:14px 16px;margin:7px 0;box-shadow:0 4px 12px #0f172a0a}
.mover-name{font-weight:800;font-size:1rem}.mover-value{font-size:1.25rem;font-weight:800;margin-top:6px}.mover-up{color:#15803d}.mover-down{color:#b91c1c}.mover-flat{color:#475569}
.health-card{border-radius:13px;padding:13px 15px;margin:6px 0;border:1px solid;min-height:78px}.health-ok{background:#f0fdf4;border-color:#86efac;color:#166534}.health-bad{background:#fff1f2;border-color:#fda4af;color:#9f1239}.health-field{font-weight:750;word-break:break-word}.health-status{font-size:.83rem;margin-top:6px;font-weight:650}
.leader-card{border:1px solid #dbe3ef;background:#fff;border-radius:16px;padding:17px 19px;margin:10px 0;box-shadow:0 5px 16px #0f172a0b}.leader-head{display:flex;justify-content:space-between;align-items:center;font-weight:800;font-size:1.08rem;margin-bottom:12px}
.mbar-row{display:grid;grid-template-columns:90px minmax(80px,1fr) 95px;align-items:center;gap:10px;margin:8px 0}.mbar-label{font-size:.82rem;font-weight:700;color:#475569}.mbar-track{height:11px;border-radius:99px;background:#edf2f7;overflow:hidden}.mbar-fill{height:100%;border-radius:99px}.mbar-val{text-align:right;font-size:.8rem;font-weight:700;color:#334155}
.section-head{font-size:1.22rem;font-weight:850;color:#172554;margin:18px 0 10px}
.forecast-flow{display:flex;align-items:center;justify-content:space-between;gap:14px;background:linear-gradient(110deg,#f8fafc,#eff6ff);border:1px solid #dbe3ef;border-radius:20px;padding:22px;margin:12px 0 18px}
.ff-block{flex:1;min-width:0;text-align:center;background:#fff;border:1px solid #e2e8f0;border-radius:15px;padding:18px 12px}.ff-label{font-size:.9rem;font-weight:750;color:#475569}.ff-value{font-size:1.65rem;font-weight:850;color:#172554;margin:8px 0}.ff-sub{font-size:.8rem;color:#64748b}
.ff-arrow{min-width:95px;text-align:center;font-size:1.8rem;font-weight:850}.ff-arrow.up{color:#15803d}.ff-arrow.down{color:#b91c1c}.ff-delta{display:block;font-size:1rem;margin-top:3px}
@media(max-width:650px){.forecast-flow{flex-direction:column}.ff-block{width:100%}.ff-arrow{transform:rotate(90deg)}.card-details{grid-template-columns:1fr}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

@st.cache_data
def parquet(path):
    return pd.read_parquet(path)

@st.cache_data
def csv(path):
    return pd.read_csv(path)

@st.cache_resource
def ml_models(path):
    with open(path, 'rb') as f:
        return pickle.load(f)

def warn(path, step):
    st.warning(f'Required artifact is missing: {path.name}. Run script {step} first.')

def load_report(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None

def safe_text(value, default=''):
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return default
    return str(value)

def humanize_feature(feature):
    """Translate model feature identifiers into readable procurement language."""
    f = safe_text(feature, 'market conditions').strip().lower()
    if not f:
        return 'market conditions'
    if f.startswith('cross_') and f.endswith('_lag1'):
        commodity = f[len('cross_'):-len('_lag1')].replace('_', ' ').title()
        return f'{commodity} price (previous day)'
    if f in {'position_52w', 'position_52_week'}:
        return 'position within the 52-week price range'
    if f in {'price_accel', 'price_acceleration'}:
        return 'price acceleration'
    if f in {'sw_monsoon', 'south_west_monsoon'}:
        return 'South-West monsoon season'
    if f in {'ne_monsoon', 'north_east_monsoon'}:
        return 'North-East monsoon season'
    names = {
        'pongal': 'Pongal period', 'tamil_new_year': 'Tamil New Year period',
        'diwali': 'Diwali period', 'navratri': 'Navratri period',
        'rain_7d_sum': 'rainfall over the past 7 days',
        'rain_30d_sum': 'rainfall over the past 30 days',
        'heat_wave': 'heat-wave conditions', 'cold_day': 'cold-day conditions',
        'market_count': 'number of reporting markets', 'temp_max': 'maximum temperature',
        'temp_min': 'minimum temperature', 'temp_avg': 'average temperature',
        'temperature_2m_max': 'maximum temperature', 'temperature_2m_min': 'minimum temperature',
        'temperature_2m_mean': 'average temperature', 'precipitation': 'daily precipitation',
        'precipitation_sum': 'daily precipitation', 'rain_sum': 'daily rainfall',
        'price_range': 'daily price range', 'month': 'calendar month',
        'week_of_year': 'week of year', 'quarter': 'calendar quarter',
        'day_of_week': 'day of week', 'year': 'calendar year',
    }
    if f in names:
        return names[f]
    patterns = (
        (r'^(?:lag)_(\d+)$', lambda m: f'price {m.group(1)} days earlier'),
        (r'^(?:rolling_mean|roll_mean)_(\d+)$', lambda m: f'{m.group(1)}-day average price'),
        (r'^(?:rolling_std|roll_std)_(\d+)$', lambda m: f'{m.group(1)}-day price variability'),
        (r'^(?:rolling_min|roll_min)_(\d+)$', lambda m: f'{m.group(1)}-day minimum price'),
        (r'^(?:rolling_max|roll_max)_(\d+)$', lambda m: f'{m.group(1)}-day maximum price'),
        (r'^ema_(\d+)$', lambda m: f'{m.group(1)}-day exponential price average'),
        (r'^(?:pct_change|momentum)_(\d+)$', lambda m: f'price change over {m.group(1)} days'),
    )
    for pattern, render in patterns:
        match = re.match(pattern, f)
        if match:
            return render(match)
    return f.replace('_', ' ')

def feature_card(label, value):
    st.markdown(
        f'<div class="hero-card"><div class="lbl">{html.escape(str(label))}</div>'
        f'<div class="big">{html.escape(str(value))}</div></div>',
        unsafe_allow_html=True,
    )

def render_health_grid(data):
    nulls = data.isna().sum()
    columns = st.columns(3)
    for i, (field, count) in enumerate(nulls.items()):
        count = int(count)
        clean = count == 0
        css = 'health-ok' if clean else 'health-bad'
        icon = '✔️ Clean' if clean else f'⚠️ {count:,} missing'
        markup = (
            f'<div class="health-card {css}"><div class="health-field">{html.escape(str(field))}</div>'
            f'<div class="health-status">{icon}</div></div>'
        )
        with columns[i % 3]:
            st.markdown(markup, unsafe_allow_html=True)

def render_price_movers(data):
    data = data.copy()
    data['arrival_date'] = pd.to_datetime(data['arrival_date'])
    latest = data['arrival_date'].max().normalize()
    daily = data.groupby(['commodity', 'arrival_date']).modal_price.median().reset_index()
    daily['arrival_date'] = daily['arrival_date'].dt.normalize()
    movers = []
    for commodity, group in daily.groupby('commodity'):
        recent = group.loc[group.arrival_date.gt(latest - pd.Timedelta(days=7)) & group.arrival_date.le(latest), 'modal_price']
        prior = group.loc[group.arrival_date.gt(latest - pd.Timedelta(days=14)) & group.arrival_date.le(latest - pd.Timedelta(days=7)), 'modal_price']
        if recent.empty:
            continue
        current = float(recent.median())
        previous = float(prior.median()) if not prior.empty else None
        change = ((current / previous) - 1) * 100 if previous else None
        movers.append((commodity, current, change, len(recent)))
    movers.sort(key=lambda item: abs(item[2]) if item[2] is not None else -1, reverse=True)
    if not movers:
        st.info('No recent daily price observations are available.')
        return
    columns = st.columns(4)
    for i, (commodity, price, change, count) in enumerate(movers):
        css = 'mover-flat' if change is None or change == 0 else ('mover-up' if change > 0 else 'mover-down')
        change_text = 'Previous-week comparison unavailable' if change is None else f'{change:+.1f}% vs prior 7 days'
        markup = (
            f'<div class="mover-card"><div class="mover-name">{html.escape(str(commodity))}</div>'
            f'<div class="mover-value">₹{price:,.0f}/quintal</div>'
            f'<div class="{css}">{change_text}</div><small>Latest {count} observed days · through {latest:%d %b %Y}</small></div>'
        )
        with columns[i % 4]:
            st.markdown(markup, unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'rec'

st.sidebar.title('AgriSight')
st.sidebar.subheader('🎯 Core Decisions')
for label, key in [('Agent Recommendations', 'rec'), ('Price Forecast', 'forecast'), ('Model Trust', 'trust')]:
    if st.sidebar.button(label, key=f'nav_{key}', use_container_width=True):
        st.session_state.page = key
with st.sidebar.expander('📊 More Insights', expanded=False):
    for label, key in [('Price Movers', 'movers'), ('Market Trends & Seasonality', 'trends'), ('SHAP Explainability', 'shap')]:
        if st.button(label, key=f'nav_{key}', use_container_width=True):
            st.session_state.page = key
with st.sidebar.expander('🛠️ Diagnostics', expanded=False):
    for label, key in [('Dataset Snapshot', 'snapshot'), ('Data Quality', 'quality')]:
        if st.button(label, key=f'nav_{key}', use_container_width=True):
            st.session_state.page = key

page = st.session_state.page
page_titles = {
    'rec': 'Agent Recommendations', 'forecast': 'Price Forecast', 'trust': 'Model Trust',
    'movers': 'Price Movers', 'trends': 'Market Trends & Seasonality',
    'shap': 'SHAP Explainability', 'snapshot': 'Dataset Snapshot', 'quality': 'Data Quality',
}
if page not in page_titles:
    page = 'rec'
    st.session_state.page = page
st.title('AgriSight | Tamil Nadu Vegetable Prices')
st.caption(page_titles.get(page, 'Agent Recommendations'))
raw = PROC / 'tn_vegetables_daily.parquet'
features = PROC / 'tn_features.parquet'

if page == 'rec':
    st.markdown('<div class="section-head">Agent Recommendations</div>', unsafe_allow_html=True)
    report_path = REPORT / 'agrisight_pipeline_report.json'
    rep = load_report(report_path)
    if not rep:
        warn(report_path, '09')
    else:
        recommendations = pd.DataFrame(rep.get('recommendations', []))
        executive = rep.get('executive_summary', {})
        high_risk = executive.get('high_risk', [])
        st.markdown('<div class="section-head">Executive Summary</div>', unsafe_allow_html=True)
        badges = ''.join(
            f'<span class="risk-badge risk-HIGH">⚠️ {html.escape(str(name))}</span>'
            for name in high_risk
        ) or '<span class="risk-badge risk-LOW">No high-risk commodities</span>'
        cols = st.columns([2, 1])
        with cols[0]:
            st.markdown(
                f'<div class="hero-card"><div class="lbl">⚠️ High-Risk Items ({len(high_risk)})</div>'
                f'<div style="margin-top:10px">{badges}</div></div>',
                unsafe_allow_html=True,
            )
        with cols[1]:
            feature_card('Action items', f'{len(recommendations)} commodities')
        st.caption('For live model MAPE and the model comparison, see the Model Trust page.')
        st.markdown('<div class="section-head">Priority Actions</div>', unsafe_allow_html=True)
        if recommendations.empty:
            st.info('No recommendation rows are available in the saved report.')
        else:
            action_priority = {
                'PROCURE NOW': 0, 'PARTIAL PROCUREMENT': 1, 'HEDGE': 2,
                'HOLD': 3, 'DELAY PROCUREMENT': 4,
            }
            recommendations['action_priority'] = recommendations.action.map(action_priority).fillna(99)
            if 'risk_score' not in recommendations:
                recommendations['risk_score'] = 0
            recommendations['risk_score'] = pd.to_numeric(recommendations.risk_score, errors='coerce').fillna(0)
            recommendations = recommendations.sort_values(
                ['action_priority', 'risk_score'], ascending=[True, False]
            )
            columns = st.columns(2)
            for i, (_, item) in enumerate(recommendations.iterrows()):
                action = safe_text(item.get('action'), 'HOLD').upper()
                action_css = action.replace(' ', '-')
                if action_css not in {'PROCURE-NOW', 'PARTIAL-PROCUREMENT', 'HEDGE', 'HOLD', 'DELAY-PROCUREMENT'}:
                    action_css = 'HOLD'
                risk = safe_text(item.get('risk'), 'LOW').upper()
                if risk not in {'HIGH', 'MEDIUM', 'LOW'}:
                    risk = 'LOW'
                driver = item.get('driver1', item.get('driver', 'market_price'))
                if pd.isna(driver):
                    driver = 'market_price'
                raw_trigger = safe_text(item.get('trigger'), 'Routine market conditions')
                narrative = raw_trigger.split(';', 1)[0].strip()
                trigger = f'{narrative} - mainly driven by {humanize_feature(driver)}'
                commodity = html.escape(safe_text(item.get('commodity'), 'Commodity'))
                markup = (
                    f'<div class="cardfull-{action_css}"><div class="card-action">{html.escape(action)}</div>'
                    f'<div class="card-title">{commodity} <span class="risk-badge risk-{risk}">{risk} RISK</span></div>'
                    f'<div class="card-trigger">{html.escape(trigger)}</div><div class="card-details">'
                    f'<div><b>Current:</b> ₹{float(item.get("current_price", 0)):,.0f}/quintal</div>'
                    f'<div><b>14-day forecast:</b> ₹{float(item.get("forecast_14d", 0)):,.0f}/quintal</div>'
                    f'<div><b>Expected change:</b> {float(item.get("forecast_14d_change_pct", 0)):+.1f}%</div>'
                    f'<div><b>Timing:</b> {html.escape(safe_text(item.get("timing"), "Review market conditions"))}</div>'
                    f'<div><b>Quantity:</b> {html.escape(safe_text(item.get("quantity_guidance"), "Standard replenishment"))}</div>'
                    f'<div><b>Estimated savings:</b> ₹{float(item.get("estimated_savings_per_quintal", 0)):,.0f}/quintal</div>'
                    '</div></div>'
                )
                with columns[i % 2]:
                    st.markdown(markup, unsafe_allow_html=True)

elif page == 'forecast':
    model_path = MODELS / 'ml_results.pkl'
    if features.exists() and model_path.exists():
        data = parquet(str(features)).copy()
        data['arrival_date'] = pd.to_datetime(data['arrival_date'])
        models = ml_models(str(model_path))
        commodity = st.selectbox('Commodity', sorted(models))
        horizon = st.selectbox('Forecast horizon (days)', [7, 14, 30])
        group = data[data.commodity == commodity].sort_values('arrival_date')
        if group.empty:
            st.warning(f'No feature rows are available for {commodity}.')
        else:
            latest = group.iloc[-1]
            future = pd.Timestamp(latest.arrival_date) + pd.Timedelta(days=horizon)
            row = latest[models[commodity]['features']].copy().astype(float)
            for key, value in {
                'month': future.month, 'week_of_year': int(future.isocalendar().week),
                'quarter': future.quarter, 'day_of_week': future.dayofweek, 'year': future.year,
            }.items():
                if key in row:
                    row[key] = value
            val = float(models[commodity]['model'].predict(row.to_frame().T.astype(float))[0])
            current = float(latest.modal_price)
            delta = (val / current - 1) * 100 if current else 0.0
            arrow = 'up' if delta >= 0 else 'down'
            icon = '📈' if delta >= 0 else '📉'
            flow = (
                '<div class="forecast-flow">'
                f'<div class="ff-block"><div class="ff-label">🎯 Current Price</div>'
                f'<div class="ff-value">₹{current:,.0f}/quintal</div>'
                f'<div class="ff-sub">as of {pd.Timestamp(latest.arrival_date):%d %b %Y}</div></div>'
                f'<div class="ff-arrow {arrow}">{icon}<span class="ff-delta">{delta:+.1f}%</span></div>'
                f'<div class="ff-block"><div class="ff-label">🔮 {horizon}-Day Forecast</div>'
                f'<div class="ff-value">₹{val:,.0f}/quintal</div>'
                f'<div class="ff-sub">by {future:%d %b %Y}</div></div></div>'
            )
            st.markdown(flow, unsafe_allow_html=True)
            st.markdown('<div class="section-head">90-Day Price History</div>', unsafe_allow_html=True)
            history = group.tail(90).set_index('arrival_date')['modal_price']
            st.line_chart(history)
            st.caption('Weather, market count, and cross-commodity features stay at their last known values across this horizon.')
    else:
        if not features.exists():
            warn(features, '04')
        if not model_path.exists():
            warn(model_path, '07')

elif page == 'trust':
    st.markdown('<div class="section-head">Model Leaderboard</div>', unsafe_allow_html=True)
    paths = {
        'RF': REPORT / 'ml_summary.csv', 'XGBoost': REPORT / 'ml_summary.csv',
        'SARIMA': REPORT / 'sarima_summary.csv', 'Prophet': REPORT / 'prophet_summary.csv',
    }
    colors = {'RF': '#4e9eed', 'XGBoost': '#f5a742', 'SARIMA': '#52c77e', 'Prophet': '#e5534b'}
    model_map = {name: {} for name in paths}
    raw_tables = {}
    for name, path in paths.items():
        if path.exists() and path not in raw_tables:
            raw_tables[path] = csv(str(path))
    ml_table = raw_tables.get(REPORT / 'ml_summary.csv')
    if ml_table is not None and {'commodity', 'model', 'mape'}.issubset(ml_table.columns):
        ml_table = ml_table[ml_table.commodity.astype(str) != 'AVERAGE']
        for name in ('RF', 'XGBoost'):
            selected = ml_table[ml_table.model.astype(str).str.casefold() == name.casefold()]
            model_map[name] = selected.dropna(subset=['mape']).groupby('commodity').mape.first().to_dict()
    for name in ('SARIMA', 'Prophet'):
        table = raw_tables.get(paths[name])
        if table is not None and {'commodity', 'mape'}.issubset(table.columns):
            table = table[table.commodity.astype(str) != 'AVERAGE']
            model_map[name] = table.dropna(subset=['mape']).groupby('commodity').mape.first().to_dict()
    all_commodities = sorted(set().union(*(set(values) for values in model_map.values())))
    leaderboard = pd.DataFrame({name: pd.Series(values) for name, values in model_map.items()}).reindex(all_commodities)
    if leaderboard.empty:
        warn(REPORT / 'ml_summary.csv', '07')
    else:
        leaderboard.index.name = 'commodity'
        wins = {name: 0 for name in model_map}
        for _, values in leaderboard.iterrows():
            available = values.dropna()
            if not available.empty:
                best_mape = available.min()
                for name in available.index[available == best_mape]:
                    wins[name] += 1
        cards = st.columns(4)
        for i, name in enumerate(('RF', 'XGBoost', 'SARIMA', 'Prophet')):
            with cards[i]:
                st.markdown(
                    f'<div class="hero-card" style="border-top:5px solid {colors[name]}">'
                    f'<div class="lbl">{html.escape(name)} wins</div>'
                    f'<div class="big">{wins[name]}/{len(leaderboard)}</div></div>',
                    unsafe_allow_html=True,
                )
        leaderboard['winning_mape'] = leaderboard.min(axis=1, skipna=True)
        leaderboard = leaderboard.sort_values('winning_mape', ascending=True, na_position='last')
        for commodity, values in leaderboard.iterrows():
            winning_mape = values['winning_mape']
            rows = []
            valid = values.drop(labels=['winning_mape']).dropna()
            best_mape = valid.min() if not valid.empty else None
            for model_name in ('RF', 'XGBoost', 'SARIMA', 'Prophet'):
                mape = values.get(model_name)
                if pd.isna(mape):
                    continue
                width = 100.0 if mape == 0 else (100.0 * best_mape / mape if best_mape is not None else 0.0)
                rows.append(
                    f'<div class="mbar-row"><div class="mbar-label">{html.escape(model_name)}</div>'
                    f'<div class="mbar-track"><div class="mbar-fill" style="width:{min(100,max(0,width)):.1f}%;background:{colors[model_name]}"></div></div>'
                    f'<div class="mbar-val">{float(mape):.1f}% MAPE</div></div>'
                )
            winning_text = f'{float(winning_mape):.1f}% best MAPE' if pd.notna(winning_mape) else 'No model score'
            st.markdown(
                f'<div class="leader-card"><div class="leader-head"><span>{html.escape(str(commodity))}</span>'
                f'<span>{winning_text}</span></div>{"".join(rows)}</div>',
                unsafe_allow_html=True,
            )
    with st.expander('Raw model summary tables', expanded=False):
        for path, table in raw_tables.items():
            st.markdown(f'**{html.escape(path.stem.replace("_", " ").title())}**')
            st.dataframe(table, use_container_width=True)
        if not raw_tables:
            st.caption('Run scripts 05–07 to generate model summary tables.')

elif page == 'movers':
    st.markdown('<div class="section-head">7-Day Price Movers</div>', unsafe_allow_html=True)
    if raw.exists():
        render_price_movers(parquet(str(raw)))
    else:
        warn(raw, '02')

elif page == 'snapshot':
    st.markdown('<div class="section-head">Dataset Snapshot</div>', unsafe_allow_html=True)
    if raw.exists():
        data = parquet(str(raw)).copy()
        data['arrival_date'] = pd.to_datetime(data['arrival_date'])
        cards = st.columns(3)
        for column, label, value in zip(cards, ('Observations', 'Commodities', 'Markets'), (f'{len(data):,}', data.commodity.nunique(), data.market.nunique())):
            with column:
                feature_card(label, value)
        st.markdown('<div class="section-head">Aggregate Price Trend</div>', unsafe_allow_html=True)
        trend = data.groupby('arrival_date').modal_price.median().sort_index()
        st.line_chart(trend)
        st.caption('This Kaggle build is filtered to price records from 2024 onward; earlier years are outside the selected input window.')
    else:
        warn(raw, '02')

elif page == 'trends':
    st.markdown('<div class="section-head">Market Trends & Seasonality</div>', unsafe_allow_html=True)
    if raw.exists():
        data = parquet(str(raw)).copy()
        data['arrival_date'] = pd.to_datetime(data['arrival_date'])
        trends_tab, season_tab, coverage_tab = st.tabs(['Price Trends', 'Seasonality', 'Market Coverage'])
        with trends_tab:
            years = sorted(data.arrival_date.dt.year.unique())
            if years:
                year = st.selectbox('Year', years, index=len(years) - 1)
                commodity = st.selectbox('Commodity', sorted(data.commodity.dropna().unique()), key='trend_commodity')
                group = data[(data.commodity == commodity) & (data.arrival_date.dt.year == year)]
                st.line_chart(group.groupby('arrival_date').modal_price.median())
        with season_tab:
            commodity = st.selectbox('Commodity', sorted(data.commodity.dropna().unique()), key='season_commodity')
            group = data[data.commodity == commodity].assign(month=lambda frame: frame.arrival_date.dt.month)
            st.bar_chart(group.groupby('month').modal_price.median())
        with coverage_tab:
            st.bar_chart(data.market.value_counts().head(20))
            st.line_chart(data.groupby(data.arrival_date.dt.year).size())
    else:
        warn(raw, '02')

elif page == 'quality':
    st.markdown('<div class="section-head">Data Quality</div>', unsafe_allow_html=True)
    if raw.exists():
        data = parquet(str(raw))
        st.caption('Null checks are calculated for every field in the filtered 2024-onward price dataset.')
        render_health_grid(data)
    else:
        warn(raw, '02')

elif page == 'shap':
    st.markdown('<div class="section-head">SHAP Explainability</div>', unsafe_allow_html=True)
    tabs = st.tabs(['Per-Commodity SHAP', 'Tomato Deep-Dive', 'Global Insights'])
    with tabs[0]:
        commodity = st.selectbox('Commodity', ['Tomato', 'Onion', 'Potato', 'Cabbage', 'Carrot', 'Beans', 'Brinjal', 'Drumstick'])
        path = FIG / f'shap_bar_{commodity.lower()}.png'
        st.image(str(path)) if path.exists() else warn(path, '08')
    with tabs[1]:
        st.info('SHAP values show each feature contribution to the selected model prediction; they describe model behavior, not causal effects.')
        path = FIG / 'shap_tomato_waterfall.png'
        st.image(str(path)) if path.exists() else warn(path, '08')
        for path in FIG.glob('shap_tomato_dependence_*.png'):
            st.image(str(path))
    with tabs[2]:
        path = FIG / 'shap_global_importance.png'
        st.image(str(path)) if path.exists() else warn(path, '08')