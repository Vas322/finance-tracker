from typing import Optional
from database import get_db
from utils import get_period


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


def create_account(name: str, target_amount: int = 0, target_date: Optional[str] = None,
                   icon: str = 'bi-piggy-bank', color: str = '#17a2b8') -> int:
    with get_db() as conn:
        max_sort = conn.execute(
            'SELECT COALESCE(MAX(sort_order), 0) + 1 FROM savings_accounts'
        ).fetchone()[0]
        cursor = conn.execute('''
            INSERT INTO savings_accounts (name, target_amount, target_date, icon, color, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, target_amount, target_date, icon, color, max_sort))
    return cursor.lastrowid


def update_account(account_id: int, **kwargs):
    allowed_fields = {'name', 'target_amount', 'target_date', 'icon', 'color', 'is_active', 'sort_order'}
    fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
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


def get_savings_stats() -> dict:
    total = get_savings_total()
    accounts = get_all_accounts()
    return {
        'total': total,
        'account_count': len(accounts),
    }
