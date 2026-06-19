from datetime import datetime, date
from typing import Optional
from database import get_db


def get_vacation_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def _sync_vacation_status(row, conn):
    today = date.today()
    current = row['status']
    start_date = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(row['end_date'], '%Y-%m-%d').date()

    new = None
    if current in ('planned', 'ongoing'):
        if end_date < today:
            new = 'completed'
        elif current == 'planned' and start_date <= today <= end_date:
            new = 'ongoing'

    if new:
        conn.execute('UPDATE vacations SET status = ? WHERE id = ?', (new, row['id']))
        return new
    return current


def get_yearly_vacation_days(year: int) -> int:
    from database import get_db
    total = 0
    with get_db() as conn:
        rows = conn.execute(
            'SELECT start_date, end_date, status FROM vacations'
        ).fetchall()
        for row in rows:
            status = _sync_vacation_status(row, conn)
            s = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
            e = datetime.strptime(row['end_date'], '%Y-%m-%d').date()
            if s.year <= year <= e.year:
                start = s if s.year >= year else date(year, 1, 1)
                end = e if e.year <= year else date(year, 12, 31)
                total += (end - start).days + 1
    return total


def get_upcoming_vacation() -> Optional[dict]:
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    with get_db() as conn:
        row = conn.execute('''
            SELECT * FROM vacations
            WHERE status IN ('planned', 'ongoing') AND start_date >= ?
            ORDER BY start_date
            LIMIT 1
        ''', (today_str,)).fetchone()
    if row:
        start_date = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(row['end_date'], '%Y-%m-%d').date()
        status = _sync_vacation_status(row, conn)
        return {
            'id': row['id'],
            'start_date': start_date,
            'end_date': end_date,
            'days': get_vacation_days(start_date, end_date),
            'status': status
        }
    return None


def add_vacation(start_date: date, end_date: date):
    with get_db() as conn:
        conn.execute('''
            INSERT INTO vacations (start_date, end_date) VALUES (?, ?)
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))


def get_all_vacations():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM vacations ORDER BY start_date DESC').fetchall()
        vacations = []
        for row in rows:
            start_date = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(row['end_date'], '%Y-%m-%d').date()
            status = _sync_vacation_status(row, conn)
            vacations.append({
                'id': row['id'],
                'start_date': start_date,
                'end_date': end_date,
                'days': get_vacation_days(start_date, end_date),
                'status': status,
                'created_at': row['created_at']
            })
    return vacations
