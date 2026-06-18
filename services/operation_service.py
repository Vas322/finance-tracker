from database import get_db
from config import Config


def get_operations_page(
    page: int = 1,
    per_page: int = 50,
    period_filter: str = '',
    type_filter: str = '',
    category_filter: str = '',
    date_from: str = '',
    date_to: str = '',
):
    where_clause = ''
    where_params = []
    if period_filter:
        where_clause += ' AND period = ?'
        where_params.append(period_filter)
    if type_filter:
        where_clause += ' AND type = ?'
        where_params.append(type_filter)
    if category_filter:
        where_clause += ' AND category = ?'
        where_params.append(category_filter)
    if date_from:
        where_clause += ' AND date >= ?'
        where_params.append(date_from)
    if date_to:
        where_clause += ' AND date <= ?'
        where_params.append(date_to)
    with get_db() as conn:
        total_count = conn.execute(
            'SELECT COUNT(*) FROM operations WHERE 1=1' + where_clause, where_params
        ).fetchone()[0]
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        page = min(page, total_pages)
        offset = (page - 1) * per_page
        operations = conn.execute(
            'SELECT * FROM operations WHERE 1=1' + where_clause + ' ORDER BY date DESC LIMIT ? OFFSET ?',
            where_params + [per_page, offset]
        ).fetchall()
    return operations, total_pages, page


def get_totals():
    with get_db() as conn:
        total_income = conn.execute(
            'SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Доход"'
        ).fetchone()[0]
        total_expense = conn.execute(
            'SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Расход"'
        ).fetchone()[0]
        total_expense_without_regulars = conn.execute('''
            SELECT COALESCE(SUM(o.amount), 0) FROM operations o
            WHERE o.type = 'Расход'
            AND NOT EXISTS (
                SELECT 1 FROM regular_payments r
                WHERE r.category = o.category
                AND (r.subcategory = o.subcategory OR (r.subcategory IS NULL AND o.subcategory IS NULL))
            )
        ''').fetchone()[0]
    return total_income, total_expense, total_income - total_expense, total_expense_without_regulars


def get_latest_advance():
    with get_db() as conn:
        advance_row = conn.execute('''
            SELECT amount FROM operations
            WHERE type = 'Доход' AND category = 'Зарплата' AND subcategory = 'Аванс'
            ORDER BY date DESC LIMIT 1
        ''').fetchone()
    return advance_row['amount'] if advance_row else 0


def get_planned_salary():
    with get_db() as conn:
        row = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()
    return float(row['value']) if row else Config.DEFAULT_PLANNED_SALARY
