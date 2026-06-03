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


def get_regular_payments_for_period(today, period_start_day, period_end_day):
    """Возвращает сумму НЕОПЛАЧЕННЫХ регулярных платежей за период с учётом периодичности"""
    from database import get_db

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    total = 0
    for p in payments:
        if not p['day']:
            continue

        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

        in_period = False
        if period_start_day <= period_end_day:
            if period_start_day <= payment_day <= period_end_day:
                in_period = True
        else:
            if payment_day >= period_start_day or payment_day <= period_end_day:
                in_period = True

        if in_period:
            interval = p['interval'] if p['interval'] else 'monthly'
            amount = p['amount']
            if interval == 'monthly':
                total += amount
            elif interval == 'weekly':
                total += amount * 2
            elif interval == 'yearly':
                total += amount / 24
            else:
                total += amount

    return total


def get_regular_total_for_month():
    from database import get_db
    with get_db() as conn:
        result = conn.execute('SELECT SUM(amount) FROM regular_payments').fetchone()[0]
        return result or 0


def apply_regular_payments():
    """Автоматически добавляет операции по регулярным платежам за сегодня"""
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


def get_unpaid_regular_payments(today, period_start_day, period_end_day):
    """Возвращает сумму НЕОПЛАЧЕННЫХ регулярных платежей за период (дата списания уже прошла)"""
    from database import get_db
    from datetime import datetime, date

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()
        start_of_month = date(today.year, today.month, 1)
        operations = conn.execute('''
            SELECT category, subcategory, amount FROM operations 
            WHERE date >= ? AND type = 'Расход'
        ''', (start_of_month,)).fetchall()

    paid = {(op['category'], op['subcategory'], op['amount']) for op in operations}

    total = 0
    today_day = today.day

    for p in payments:
        if not p['day']:
            continue

        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

        in_period = False
        if period_start_day <= period_end_day:
            if period_start_day <= payment_day <= period_end_day:
                in_period = True
        else:
            if payment_day >= period_start_day or payment_day <= period_end_day:
                in_period = True

        is_passed = today_day >= payment_day

        if in_period and is_passed and (p['category'], p['subcategory'], p['amount']) not in paid:
            interval = p['interval'] if p['interval'] else 'monthly'
            amount = p['amount']
            if interval == 'monthly':
                total += amount
            elif interval == 'weekly':
                total += amount * 2
            elif interval == 'yearly':
                total += amount / 24
            else:
                total += amount

    return total


def get_regular_payments_until_date(today, target_date):
    """Возвращает сумму регулярных платежей, которые произойдут между today и target_date (включительно)"""
    from database import get_db
    from datetime import datetime

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    total = 0
    today_day = today.day
    target_day = target_date.day

    for p in payments:
        if not p['day']:
            continue

        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

        if today_day <= target_day:
            is_between = today_day <= payment_day <= target_day
        else:
            is_between = payment_day >= today_day or payment_day <= target_day

        if is_between:
            interval = p['interval'] if p['interval'] else 'monthly'
            amount = p['amount']
            if interval == 'monthly':
                total += amount
            elif interval == 'weekly':
                total += amount * 2
            elif interval == 'yearly':
                total += amount / 24
            else:
                total += amount

    return total


def get_regular_payments_after_date(today, target_date):
    """Возвращает сумму регулярных платежей, которые произойдут ПОСЛЕ target_date (в текущем месяце)"""
    from database import get_db
    from datetime import datetime

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    total = 0
    target_day = target_date.day

    for p in payments:
        if not p['day']:
            continue

        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

        if payment_day > target_day:
            interval = p['interval'] if p['interval'] else 'monthly'
            amount = p['amount']
            if interval == 'monthly':
                total += amount
            elif interval == 'weekly':
                total += amount * 2
            elif interval == 'yearly':
                total += amount / 24
            else:
                total += amount

    return total


def get_regular_payments_for_month():
    """Возвращает общую сумму регулярных платежей за месяц (без учёта оплаченных)"""
    from database import get_db

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    total = 0
    for p in payments:
        interval = p['interval'] if p['interval'] else 'monthly'
        amount = p['amount']
        if interval == 'monthly':
            total += amount
        elif interval == 'weekly':
            total += amount * 4
        elif interval == 'yearly':
            total += amount / 12
        else:
            total += amount

    return total


def get_paid_regular_payments_this_month():
    """Возвращает сумму уже оплаченных регулярных платежей в текущем месяце"""
    from database import get_db
    from datetime import date

    today = date.today()
    start_of_month = date(today.year, today.month, 1)

    with get_db() as conn:
        operations = conn.execute('''
            SELECT category, subcategory, amount FROM operations 
            WHERE date >= ? AND type = 'Расход'
        ''', (start_of_month,)).fetchall()

        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    paid_amounts = set()
    for op in operations:
        for p in payments:
            if p['category'] == op['category'] and p['subcategory'] == op['subcategory'] and p['amount'] == op[
                'amount']:
                paid_amounts.add(p['amount'])

    return sum(paid_amounts)


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
        # Получаем все операции до начала периода
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