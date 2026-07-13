from datetime import datetime
from typing import Optional
from database import get_db


def _ensure_int_fields(idea: dict) -> dict:
    """Преобразует roi и complexity в int, если они пришли как str из TEXT-колонок"""
    if idea:
        try:
            idea['roi'] = int(idea['roi'])
        except (ValueError, TypeError):
            idea['roi'] = 0
        try:
            idea['complexity'] = int(idea['complexity'])
        except (ValueError, TypeError):
            idea['complexity'] = 0
    return idea


def _generate_code() -> str:
    with get_db() as conn:
        row = conn.execute('SELECT MAX(id) as max_id FROM ideas').fetchone()
        next_id = (row[0] or 0) + 1
    return f'P-{next_id:03d}'


def get_all_ideas() -> list:
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM ideas ORDER BY created_at DESC').fetchall()
    return [_ensure_int_fields(dict(r)) for r in rows]


def get_idea(id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute('SELECT * FROM ideas WHERE id = ?', (id,)).fetchone()
    return _ensure_int_fields(dict(row)) if row else None


def create_idea(title: str, problem: str, description: str, benefit: str, roi: int = 0, complexity: int = 0, risk: str = '') -> None:
    code = _generate_code()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        conn.execute(
            'INSERT INTO ideas (code, title, problem, description, benefit, roi, complexity, risk, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (code, title, problem, description, benefit, roi, complexity, risk, now, now)
        )


def update_idea(id: int, title: str, problem: str, description: str, benefit: str, status: str, roi: int = 0, complexity: int = 0, risk: str = '') -> None:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        conn.execute(
            'UPDATE ideas SET title = ?, problem = ?, description = ?, benefit = ?, roi = ?, complexity = ?, risk = ?, status = ?, updated_at = ? WHERE id = ?',
            (title, problem, description, benefit, roi, complexity, risk, status, now, id)
        )


def delete_idea(id: int) -> None:
    with get_db() as conn:
        conn.execute('DELETE FROM ideas WHERE id = ?', (id,))


def get_idea_stats() -> dict:
    with get_db() as conn:
        rows = conn.execute('SELECT status, COUNT(*) as cnt FROM ideas GROUP BY status').fetchall()
    stats = {}
    for r in rows:
        stats[r['status']] = r['cnt']
    return stats
