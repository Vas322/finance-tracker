from datetime import datetime, date, timedelta
from typing import Optional
from database import get_db
from services.operation_service import get_operations_page, get_totals, get_latest_advance, get_planned_salary


def get_vacation_days(start_date: date, end_date: date) -> int:
    """Возвращает количество календарных дней отпуска"""
    return (end_date - start_date).days + 1


def get_average_daily_earnings() -> float:
    """Рассчитывает средний дневной заработок для отпускных"""
    today = date.today()
    # Берем доходы за последние 12 месяцев
    start_date = today - timedelta(days=365)
    start_str = start_date.strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    with get_db() as conn:
        # Получаем все доходы за последние 12 месяцев
        rows = conn.execute('''
            SELECT amount FROM operations
            WHERE type = 'Доход' AND date >= ? AND date <= ?
            ORDER BY date
        ''', (start_str, today_str)).fetchall()

        if len(rows) == 0:
            # Если нет истории, используем planned_salary
            return get_planned_salary() / 29.3

        total_earnings = sum(row['amount'] for row in rows)

        # Считаем количество месяцев в истории
        months = min(12, (today.year - start_date.year) * 12 + (today.month - start_date.month) + 1)
        if months == 0:
            months = 1

        # Среднемесячный доход
        avg_monthly = total_earnings / months
        # Среднедневной заработок (по правилам: / 29.3)
        return avg_monthly / 29.3


def calculate_vacation_pay(vacation_start: date, vacation_end: date) -> float:
    """Рассчитывает сумму отпускных"""
    days = get_vacation_days(vacation_start, vacation_end)
    avg_daily = get_average_daily_earnings()
    return avg_daily * days * 29.3


def get_upcoming_vacation() -> Optional[dict]:
    """Возвращает ближайший запланированный отпуск"""
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    with get_db() as conn:
        row = conn.execute('''
            SELECT * FROM vacations
            WHERE status = 'planned' AND start_date >= ?
            ORDER BY start_date
            LIMIT 1
        ''', (today_str,)).fetchone()
    if row:
        start_date = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(row['end_date'], '%Y-%m-%d').date()
        return {
            'id': row['id'],
            'start_date': start_date,
            'end_date': end_date,
            'days': get_vacation_days(start_date, end_date),
            'estimated_pay': calculate_vacation_pay(start_date, end_date),
            'status': row['status']
        }
    return None


def add_vacation(start_date: date, end_date: date):
    """Добавляет новый отпуск"""
    with get_db() as conn:
        conn.execute('''
            INSERT INTO vacations (start_date, end_date) VALUES (?, ?)
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))


def get_all_vacations():
    """Получает все отпуска"""
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM vacations ORDER BY start_date DESC').fetchall()
    vacations = []
    for row in rows:
        start_date = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(row['end_date'], '%Y-%m-%d').date()
        vacations.append({
            'id': row['id'],
            'start_date': start_date,
            'end_date': end_date,
            'days': get_vacation_days(start_date, end_date),
            'estimated_pay': calculate_vacation_pay(start_date, end_date),
            'status': row['status'],
            'created_at': row['created_at']
        })
    return vacations