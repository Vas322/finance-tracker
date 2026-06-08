import os
from database import get_db


def seed_default_user():
    with get_db() as conn:
        existing = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if existing == 0:
            from werkzeug.security import generate_password_hash
            default_password = os.environ.get('APP_PASSWORD', '12345')
            conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                ('admin', generate_password_hash(default_password))
            )


def seed_planned_salary():
    with get_db() as conn:
        existing = conn.execute('SELECT COUNT(*) FROM settings WHERE key = "planned_salary"').fetchone()[0]
        if existing == 0:
            conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('planned_salary', '185000'))


def seed_categories():
    with get_db() as conn:
        existing = conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
        if existing == 0:
            from config import CATEGORIES
            for cat_type, categories in CATEGORIES.items():
                for cat_name, subcats in categories.items():
                    cursor = conn.execute(
                        'INSERT INTO categories (type, name) VALUES (?, ?)', (cat_type, cat_name)
                    )
                    parent_id = cursor.lastrowid
                    for subcat in subcats:
                        if subcat:
                            conn.execute(
                                'INSERT INTO categories (type, name, parent_id) VALUES (?, ?, ?)',
                                (cat_type, subcat, parent_id)
                            )


def seed_regular_payments():
    with get_db() as conn:
        existing = conn.execute('SELECT COUNT(*) FROM regular_payments').fetchone()[0]
        if existing == 0:
            examples = [
                (35000, "2024-01-05", "ЖКХ", "Квартплата", "monthly", ""),
                (8000, "2024-01-15", "ЖКХ", "Электричество", "monthly", ""),
                (900, "2024-01-20", "Связь", "Интернет", "monthly", ""),
                (300, "2024-01-01", "Связь", "VPN", "monthly", ""),
                (600, "2024-01-10", "Связь", "Мобильная связь", "monthly", ""),
                (500, "2024-01-25", "Подписки", "", "monthly", ""),
            ]
            for amount, day, category, subcategory, interval, comment in examples:
                conn.execute('''
                    INSERT INTO regular_payments (amount, day, category, subcategory, interval, comment)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (amount, day, category, subcategory, interval, comment))
