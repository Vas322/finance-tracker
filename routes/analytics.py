from flask import Blueprint, render_template, request
from datetime import date
from database import get_db
from services.analytics_service import get_analytics_period, get_period_summary, get_trend_data, get_category_breakdown
from services.period_service import get_next_income_date

bp = Blueprint('analytics', __name__)


@bp.route('/analytics')
def analytics():
    filter_key = request.args.get('period', 'current_cycle')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    period = get_analytics_period(filter_key, date_from, date_to)
    summary = get_period_summary(
        period['start'], period['end'],
        prev_start=period['prev_start'], prev_end=period['prev_end']
    )
    trend = get_trend_data(num_periods=6)
    categories = get_category_breakdown(
        period['start'], period['end'],
        period['prev_start'], period['prev_end']
    )

    has_operations = bool(categories)

    growth_count = sum(1 for c in categories if c['pct_change'] and c['pct_change'] > 20)
    decline_count = sum(1 for c in categories if c['pct_change'] and c['pct_change'] < -10)
    new_count = sum(1 for c in categories if c['verdict'] == '🟡 Категория появилась впервые')
    stable_count = sum(1 for c in categories if not c['verdict'])
    attention_count = growth_count + new_count
    improved_count = decline_count
    has_problem_categories = attention_count > 0

    # Achievement line
    achievement_text = ''
    if trend.get('periods') and len(trend['periods']) >= 2:
        prev_expense = trend['periods'][-2]['expense']
        curr_expense = trend['periods'][-1]['expense']
        if prev_expense:
            trend_expense_pct = round((curr_expense - prev_expense) / prev_expense * 100)
            if trend_expense_pct < -5:
                achievement_text = f'✅ В этом цикле расходы снизились на {abs(trend_expense_pct)}% по сравнению с прошлым.'
        if not achievement_text and not attention_count:
            achievement_text = '🎉 Все категории в норме — значительного роста нет.'

    # Replace Period card: days to next income, left in cycle
    today = date.today()
    next_income_date = get_next_income_date(today)
    days_to_income = (next_income_date - today).days
    days_left_in_cycle = (period['end'] - today).days if today <= period['end'] else 0

    with get_db() as conn:
        op_count = conn.execute(
            'SELECT COUNT(*) FROM operations WHERE type = ? AND date >= ? AND date <= ?',
            ('Расход', period['start'].strftime('%Y-%m-%d'), period['end'].strftime('%Y-%m-%d'))
        ).fetchone()[0]

    # Trend insight: income and expense change (for graph footer)
    trend_income_pct = None
    trend_expense_pct = None
    if len(trend['periods']) >= 2:
        prev_income = trend['periods'][-2]['income']
        curr_income = trend['periods'][-1]['income']
        if prev_income:
            trend_income_pct = round((curr_income - prev_income) / prev_income * 100)
        prev_expense = trend['periods'][-2]['expense']
        curr_expense = trend['periods'][-1]['expense']
        if prev_expense:
            trend_expense_pct = round((curr_expense - prev_expense) / prev_expense * 100)

    return render_template('analytics.html',
                           period=period,
                           summary=summary,
                           trend=trend,
                           categories=categories,
                           has_operations=has_operations,
                           growth_count=growth_count,
                           decline_count=decline_count,
                           new_count=new_count,
                           stable_count=stable_count,
                           attention_count=attention_count,
                           improved_count=improved_count,
                           has_problem_categories=has_problem_categories,
                           achievement_text=achievement_text,
                           trend_income_pct=trend_income_pct,
                           trend_expense_pct=trend_expense_pct,
                           days_to_income=days_to_income,
                           days_left_in_cycle=days_left_in_cycle,
                           op_count=op_count)