from datetime import datetime, date
from typing import Optional
from database import get_db


def _get_all_payments():
    with get_db() as conn:
        return conn.execute('SELECT * FROM regular_payments').fetchall()


def _payment_mult(interval: str, period_type: str) -> float:
    if interval == 'weekly':
        return 2 if period_type == 'period' else 4
    if interval == 'yearly':
        return 1/24 if period_type == 'period' else 1/12
    return 1


def _day_in_range(day: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= day <= end
    return day >= start or day <= end


def _get_paid_set(start_date=None, end_date=None):
    today = date.today()
    if start_date is None:
        start_date = date(today.year, today.month, 1)
    if end_date is None:
        end_date = date(today.year, today.month, today.day)
    with get_db() as conn:
        ops = conn.execute(
            'SELECT category, subcategory FROM operations WHERE date >= ? AND date <= ? AND type = \'Расход\'',
            (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        ).fetchall()
    return {(op['category'], op['subcategory'] or '') for op in ops}


def get_regular_total(period_type: str = 'month') -> float:
    total = 0.0
    for p in _get_all_payments():
        mult = _payment_mult(p['interval'], period_type)
        total += p['amount'] * mult
    return total


def get_regular_payments_filtered(
    start_day: Optional[int] = None,
    end_day: Optional[int] = None,
    max_day: Optional[int] = None,
    exclude_paid: bool = False,
    period_type: str = 'period'
) -> float:
    payments = _get_all_payments()
    paid = None
    today = None
    total = 0.0
    for p in payments:
        if not p['day']:
            continue
        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
        if start_day is not None and end_day is not None:
            if not _day_in_range(payment_day, start_day, end_day):
                continue
        if max_day is not None:
            today = date.today()
            if today.day < payment_day:
                continue
        if exclude_paid:
            if paid is None:
                paid = _get_paid_set()
            if (p['category'], p['subcategory'] or '') in paid:
                continue
        mult = _payment_mult(p['interval'], period_type)
        total += p['amount'] * mult
    return total


def get_regular_payments_for_period(today: date, start: int, end: int) -> float:
    return get_regular_payments_filtered(start_day=start, end_day=end, period_type='period')


def get_unpaid_regular_payments(today: date, start: int, end: int) -> float:
    payments = _get_all_payments()
    paid = _get_paid_set()
    total = 0.0
    today_day = today.day
    for p in payments:
        if not p['day']:
            continue
        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
        if not _day_in_range(payment_day, start, end):
            continue
        if today_day < payment_day:
            continue
        if (p['category'], p['subcategory'] or '') in paid:
            continue
        mult = _payment_mult(p['interval'], 'period')
        total += p['amount'] * mult
    return total


def get_regular_payments_until_date(today: date, target_date: date) -> float:
    payments = _get_all_payments()
    total = 0.0
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


def get_regular_payments_after_date(today: date, target_date: date) -> float:
    payments = _get_all_payments()
    total = 0.0
    target_day = target_date.day
    for p in payments:
        if not p['day']:
            continue
        if datetime.strptime(p['day'], '%Y-%m-%d').day > target_day:
            mult = _payment_mult(p['interval'], 'period')
            total += p['amount'] * mult
    return total


def get_paid_regular_payments_this_month() -> float:
    paid = _get_paid_set()
    payments = _get_all_payments()
    total = 0.0
    checked = set()
    for p in payments:
        key = (p['category'], p['subcategory'] or '')
        if key in checked:
            continue
        checked.add(key)
        if key in paid:
            total += p['amount']
    return total


def get_paid_regular_payments_in_period(start_date, end_date) -> float:
    paid = _get_paid_set(start_date, end_date)
    payments = _get_all_payments()
    total = 0.0
    checked = set()
    for p in payments:
        key = (p['category'], p['subcategory'] or '')
        if key in checked:
            continue
        checked.add(key)
        if key in paid:
            total += p['amount']
    return total


def get_due_regular_payments(today: date):
    today_day = today.day
    due = []
    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()
        for p in payments:
            if not p['day'] or not p['category']:
                continue
            payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
            is_due = False
            if p['interval'] == 'monthly' and payment_day == today_day:
                is_due = True
            elif p['interval'] == 'weekly':
                pd = datetime.strptime(p['day'], '%Y-%m-%d')
                if pd.weekday() == today.weekday():
                    is_due = True
            elif p['interval'] == 'yearly':
                pd = datetime.strptime(p['day'], '%Y-%m-%d')
                if pd.month == today.month and pd.day == today_day:
                    is_due = True
            if not is_due:
                continue
            due.append({
                'id': p['id'],
                'category': p['category'],
                'subcategory': p['subcategory'] or '',
                'amount': p['amount'],
                'interval': p['interval']
            })
    return due


def apply_regular_payments():
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
        conn.commit()
