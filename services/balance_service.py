from datetime import date
from database import get_db, get_period_balance, set_period_balance
from services.period_service import get_period_dates, get_period, get_previous_period_dates
from services.regular_service import get_regular_total


def get_expenses_for_period(start_date: date, end_date: date) -> int:
    with get_db() as conn:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Расход' AND date >= ? AND date <= ?
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()
    return result['total']


def get_income_for_period(start_date: date, end_date: date) -> int:
    with get_db() as conn:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Доход' AND date >= ? AND date <= ?
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()
    return result['total']


def update_period_balance(today: date):
    period_start, period_end = get_period_dates(today)
    period_name = get_period(today.strftime('%Y-%m-%d'))
    existing = get_period_balance(period_name, period_start.strftime('%Y-%m-%d'))
    if existing is None:
        prev_start, prev_end = get_previous_period_dates(today)
        
        with get_db() as conn:
            # Get previous period balance
            prev_period_name = get_period(prev_start.strftime('%Y-%m-%d'))
            prev_balance_result = conn.execute(
                'SELECT balance FROM period_balance WHERE period = ? AND start_date = ?',
                (prev_period_name, prev_start.strftime('%Y-%m-%d'))
            ).fetchone()
            prev_balance = prev_balance_result['balance'] if prev_balance_result else 0
            
            # Calculate income and expenses for previous period
            prev_income = get_income_for_period(prev_start, prev_end)
            prev_expenses = get_expenses_for_period(prev_start, prev_end)
            
            # Get planned_salary from settings
            planned_salary_result = conn.execute(
                'SELECT value FROM settings WHERE key = ?', ('planned_salary',)
            ).fetchone()
            planned_salary = int(float(planned_salary_result['value']) * 100) if planned_salary_result else 0
            
            # Get regular_total_month
            regular_total_month = get_regular_total('month')
            
            # Calculate regular_reserve
            prev_regular_reserve = 0
            if planned_salary > 0 and prev_income > 0:
                prev_regular_reserve = int(regular_total_month * (prev_income / planned_salary))
            
            # Calculate closing balance
            closing_balance = prev_balance + prev_income - prev_expenses - prev_regular_reserve
            
            # Save new period balance
            set_period_balance(period_name, period_start.strftime('%Y-%m-%d'), closing_balance)
            return closing_balance
    return existing


def update_current_period_balance(today: date, new_balance: int):
    period_start, period_end = get_period_dates(today)
    period_name = get_period(today.strftime('%Y-%m-%d'))
    set_period_balance(period_name, period_start.strftime('%Y-%m-%d'), new_balance)
