from database import get_db


def _get_categories_by_type(op_type: str):
    with get_db() as conn:
        rows = conn.execute('''
            SELECT p.id, p.name as parent, s.name as sub
            FROM categories p
            LEFT JOIN categories s ON s.parent_id = p.id
            WHERE p.parent_id IS NULL AND p.type = ?
            ORDER BY p.name, s.name
        ''', (op_type,)).fetchall()
    result = {}
    for row in rows:
        if row['id'] not in result:
            result[row['id']] = {'parent': row['parent'], 'subs': []}
        if row['sub']:
            result[row['id']]['subs'].append(row['sub'])
    return {v['parent']: v['subs'] for v in result.values()}


def get_income_categories():
    return _get_categories_by_type('Доход')


def get_expense_categories():
    return _get_categories_by_type('Расход')


def get_all_category_names():
    with get_db() as conn:
        return [row['name'] for row in conn.execute(
            'SELECT DISTINCT name FROM categories WHERE parent_id IS NULL ORDER BY name'
        ).fetchall()]
