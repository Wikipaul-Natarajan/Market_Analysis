"""Mock-only backtest of existing procurement advice rules against the mock price panel."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRICES = ROOT / 'data' / 'mock' / 'koyambedu_mock_prices_daily.csv'
PREDICTIONS = ROOT / 'outputs' / 'reports' / 'mock_model_predictions.csv'
OUT = ROOT / 'outputs' / 'reports'
LOT_KG = 100.0
MODEL = 'XGBoost'
HORIZON = 14


def main():
    prices = pd.read_csv(PRICES, parse_dates=['date'])
    preds = pd.read_csv(PREDICTIONS, parse_dates=['date', 'origin'])
    # Use only matched XGBoost 14-day rows and only demonstration data.
    preds = preds[(preds.model == MODEL) & (preds.horizon_days == HORIZON)].copy()
    rows = []
    for _, f in preds.iterrows():
        hist = prices[(prices.project_commodity_candidate == f.commodity) &
                      (prices.date <= f.origin)].sort_values('date')
        # Forecast origin's price record is the current price observation.
        nowrow = hist[hist.date == f.origin]
        future = prices[(prices.project_commodity_candidate == f.commodity) &
                        (prices.date == f.date)]
        if len(nowrow) != 1 or len(future) != 1:
            continue
        current = float(nowrow.iloc[0].mock_price_inr_per_kg)
        actual_future = float(future.iloc[0].mock_price_inr_per_kg)
        predicted = float(f.predicted_mock_inr_per_kg)
        recent = hist.tail(30).mock_price_inr_per_kg.astype(float)
        mean = float(recent.mean())
        sd = float(recent.std()) if len(recent) > 1 else 0.0
        cv = sd / (mean or 1.0)
        z = (current - mean) / (sd or 1.0)
        change = (predicted / current - 1) * 100 if current else 0.0
        score = min(100.0, cv * 120 + abs(z) * 12 + abs(change) * 1.2)
        risk = 'HIGH' if score >= 55 else 'MEDIUM' if score >= 28 else 'LOW'
        action = ('PROCURE NOW' if change > 5 and risk != 'HIGH' else
                  'DELAY PROCUREMENT' if change < -5 else
                  'PARTIAL PROCUREMENT' if risk == 'HIGH' else
                  'HEDGE' if abs(change) > 3 else 'HOLD')
        # Fixed-lot scenario translation: procure now/HOLD = all today;
        # delay = all at horizon; partial/hedge = half today, half at horizon.
        current_share = 1.0 if action in ('PROCURE NOW', 'HOLD') else 0.0 if action == 'DELAY PROCUREMENT' else 0.5
        advice_cost = LOT_KG * (current_share * current + (1-current_share) * actual_future)
        baseline_cost = LOT_KG * current
        rows.append({
            'commodity': f.commodity, 'origin_date': f.origin.date().isoformat(),
            'evaluation_date': f.date.date().isoformat(), 'horizon_days': HORIZON,
            'current_mock_inr_per_kg': current, 'predicted_14d_mock_inr_per_kg': predicted,
            'actual_14d_mock_inr_per_kg': actual_future,
            'forecast_change_pct': change, 'cv_30d': cv, 'z_30d': z,
            'risk_score': score, 'risk_level': risk, 'advice_action': action,
            'advice_timing': ('within 1-2 days' if action == 'PROCURE NOW' else
                              'reassess in 7 days' if action == 'DELAY PROCUREMENT' else
                              'split purchase across 7-14 days'),
            'advice_quantity_guidance': ('70-100%' if action == 'PROCURE NOW' else
                                         '25-50%' if action in ('PARTIAL PROCUREMENT','HEDGE') else
                                         'defer discretionary volume' if action == 'DELAY PROCUREMENT' else
                                         'normal replenishment'),
            'fixed_lot_kg': LOT_KG, 'lot_share_bought_at_origin': current_share,
            'buy_now_baseline_cost_inr': baseline_cost,
            'advice_scenario_cost_inr': advice_cost,
            'simulated_savings_vs_buy_now_inr': baseline_cost - advice_cost,
            'simulated_savings_pct_vs_buy_now': (baseline_cost-advice_cost)/baseline_cost*100 if baseline_cost else 0,
            'is_demonstration_only': True,
        })
    result = pd.DataFrame(rows)
    if result.empty:
        raise RuntimeError('No matching mock XGBoost 14-day forecasts and price observations.')
    result.to_csv(OUT / 'mock_procurement_advice_backtest.csv', index=False)
    summary = result.groupby('advice_action', as_index=False).agg(
        cases=('commodity','size'), mean_simulated_savings_inr=('simulated_savings_vs_buy_now_inr','mean'),
        median_simulated_savings_inr=('simulated_savings_vs_buy_now_inr','median'))
    summary.to_csv(OUT / 'mock_procurement_advice_summary.csv', index=False)
    win_rate = float((result.simulated_savings_vs_buy_now_inr > 0).mean() * 100)
    report = [
        '# Mock procurement advice validation', '',
        '**Status: demonstration only.** This backtest applies the current deterministic risk and action thresholds in `scripts/09_agrisight_agents.py` to stored XGBoost 14-day mock forecasts. Every price and resulting cost is simulated; this does not validate real Koyambedu advice or establish realized savings.', '',
        '## Counterfactual assumptions', '',
        f'- Each case represents a fixed {LOT_KG:.0f} kg lot; buy-now baseline purchases the whole lot at the origin price.',
        '- PROCURE NOW and HOLD buy the lot at origin; DELAY buys it at the 14-day outcome; PARTIAL PROCUREMENT and HEDGE split the lot equally between origin and day 14.',
        '- The action labels and risk thresholds reproduce the existing advice rules. The fixed-lot translation is a backtest convention, not an operational procurement policy. In particular, DELAY is evaluated at day 14 although the production wording says reassess in 7 days.',
        '- Excludes storage, transport, spoilage, inventory, quantity constraints, quality differences, and stockout/service costs. It does not establish causal savings or forecast validity.', '',
        '## Results', '',
        f'- Evaluated cases: {len(result)} (commodity × forecast origin).',
        f'- Cases with positive simulated savings vs buying immediately: {win_rate:.1f}%.',
        f'- Mean simulated savings per fixed lot: INR {result.simulated_savings_vs_buy_now_inr.mean():.2f}.',
        f'- Total simulated savings across these non-independent test cases: INR {result.simulated_savings_vs_buy_now_inr.sum():.2f}.',
        '- Review action-level counts and means in `mock_procurement_advice_summary.csv`; case-level calculations are in `mock_procurement_advice_backtest.csv`.', '',
        '## Action breakdown', '', summary.to_markdown(index=False), '',
        'This is useful for exercising the proposal workflow and auditing rule behavior. Replace the mock panel with validated market observations and add operational costs and procurement constraints before treating the advice as decision-ready.'
    ]
    (OUT / 'mock_procurement_advice_validation.md').write_text('\n'.join(report)+'\n', encoding='utf-8')
    print(f'Wrote {len(result)} backtest cases')
    print(summary.to_string(index=False))
    print(f'Positive simulated savings rate: {win_rate:.1f}%')

if __name__ == '__main__':
    main()

