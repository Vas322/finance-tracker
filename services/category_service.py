from database import get_db


def get_income_categories():
    income_cats = {}
    with get_db() as conn:
        income_main = conn.execute(
            'SELECT * FROM categories WHERE parent_id IS NULL AND type = "Доход" ORDER BY name'
        ).fetchall()
        for cat in income_main:
            subcats = conn.execute(
                'SELECT name FROM categories WHERE parent_id = ? ORDER BY name', (cat['id'],)
            ).fetchall()
            income_cats[cat['name']] = [s['name'] for s in subcats]
    return income_cats


def get_expense_categories():
    expense_cats = {}
    with get_db() as conn:
        expense_main = conn.execute(
            'SELECT * FROM categories WHERE parent_id IS NULL AND type = "Расход" ORDER BY name'
        ).fetchall()
        for cat in expense_main:
            subcats = conn.execute(
                'SELECT name FROM categories WHERE parent_id = ? ORDER BY name', (cat['id'],)
            ).fetchall()
            expense_cats[cat['name']] = [s['name'] for s in subcats]
    return expense_cats


def get_all_category_names():
    with get_db() as conn:
        return [row['name'] for row in conn.execute(
            'SELECT DISTINCT name FROM categories WHERE parent_id IS NULL ORDER BY name'
        ).fetchall()]
