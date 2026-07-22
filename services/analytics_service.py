from datetime import date, timedelta
from database import get_db
from services.period_service import get_period_dates, get_previous_period_dates, get_previous_cycle, get_salary_period
from services.balance_service import get_income_for_period, get_expenses_for_period


def get_analytics_period(filter_key: str, date_from: str, date_to: str) -> dict:
    today = date.today()
    if filter_key == 'current_cycle':
        start, end = get_period_dates(today)
        prev_start, prev_end = get_previous_period_dates(today)
        label = f'{start.strftime("%d.%m")}–{end.strftime("%d.%m")}'
    elif filter_key == 'last_cycle':
        start, end = get_previous_period_dates(today)
        prev_start, prev_end = get_previous_period_dates(start)
        label = f'{start.strftime("%d.%m")}–{end.strftime("%d.%m")}'
    elif filter_key == 'salary_month':
        start, end = get_salary_period(today)
        prev_start = start - timedelta(days=1)
        prev_start, prev_end = get_salary_period(prev_start)
        label = f'ЗП {start.strftime("%d.%m")}–{end.strftime("%d.%m")}'
    elif filter_key == 'custom' and date_from and date_to:
        start = date.fromisoformat(date_from)
        end = date.fromisoformat(date_to)
        delta_days = (end - start).days
        prev_start = start - timedelta(days=delta_days + 1)
        prev_end = start - timedelta(days=1)
        label = f'{start.strftime("%d.%m")}–{end.strftime("%d.%m")}'
    else:
        start, end = get_period_dates(today)
        prev_start, prev_end = get_previous_period_dates(today)
        label = f'{start.strftime("%d.%m")}–{end.strftime("%d.%m")}'
    return {
        'label': label,
        'start': start,
        'end': end,
        'prev_start': prev_start,
        'prev_end': prev_end,
    }


def get_period_summary(start: date, end: date, prev_start: date = None, prev_end: date = None) -> dict:
    income = get_income_for_period(start, end)
    expense = get_expenses_for_period(start, end)
    delta = income - expense
    days = max((end - start).days + 1, 1)
    today = date.today()
    if start <= today <= end:
        actual_end = today
    else:
        actual_end = end
    days_elapsed = max((actual_end - start).days + 1, 1)
    avg_daily = expense // days_elapsed

    coverage = round(income / expense * 100) if expense else None

    is_in_progress = start <= today <= end

    prev_avg_daily = None
    avg_daily_change = None
    avg_daily_label = None
    if prev_start and prev_end and prev_start < prev_end:
        prev_expense = get_expenses_for_period(prev_start, prev_end)
        prev_days = max((prev_end - prev_start).days + 1, 1)
        prev_avg_daily = prev_expense // prev_days
        if prev_avg_daily:
            avg_daily_change = round((avg_daily - prev_avg_daily) / prev_avg_daily * 100)
            if is_in_progress and abs(avg_daily_change) > 100:
                direction = 'выше' if avg_daily_change > 0 else 'ниже'
                avg_daily_label = f'↑ пока {direction} прошлого цикла'
            else:
                avg_daily_label = f'{"↑" if avg_daily_change > 0 else "↓"} {abs(avg_daily_change)}% к прошлому циклу'

    if delta > 0:
        verdict = '✅ Доходы превышают расходы'
    elif delta == 0:
        verdict = '⚠️ Ноль — всё уходит в расход'
    else:
        verdict = '🔴 Расходы превышают доходы'

    return {
        'income': income,
        'expense': expense,
        'delta': delta,
        'avg_daily': avg_daily,
        'coverage': coverage,
        'prev_avg_daily': prev_avg_daily,
        'avg_daily_change': avg_daily_change,
        'avg_daily_label': avg_daily_label,
        'is_in_progress': is_in_progress,
        'verdict': verdict,
    }


def get_trend_data(num_periods: int = 6) -> dict:
    cursor = date.today()
    periods = []
    for _ in range(num_periods):
        start, end = get_previous_cycle(cursor)
        income = get_income_for_period(start, end)
        expense = get_expenses_for_period(start, end)
        periods.append({
            'label': f'{start.strftime("%d.%m")}–{end.strftime("%d.%m")}',
            'income': income,
            'expense': expense,
            'balance': income - expense,
            'is_deficit': expense > income,
        })
        cursor = start - timedelta(days=1)
    periods.reverse()

    trend_verdict = ''
    if len(periods) >= 2:
        prev = periods[-2]['expense']
        curr = periods[-1]['expense']
        if prev > 0:
            pct = round((curr - prev) / prev * 100)
            if pct > 5:
                trend_verdict = f'Расходы растут ↗ (+{pct}% к предыдущему циклу)'
            elif pct < -5:
                trend_verdict = f'Расходы снижаются ↘ ({pct}% к предыдущему циклу)'
            else:
                trend_verdict = 'Расходы стабильны →'
        else:
            trend_verdict = 'Недостаточно данных для тренда'
    else:
        trend_verdict = 'Недостаточно данных для тренда'

    return {
        'periods': periods,
        'trend_verdict': trend_verdict,
    }


def get_category_breakdown(start: date, end: date, prev_start: date, prev_end: date) -> list[dict]:
    with get_db() as conn:
        curr_rows = conn.execute(
            'SELECT category, COALESCE(SUM(amount), 0) as total FROM operations '
            'WHERE type = ? AND date >= ? AND date <= ? GROUP BY category ORDER BY total DESC',
            ('Расход', start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        ).fetchall()

        prev_rows = conn.execute(
            'SELECT category, COALESCE(SUM(amount), 0) as total FROM operations '
            'WHERE type = ? AND date >= ? AND date <= ? GROUP BY category',
            ('Расход', prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d'))
        ).fetchall()

        # Look one more cycle back to avoid flagging recurring payments (15th) as "new"
        prev_prev_start, prev_prev_end = get_previous_period_dates(prev_start)
        prev_prev_rows = conn.execute(
            'SELECT category, COALESCE(SUM(amount), 0) as total FROM operations '
            'WHERE type = ? AND date >= ? AND date <= ? GROUP BY category',
            ('Расход', prev_prev_start.strftime('%Y-%m-%d'), prev_prev_end.strftime('%Y-%m-%d'))
        ).fetchall()

    curr = {r['category']: r['total'] for r in curr_rows}
    prev = {r['category']: r['total'] for r in prev_rows}
    prev_prev = {r['category']: r['total'] for r in prev_prev_rows}

    result = []
    for cat, amount in curr.items():
        prev_amount = prev.get(cat, 0)
        pct_change = round((amount - prev_amount) / prev_amount * 100) if prev_amount else None

        # Category is genuinely new only if absent in BOTH prev and prev_prev
        is_new = (prev_amount == 0 and cat not in prev_prev)

        if pct_change and pct_change > 20:
            verdict = f'🔴 Расходы выросли на {pct_change}%'
        elif pct_change and pct_change < -10:
            verdict = f'🟢 Расходы снизились на {abs(pct_change)}%'
        elif is_new:
            verdict = '🟡 Категория появилась впервые'
        else:
            verdict = ''

        result.append({
            'category': cat,
            'amount': amount,
            'prev_amount': prev_amount,
            'pct_change': pct_change,
            'verdict': verdict,
        })

    result.sort(key=lambda x: (
        0 if x['pct_change'] and x['pct_change'] > 20 else
        1 if x['verdict'] == '🟡 Категория появилась впервые' else 2,
        -x['amount']
    ))
    return result