from collections import Counter
from datetime import datetime, date
from typing import Optional
from database import get_db
from services.period_service import get_regular_cycle_start


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


def _get_skipped_ids(cycle_start: date) -> set:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT regular_payment_id FROM regular_skips WHERE cycle_start = ?',
            (cycle_start.strftime('%Y-%m-%d'),)
        ).fetchall()
    return {r['regular_payment_id'] for r in rows}


def get_skipped_total(cycle_start: date) -> int:
    skipped_ids = _get_skipped_ids(cycle_start)
    total = 0
    for p in _get_all_payments():
        if p['id'] in skipped_ids:
            total += int(p['amount'])
    return total


def skip_regular_payment(payment_id: int, cycle_start: date):
    with get_db() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO regular_skips (regular_payment_id, cycle_start) VALUES (?, ?)',
            (payment_id, cycle_start.strftime('%Y-%m-%d'))
        )
        conn.commit()


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


def get_paid_regulars_in_period(start_date, end_date) -> int:
    """Сумма оплаченных регулярных платежей за период.
       - по regular_payment_id (авто и через кнопку) — всегда учитываются
       - ручные операции, где (категория, подкатегория, сумма) совпадает с regular_payments
    """
    payments = _get_all_payments()
    paid_ids = _get_paid_ids(start_date, end_date)

    total = 0
    for p in payments:
        if p['id'] in paid_ids:
            total += p['amount']

    patterns = {(p['category'], p['subcategory'] or '', int(p['amount'])) for p in payments if p['category']}
    if patterns:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT category, COALESCE(subcategory, '') as subcat, amount FROM operations "
                "WHERE type='Расход' AND date >= ? AND date <= ? AND regular_payment_id IS NULL",
                (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            ).fetchall()
        for r in rows:
            if (r['category'], r['subcat'], int(r['amount'])) in patterns:
                total += r['amount']
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
    cycle_regulars = get_cycle_regulars_list(today)
    handled_ids = {r['id'] for r in cycle_regulars if r['paid'] or r['skipped']}
    due = []
    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()
        for p in payments:
            if not p['day'] or not p['category']:
                continue
            if p['id'] in handled_ids:
                continue
            payment_date_in_cycle = _payment_date_in_cycle(today, p['day'])
            if payment_date_in_cycle is None or payment_date_in_cycle > today:
                continue
            due.append({
                'id': p['id'],
                'category': p['category'],
                'subcategory': p['subcategory'] or '',
                'amount': p['amount'],
                'interval': p['interval'],
                'payment_date': payment_date_in_cycle,
            })
    return due


def apply_regular_payments():
    today = date.today()
    today_day = today.day
    today_str = today.strftime('%Y-%m-%d')
    cycle_start = get_regular_cycle_start(today)
    skipped_ids = _get_skipped_ids(cycle_start)
    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()
        for p in payments:
            if not p['day']:
                continue
            if p['id'] in skipped_ids:
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


def _payment_date_in_cycle(today: date, payment_day_str: str) -> Optional[date]:
    """Дата платежа в текущем регулярном цикле (25→24)."""
    day = int(payment_day_str.split('-')[2])
    cycle_start = get_regular_cycle_start(today)
    if day >= 25:
        try:
            return date(cycle_start.year, cycle_start.month, day)
        except ValueError:
            return None
    next_month = cycle_start.month + 1
    next_year = cycle_start.year
    if next_month > 12:
        next_month = 1
        next_year += 1
    try:
        return date(next_year, next_month, day)
    except ValueError:
        return None


def get_cycle_regulars_list(today: date) -> list[dict]:
    """Список всех регулярных платежей текущего цикла с пометкой об оплате."""
    cycle_start = get_regular_cycle_start(today)
    all_payments = _get_all_payments()
    paid_ids = _get_paid_ids(cycle_start, today)
    skipped_ids = _get_skipped_ids(cycle_start)

    patterns = {(p['category'], p['subcategory'] or '', int(p['amount']))
                for p in all_payments if p['category']}

    pattern_counts = Counter()
    if patterns:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT category, COALESCE(subcategory, '') as subcat, amount FROM operations "
                "WHERE type='Расход' AND date >= ? AND date <= ? AND regular_payment_id IS NULL",
                (cycle_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
            ).fetchall()
        for r in rows:
            key = (r['category'], r['subcat'], int(r['amount']))
            if key in patterns:
                pattern_counts[key] += 1

    result = []
    for p in all_payments:
        if not p['day'] or not p['category']:
            continue
        key = (p['category'], p['subcategory'] or '', int(p['amount']))
        paid = p['id'] in paid_ids
        if not paid and key in patterns and pattern_counts.get(key, 0) > 0:
            paid = True
            pattern_counts[key] -= 1
        skipped = p['id'] in skipped_ids
        result.append({
            'id': p['id'],
            'date': _payment_date_in_cycle(today, p['day']),
            'day': int(p['day'].split('-')[2]),
            'category': p['category'],
            'subcategory': p['subcategory'] or '',
            'amount': int(p['amount']),
            'interval': p['interval'],
            'paid': paid,
            'skipped': skipped,
        })

    result.sort(key=lambda x: (x['date'] or date.max, x['category']))
    return result
