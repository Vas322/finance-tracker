from datetime import datetime
from typing import Optional
from database import get_db


def _generate_code() -> str:
    with get_db() as conn:
        row = conn.execute('SELECT MAX(id) as max_id FROM ideas').fetchone()
        next_id = (row[0] or 0) + 1
    return f'P-{next_id:03d}'


def get_all_ideas():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM ideas ORDER BY created_at DESC').fetchall()
    return [dict(r) for r in rows]


def get_idea(id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute('SELECT * FROM ideas WHERE id = ?', (id,)).fetchone()
    return dict(row) if row else None


def create_idea(title: str, problem: str, description: str, benefit: str):
    code = _generate_code()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        conn.execute(
            'INSERT INTO ideas (code, title, problem, description, benefit, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (code, title, problem, description, benefit, now, now)
        )


def update_idea(id: int, title: str, problem: str, description: str, benefit: str, status: str):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        conn.execute(
            'UPDATE ideas SET title = ?, problem = ?, description = ?, benefit = ?, status = ?, updated_at = ? WHERE id = ?',
            (title, problem, description, benefit, status, now, id)
        )


def delete_idea(id: int):
    with get_db() as conn:
        conn.execute('DELETE FROM ideas WHERE id = ?', (id,))


def get_idea_stats() -> dict:
    with get_db() as conn:
        rows = conn.execute('SELECT status, COUNT(*) as cnt FROM ideas GROUP BY status').fetchall()
    stats = {}
    for r in rows:
        stats[r['status']] = r['cnt']
    return stats
