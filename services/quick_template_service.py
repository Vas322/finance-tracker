from database import get_db


def get_all_templates() -> list:
    """Все шаблоны, отсортированные по sort_order"""
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM quick_templates ORDER BY sort_order ASC, id ASC'
        ).fetchall()
    return [dict(r) for r in rows]


def get_template(template_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM quick_templates WHERE id = ?', (template_id,)
        ).fetchone()
    return dict(row) if row else None


def create_template(name: str, category: str, subcategory: str, amount: int) -> int:
    """Создать шаблон. Возвращает id. Amount в копейках."""
    with get_db() as conn:
        max_order = conn.execute(
            'SELECT COALESCE(MAX(sort_order), 0) FROM quick_templates'
        ).fetchone()[0]
        cursor = conn.execute(
            'INSERT INTO quick_templates (name, category, subcategory, amount, sort_order) VALUES (?, ?, ?, ?, ?)',
            (name, category, subcategory, amount, max_order + 1)
        )
        return cursor.lastrowid


def update_template(template_id: int, name: str, category: str, subcategory: str, amount: int) -> None:
    with get_db() as conn:
        conn.execute(
            'UPDATE quick_templates SET name = ?, category = ?, subcategory = ?, amount = ? WHERE id = ?',
            (name, category, subcategory, amount, template_id)
        )


def delete_template(template_id: int) -> None:
    with get_db() as conn:
        conn.execute('DELETE FROM quick_templates WHERE id = ?', (template_id,))


def reorder_templates(template_ids: list[int]) -> None:
    """Переупорядочить шаблоны. template_ids в новом порядке."""
    with get_db() as conn:
        conn.executemany(
            'UPDATE quick_templates SET sort_order = ? WHERE id = ?',
            enumerate(template_ids)
        )
