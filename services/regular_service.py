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


def _get_paid_ids(start_date=None, end_date=None):
    """Возвращает set{regular_payment_id} оплаченных регулярных платежей за период."""
    today = date.today()
    if start_date is None:
        start_date = date(today.year, today.month, 1)
    if end_date is None:
        end_date = date(today.year, today.month, today.day)
    with get_db() as conn:
        rows = conn.execute(
            'SELECT DISTINCT regular_payment_id FROM operations WHERE date >= ? AND date <= ? AND type = \'Расход\' AND regular_payment_id IS NOT NULL',
            (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        ).fetchall()
    return {row['regular_payment_id'] for row in rows}


def get_regular_total(period_type: str = 'month') -> int:
    total = 0
    for p in _get_all_payments():
        mult = _payment_mult(p['interval'], period_type)
        total += int(p['amount'] * mult)
    return total


def get_regular_payments_filtered(
    start_day=None, end_day=None, max_day=None,
    exclude_paid=False, period_type='period'
) -> float:
    payments = _get_all_payments()
    paid = None
    total = 0
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
                paid = _get_paid_ids()
            if p['id'] in paid:
                continue
        mult = _payment_mult(p['interval'], period_type)
        total += int(p['amount'] * mult)
    return total


def get_regular_payments_for_period(today: date, start: int, end: int) -> float:
    return get_regular_payments_filtered(start_day=start, end_day=end, period_type='period')


def get_unpaid_regular_payments(today: date, start: int, end: int) -> float:
    payments = _get_all_payments()
    paid = _get_paid_ids()
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
        if p['id'] in paid:
            continue
        mult = _payment_mult(p['interval'], 'period')
        total += int(p['amount'] * mult)
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
    paid = _get_paid_ids()
    payments = _get_all_payments()
    total = 0
    for p in payments:
        if p['id'] in paid:
            total += p['amount']
    return total


def get_paid_regular_payments_in_period(start_date, end_date) -> float:
    paid = _get_paid_ids(start_date, end_date)
    payments = _get_all_payments()
    total = 0
    for p in payments:
        if p['id'] in paid:
            total += p['amount']
    return total


def get_regular_totals_by_category(period_type='month') -> dict:
    """Возвращает {category: monthly_amount} для всех регулярных платежей."""
    totals = {}
    for p in _get_all_payments():
        cat = p['category']
        if not cat:
            continue
        mult = _payment_mult(p['interval'], period_type)
        totals[cat] = totals.get(cat, 0) + p['amount'] * mult
    return totals


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
                    WHERE date = ? AND regular_payment_id = ? AND type = 'Расход'
                ''', (today_str, p['id'])).fetchone()
                if not existing:
                    period = "10-24" if 10 <= today_day <= 24 else "25-09"
                    conn.execute('''
                        INSERT INTO operations (date, type, category, subcategory, amount, comment, period, regular_payment_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (today_str, 'Расход', p['category'], p['subcategory'], p['amount'],
                          f'Авто: {p["interval"]}', period, p['id']))
        conn.commit()
