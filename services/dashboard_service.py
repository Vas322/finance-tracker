from datetime import date
from database import get_db, get_period_balance
from config import Config
from services.period_service import get_period_dates, get_period, get_regular_cycle_start
from services.balance_service import get_expenses_for_period, get_income_for_period, update_period_balance
from services.regular_service import get_regular_total, get_paid_regular_payments_this_month, get_paid_regulars_in_period
from services.operation_service import get_latest_advance


def compute_dashboard_stats(today=None):
    if today is None:
        today = date.today()

    period_start_date, period_end_date = get_period_dates(today)
    period_balance = update_period_balance(today)
    expenses_this_period = get_expenses_for_period(period_start_date, period_end_date)
    income_this_period = get_income_for_period(period_start_date, period_end_date)

    with get_db() as conn:
        row = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()
    planned_salary = int(float(row['value']) * 100) if row else Config.DEFAULT_PLANNED_SALARY

    from services.period_service import calculate_next_income
    expected_income, next_income = calculate_next_income(today, planned_salary)
    days_to_income = (next_income - today).days

    real_advance = get_latest_advance()
    regular_total_month = get_regular_total(period_type='month')
    paid_regular = get_paid_regular_payments_this_month()
    remaining_regulars = max(0, regular_total_month - paid_regular)

    # Расчёт от начала цикла регулярного резерва (25-го числа)
    cycle_start = get_regular_cycle_start(today)
    income_since_cycle = get_income_for_period(cycle_start, today)
    expenses_since_cycle = get_expenses_for_period(cycle_start, today)
    regulars_paid_since_cycle = get_paid_regulars_in_period(cycle_start, today)

    cycle_start_period = get_period(cycle_start.strftime('%Y-%m-%d'))
    cycle_start_balance = get_period_balance(cycle_start_period, cycle_start.strftime('%Y-%m-%d')) or 0

    ratio = regular_total_month / planned_salary if planned_salary > 0 else 0
    daily_ratio = 1 - ratio
    regular_reserve = int(income_since_cycle * ratio - regulars_paid_since_cycle)

    cash_on_hand = cycle_start_balance + income_since_cycle - expenses_since_cycle
    can_spend_today = cash_on_hand - regular_reserve
    unpaid_regular_month = regular_total_month - paid_regular

    # Расходы без регулярных за текущий период
    with get_db() as conn:
        total_expense_without_regulars = conn.execute('''
            SELECT COALESCE(SUM(o.amount), 0) FROM operations o
            WHERE o.type = 'Расход' AND o.date >= ? AND o.date <= ?
            AND NOT EXISTS (
                SELECT 1 FROM regular_payments r
                WHERE r.category = o.category
                AND (r.subcategory = o.subcategory OR (r.subcategory IS NULL AND o.subcategory IS NULL))
            )
        ''', (period_start_date.strftime('%Y-%m-%d'), period_end_date.strftime('%Y-%m-%d'))).fetchone()[0]

    with get_db() as conn:
        remaining_received = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM operations
            WHERE type = 'Доход' AND category = 'Зарплата'
              AND (subcategory != 'Аванс' OR subcategory IS NULL)
              AND date >= ? AND date <= ?
        ''', (period_start_date.strftime('%Y-%m-%d'), period_end_date.strftime('%Y-%m-%d'))).fetchone()[0]

    future_income = max(0, expected_income - remaining_received)
    available_for_month = cash_on_hand + future_income - unpaid_regular_month
    daily_limit = can_spend_today / days_to_income if days_to_income > 0 else can_spend_today

    return {
        'today': today,
        'period_start_date': period_start_date,
        'period_end_date': period_end_date,
        'period_balance': period_balance,
        'expenses_this_period': expenses_this_period,
        'income_this_period': income_this_period,
        'next_income': next_income,
        'days_to_income': days_to_income,
        'planned_salary': planned_salary,
        'real_advance': real_advance,
        'regular_total_month': regular_total_month,
        'paid_regular': paid_regular,
        'remaining_regulars': remaining_regulars,
        'regular_reserve': regular_reserve,
        'can_spend_today': can_spend_today,
        'expected_income': expected_income,
        'cash_on_hand': cash_on_hand,
        'future_income': future_income,
        'available_for_month': available_for_month,
        'daily_limit': daily_limit,
        'unpaid_regular_month': unpaid_regular_month,
        'remaining_received': remaining_received,
        'total_expense_without_regulars': total_expense_without_regulars,
    }
