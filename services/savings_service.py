from datetime import date as date_cls, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional
import calendar

from database import get_db
from utils import get_period

DAYS_IN_YEAR = Decimal('365')
PERCENT = Decimal('100')


def add_months(base: date_cls, months: int) -> date_cls:
    """Возвращает дату, сдвинутую на указанное количество месяцев."""
    month = base.month - 1 + months
    year = base.year + month // 12
    month = month % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date_cls(year, month, day)


def get_savings_total() -> int:
    with get_db() as conn:
        result = conn.execute(
            'SELECT COALESCE(SUM(balance), 0) FROM savings_accounts WHERE is_active = 1'
        ).fetchone()[0]
    return result


def get_all_accounts(active_only: bool = True) -> list:
    with get_db() as conn:
        if active_only:
            rows = conn.execute(
                'SELECT * FROM savings_accounts WHERE is_active = 1 ORDER BY sort_order'
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM savings_accounts ORDER BY sort_order'
            ).fetchall()
    return [dict(r) for r in rows]


def get_account(account_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM savings_accounts WHERE id = ?', (account_id,)
        ).fetchone()
    return dict(row) if row else None


def _normalize_term(start_date: Optional[str],
                    end_date: Optional[str],
                    duration_months: Optional[int]) -> tuple[Optional[str], Optional[int]]:
    """
    Приводит срок накопления к консистентному состоянию (детерминированное правило):
    - задан duration_months -> end_date пересчитан = start + months, duration_months сохраняется;
    - задан только end_date   -> duration_months = None;
    - ни то, ни то (бессрочный) -> end_date = None, duration_months = None.
    Возвращает (end_date, duration_months).
    """
    if duration_months is not None:
        if start_date:
            base = date_cls.fromisoformat(start_date)
            end_date = add_months(base, duration_months).isoformat()
        else:
            end_date = None
    elif end_date:
        duration_months = None
    else:
        end_date = None
    return end_date, duration_months


def create_account(name: str, target_amount: int = 0, target_date: Optional[str] = None,
                   icon: str = 'bi-piggy-bank', color: str = '#17a2b8',
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   duration_months: Optional[int] = None,
                   interest_rate: Optional[Decimal] = None,
                   bank: Optional[str] = None) -> int:
    end_date, duration_months = _normalize_term(start_date, end_date, duration_months)
    with get_db() as conn:
        max_sort = conn.execute(
            'SELECT COALESCE(MAX(sort_order), 0) + 1 FROM savings_accounts'
        ).fetchone()[0]
        cursor = conn.execute('''
            INSERT INTO savings_accounts (name, target_amount, target_date, icon, color,
                                          start_date, end_date, duration_months,
                                          interest_rate, bank, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, target_amount, target_date, icon, color,
              start_date, end_date, duration_months,
              str(interest_rate) if interest_rate is not None else None,
              bank, max_sort))
    return cursor.lastrowid


def update_account(account_id: int, **kwargs) -> None:
    allowed_fields = {'name', 'target_amount', 'target_date', 'icon', 'color', 'is_active', 'sort_order',
                      'start_date', 'end_date', 'duration_months', 'interest_rate', 'bank'}
    fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
    if not fields:
        return
    # Согласование срока: единая логика с create_account.
    if 'end_date' in fields or 'duration_months' in fields or 'start_date' in fields:
        start_date = fields.get('start_date')
        end_date = fields.get('end_date')
        duration_months = fields.get('duration_months') if 'duration_months' in fields else None
        if start_date is None and ('end_date' in fields or 'duration_months' in fields):
            account = get_account(account_id)
            start_date = account.get('start_date') if account else None
        elif 'end_date' not in fields and 'duration_months' not in fields:
            # Обновляется только start_date — сохраняем существующий срок.
            account = get_account(account_id)
            if account:
                end_date = account.get('end_date')
                duration_months = account.get('duration_months')
        end_date, duration_months = _normalize_term(start_date, end_date, duration_months)
        fields['end_date'] = end_date
        fields['duration_months'] = duration_months
    if 'interest_rate' in fields:
        fields['interest_rate'] = str(fields['interest_rate']) if fields['interest_rate'] is not None else None
    if not fields:
        return
    set_clause = ', '.join(f'{k} = ?' for k in fields)
    values = list(fields.values()) + [account_id]
    with get_db() as conn:
        conn.execute(
            f'UPDATE savings_accounts SET {set_clause}, updated_at = datetime(\'now\') WHERE id = ?',
            values
        )


def archive_account(account_id: int):
    with get_db() as conn:
        row = conn.execute(
            'SELECT balance FROM savings_accounts WHERE id = ?', (account_id,)
        ).fetchone()
        if not row:
            return
        if row['balance'] != 0:
            raise ValueError('Нельзя архивировать счёт с остатком')
        conn.execute(
            'UPDATE savings_accounts SET is_active = 0, updated_at = datetime(\'now\') WHERE id = ?',
            (account_id,)
        )


def reactivate_account(account_id: int):
    with get_db() as conn:
        conn.execute(
            'UPDATE savings_accounts SET is_active = 1, updated_at = datetime(\'now\') WHERE id = ?',
            (account_id,)
        )


def delete_account(account_id: int):
    with get_db() as conn:
        row = conn.execute(
            'SELECT balance FROM savings_accounts WHERE id = ?', (account_id,)
        ).fetchone()
        if not row:
            return
        if row['balance'] != 0:
            raise ValueError('Нельзя удалить счёт с остатком')
        conn.execute('DELETE FROM savings_accounts WHERE id = ?', (account_id,))


def deposit(account_id: int, amount: int, date_str: str, comment: str = ''):
    with get_db() as conn:
        conn.execute('BEGIN')
        try:
            # Получаем имя счёта
            account = conn.execute(
                'SELECT name FROM savings_accounts WHERE id = ?', (account_id,)
            ).fetchone()
            if not account:
                raise ValueError('Счёт не найден')

            period = get_period(date_str)

            # Вставляем операцию как Расход (откладывание)
            conn.execute('''
                INSERT INTO operations (type, category, subcategory, amount, date, comment, period)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('Расход', 'Накопления', account['name'], amount, date_str, comment, period))

            # Вставляем транзакцию накопления
            conn.execute('''
                INSERT INTO savings_transactions (savings_account_id, amount, type, date, comment)
                VALUES (?, ?, ?, ?, ?)
            ''', (account_id, +amount, 'deposit', date_str, comment))

            # Обновляем баланс счёта
            conn.execute('''
                UPDATE savings_accounts SET balance = balance + ?, updated_at = datetime('now')
                WHERE id = ?
            ''', (amount, account_id))

            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise


def withdraw(account_id: int, amount: int, date_str: str, comment: str = ''):
    with get_db() as conn:
        conn.execute('BEGIN')
        try:
            # Проверяем баланс
            account = conn.execute(
                'SELECT name, balance FROM savings_accounts WHERE id = ?', (account_id,)
            ).fetchone()
            if not account:
                raise ValueError('Счёт не найден')
            if account['balance'] < amount:
                raise ValueError('Недостаточно средств')

            period = get_period(date_str)

            # Вставляем операцию как Доход (снятие с накоплений)
            conn.execute('''
                INSERT INTO operations (type, category, subcategory, amount, date, comment, period)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('Доход', 'Снятие с накоплений', account['name'], amount, date_str, comment, period))

            # Вставляем транзакцию накопления
            conn.execute('''
                INSERT INTO savings_transactions (savings_account_id, amount, type, date, comment)
                VALUES (?, ?, ?, ?, ?)
            ''', (account_id, -amount, 'withdrawal', date_str, comment))

            # Обновляем баланс счёта
            conn.execute('''
                UPDATE savings_accounts SET balance = balance - ?, updated_at = datetime('now')
                WHERE id = ?
            ''', (amount, account_id))

            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise


def get_transactions(account_id: int, limit: int = 50) -> list:
    with get_db() as conn:
        rows = conn.execute('''
            SELECT * FROM savings_transactions
            WHERE savings_account_id = ?
            ORDER BY date DESC, id DESC
            LIMIT ?
        ''', (account_id, limit)).fetchall()
    return [dict(r) for r in rows]


def _parse_date(value: Optional[str]) -> Optional[date_cls]:
    if not value:
        return None
    try:
        return date_cls.fromisoformat(value)
    except ValueError:
        return None


def _to_decimal_rate(interest_rate: Optional[Decimal | str]) -> Optional[Decimal]:
    if interest_rate is None or interest_rate == '':
        return None
    try:
        return Decimal(str(interest_rate))
    except (InvalidOperation, ValueError):
        return None


def accrued_income(transactions: list[dict], start_date: Optional[str], interest_rate: Optional[Decimal | str]) -> int:
    """Накопленный доход (копейки) методом среднего дневного баланса."""
    rate = _to_decimal_rate(interest_rate)
    if rate is None or rate <= 0:
        return 0
    start = _parse_date(start_date)
    if not start:
        return 0
    today = date_cls.today()
    if start > today:
        return 0

    daily_deltas: dict[date_cls, Decimal] = {}
    for t in transactions:
        d = _parse_date(t.get('date'))
        if not d:
            continue
        daily_deltas[d] = daily_deltas.get(d, Decimal(0)) + Decimal(str(t.get('amount') or 0))

    events = sorted(daily_deltas.keys())
    idx = 0
    balance = Decimal(0)
    total = Decimal(0)
    daily_rate = rate / (DAYS_IN_YEAR * PERCENT)
    current = start
    # Включаем транзакции, произошедшие до начала начисления, в начальный баланс
    while idx < len(events) and events[idx] < start:
        balance += daily_deltas[events[idx]]
        idx += 1
    while current <= today:
        # Транзакции в текущий день учитываются в балансе этого дня
        while idx < len(events) and events[idx] <= current:
            balance += daily_deltas[events[idx]]
            idx += 1
        total += balance * daily_rate
        current += timedelta(days=1)
    return int(total.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def projected_income(balance: int, end_date: Optional[str], interest_rate: Optional[Decimal | str]) -> int:
    """Прогнозируемый доход (копейки) до конца срока по простому проценту."""
    rate = _to_decimal_rate(interest_rate)
    if rate is None or rate <= 0:
        return 0
    if balance <= 0:
        return 0
    today = date_cls.today()
    end = _parse_date(end_date)
    if end is None:
        # Бессрочный депозит — прогноз до конца текущего года
        end = date_cls(today.year, 12, 31)
    if end <= today:
        return 0
    days = Decimal((end - today).days)
    result = Decimal(str(balance)) * rate / PERCENT * days / DAYS_IN_YEAR
    return int(result.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def get_savings_stats() -> dict:
    total = get_savings_total()
    accounts = get_all_accounts()
    return {
        'total': total,
        'account_count': len(accounts),
    }
