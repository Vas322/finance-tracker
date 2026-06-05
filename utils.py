from datetime import datetime, date, timedelta
from config import SALARY_DAY, ADVANCE_DAY
import calendar


def get_period(date_str):
    day = datetime.strptime(date_str, '%Y-%m-%d').day
    return "10-24" if 10 <= day <= 24 else "25-09"


def get_next_income_date(today):
    if today.day < SALARY_DAY:
        return date(today.year, today.month, SALARY_DAY)
    elif today.day < ADVANCE_DAY:
        return date(today.year, today.month, ADVANCE_DAY)
    else:
        next_month = today.month + 1
        year = today.year
        if next_month > 12:
            next_month = 1
            year += 1
        return date(year, next_month, SALARY_DAY)


def get_period_dates(today):
    """Возвращает даты начала и конца текущего периода"""
    if 10 <= today.day <= 24:
        period_start = date(today.year, today.month, 10)
        period_end = date(today.year, today.month, 24)
    else:
        if today.day >= 25:
            period_start = date(today.year, today.month, 25)
            if today.month == 12:
                period_end = date(today.year + 1, 1, 9)
            else:
                period_end = date(today.year, today.month + 1, 9)
        else:
            period_start = date(today.year, today.month - 1, 25) if today.month > 1 else date(today.year - 1, 12, 25)
            period_end = date(today.year, today.month, 9)
    return period_start, period_end


def _get_all_payments():
    from database import get_db
    with get_db() as conn:
        return conn.execute('SELECT * FROM regular_payments').fetchall()


def _payment_mult(interval, period_type):
    if interval == 'weekly':
        return 2 if period_type == 'period' else 4
    if interval == 'yearly':
        return 1/24 if period_type == 'period' else 1/12
    return 1


def _day_in_range(day, start, end):
    if start <= end:
        return start <= day <= end
    return day >= start or day <= end


def _get_paid_set():
    from database import get_db
    from datetime import date
    today = date.today()
    with get_db() as conn:
        ops = conn.execute(
            'SELECT category, subcategory, amount FROM operations WHERE date >= ? AND type = \'Расход\'',
            (date(today.year, today.month, 1),)
        ).fetchall()
    return {(op['category'], op['subcategory'], op['amount']) for op in ops}


def get_regular_total(period_type='month'):
    total = 0
    for p in _get_all_payments():
        mult = _payment_mult(p['interval'], period_type)
        total += p['amount'] * mult
    return total


def get_regular_payments_filtered(start_day=None, end_day=None, max_day=None, exclude_paid=False, period_type='period'):
    payments = _get_all_payments()
    paid = None
    today = None

    total = 0
    for p in payments:
        if not p['day']:
            continue
        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

        if start_day is not None and end_day is not None:
            if not _day_in_range(payment_day, start_day, end_day):
                continue
        if max_day is not None:
            from datetime import date
            today = date.today()
            if today.day < payment_day:
                continue

        if exclude_paid:
            if paid is None:
                paid = _get_paid_set()
            if (p['category'], p['subcategory'], p['amount']) in paid:
                continue

        mult = _payment_mult(p['interval'], period_type)
        total += p['amount'] * mult

    return total


# Backward-compatible aliases
def get_regular_payments_for_period(today, start, end):
    return get_regular_payments_filtered(start_day=start, end_day=end, period_type='period')


def get_regular_total_for_month():
    return get_regular_total(period_type='month')


def get_unpaid_regular_payments(today, start, end):
    payments = _get_all_payments()
    paid = _get_paid_set()
    total = 0
    today_day = today.day
    for p in payments:
        if not p['day']:
            continue
        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
        if not _day_in_range(payment_day, start, end):
            continue
        if today_day < payment_day:
            continue
        if (p['category'], p['subcategory'], p['amount']) in paid:
            continue
        mult = _payment_mult(p['interval'], 'period')
        total += p['amount'] * mult
    return total


def get_regular_payments_until_date(today, target_date):
    payments = _get_all_payments()
    total = 0
    today_day, target_day = today.day, target_date.day
    for p in payments:
        if not p['day']:
            continue
        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
        if today_day <= target_day:
            is_between = today_day <= payment_day <= target_day
        else:
            is_between = payment_day >= today_day or payment_day <= target_day
        if is_between:
            mult = _payment_mult(p['interval'], 'period')
            total += p['amount'] * mult
    return total


def get_regular_payments_after_date(today, target_date):
    payments = _get_all_payments()
    total = 0
    target_day = target_date.day
    for p in payments:
        if not p['day']:
            continue
        if datetime.strptime(p['day'], '%Y-%m-%d').day > target_day:
            mult = _payment_mult(p['interval'], 'period')
            total += p['amount'] * mult
    return total


def get_regular_payments_for_month():
    return get_regular_total(period_type='month')


def get_paid_regular_payments_this_month():
    paid = _get_paid_set()
    payments = _get_all_payments()
    paid_amounts = set()
    for p in payments:
        if (p['category'], p['subcategory'], p['amount']) in paid:
            paid_amounts.add(p['amount'])
    return sum(paid_amounts)


def apply_regular_payments():
    from database import get_db
    from datetime import date, datetime

    today = date.today()
    today_day = today.day
    today_str = today.strftime('%Y-%m-%d')

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

        for p in payments:
            if not p['day']:
                continue

            payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

            should_apply = False

            if p['interval'] == 'monthly':
                if payment_day == today_day:
                    should_apply = True
            elif p['interval'] == 'weekly':
                payment_date = datetime.strptime(p['day'], '%Y-%m-%d')
                if payment_date.weekday() == today.weekday():
                    should_apply = True
            elif p['interval'] == 'yearly':
                payment_date = datetime.strptime(p['day'], '%Y-%m-%d')
                if payment_date.month == today.month and payment_date.day == today_day:
                    should_apply = True

            if should_apply and p['category']:
                existing = conn.execute('''
                    SELECT id FROM operations 
                    WHERE date = ? AND category = ? AND subcategory = ? AND amount = ? AND type = 'Расход'
                ''', (today_str, p['category'], p['subcategory'], p['amount'])).fetchone()

                if not existing:
                    period = "10-24" if 10 <= today_day <= 24 else "25-09"
                    conn.execute('''
                        INSERT INTO operations (date, type, category, subcategory, amount, comment, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (today_str, 'Расход', p['category'], p['subcategory'], p['amount'],
                          f'Авто: {p["interval"]}', period))


def get_planning_data(planned_salary, real_advance, regular_total, paid_regular=0):
    """Возвращает данные для планирования бюджета"""
    if real_advance > 0:
        advance = real_advance
        remaining_salary = planned_salary - advance
        advance_percent = advance / planned_salary if planned_salary > 0 else 0
    else:
        advance_percent = 0.5
        advance = planned_salary * advance_percent
        remaining_salary = planned_salary - advance

    regular_to_save = max(0, regular_total - paid_regular)

    need_to_save_from_advance = regular_to_save * advance_percent
    need_to_save_from_remaining = regular_to_save * (1 - advance_percent)

    return {
        'advance': advance,
        'remaining_salary': remaining_salary,
        'advance_percent': advance_percent,
        'regular_to_save': regular_to_save,
        'need_to_save_from_advance': need_to_save_from_advance,
        'need_to_save_from_remaining': need_to_save_from_remaining,
        'left_from_advance': advance - need_to_save_from_advance,
        'left_from_remaining': remaining_salary - need_to_save_from_remaining
    }


def get_expenses_for_period(start_date, end_date):
    """Возвращает сумму расходов за период"""
    from database import get_db

    with get_db() as conn:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Расход' AND date >= ? AND date <= ?
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()
    return result['total']


def update_period_balance(today):
    """Обновляет остаток на начало текущего периода, если он ещё не установлен"""
    from database import get_db, get_period_balance, set_period_balance
    from datetime import date

    period_start, period_end = get_period_dates(today)
    period_name = get_period(today.strftime('%Y-%m-%d'))

    existing = get_period_balance(period_name, period_start.strftime('%Y-%m-%d'))
    if existing is None:
        # Рассчитываем остаток на начало периода
        with get_db() as conn:
            result = conn.execute('''
                SELECT COALESCE(SUM(CASE WHEN type = 'Доход' THEN amount ELSE -amount END), 0) as balance
                FROM operations
                WHERE date < ?
            ''', (period_start.strftime('%Y-%m-%d'),)).fetchone()
            balance = result['balance']
        set_period_balance(period_name, period_start.strftime('%Y-%m-%d'), balance)
        return balance
    return existing


def update_current_period_balance(today, new_balance):
    """Обновляет остаток на начало текущего периода (ручное редактирование)"""
    from database import get_period_balance, set_period_balance
    period_start, period_end = get_period_dates(today)
    period_name = get_period(today.strftime('%Y-%m-%d'))
    set_period_balance(period_name, period_start.strftime('%Y-%m-%d'), new_balance)