import sqlite3


def get_db():
    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        # Таблица операций
        conn.execute('''
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                amount REAL NOT NULL,
                comment TEXT,
                period TEXT
            )
        ''')

        # Таблица регулярных платежей
        conn.execute('''
            CREATE TABLE IF NOT EXISTS regular_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                day TEXT DEFAULT '2024-01-01',
                category TEXT DEFAULT '',
                subcategory TEXT DEFAULT '',
                interval TEXT DEFAULT 'monthly'
            )
        ''')

        # Таблица настроек
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # Таблица категорий
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                parent_id INTEGER DEFAULT NULL,
                UNIQUE(type, name, parent_id)
            )
        ''')

        # Начальный остаток (если нет)
        existing = conn.execute('SELECT COUNT(*) FROM settings WHERE key = "current_money"').fetchone()[0]
        if existing == 0:
            conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('current_money', '45000'))

        # Настройки доходов (если нет)
        existing_plan = conn.execute('SELECT COUNT(*) FROM settings WHERE key = "planned_salary"').fetchone()[0]
        if existing_plan == 0:
            conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('planned_salary', '185000'))

        # Заполняем категории, если таблица пустая
        existing_cats = conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
        if existing_cats == 0:
            from config import CATEGORIES
            for cat_type, categories in CATEGORIES.items():
                for cat_name, subcats in categories.items():
                    # Добавляем основную категорию
                    cursor = conn.execute(
                        'INSERT INTO categories (type, name) VALUES (?, ?)',
                        (cat_type, cat_name)
                    )
                    parent_id = cursor.lastrowid
                    # Добавляем подкатегории
                    for subcat in subcats:
                        if subcat:
                            conn.execute(
                                'INSERT INTO categories (type, name, parent_id) VALUES (?, ?, ?)',
                                (cat_type, subcat, parent_id)
                            )

        # Примеры регулярных платежей (если таблица пустая)
        existing_payments = conn.execute('SELECT COUNT(*) FROM regular_payments').fetchone()[0]
        if existing_payments == 0:
            examples = [
                (35000, "2024-01-05", "ЖКХ", "Квартплата", "monthly"),
                (8000, "2024-01-15", "ЖКХ", "Электричество", "monthly"),
                (900, "2024-01-20", "Связь", "Интернет", "monthly"),
                (300, "2024-01-01", "Связь", "VPN", "monthly"),
                (600, "2024-01-10", "Связь", "Мобильная связь", "monthly"),
                (500, "2024-01-25", "Подписки", "", "monthly"),
            ]
            for amount, day, category, subcategory, interval in examples:
                conn.execute('''
                    INSERT INTO regular_payments (amount, day, category, subcategory, interval)
                    VALUES (?, ?, ?, ?, ?)
                ''', (amount, day, category, subcategory, interval))


def get_current_money():
    with get_db() as conn:
        result = conn.execute('SELECT value FROM settings WHERE key = "current_money"').fetchone()
        return float(result['value']) if result else 45000


def set_current_money(amount):
    with get_db() as conn:
        conn.execute('UPDATE settings SET value = ? WHERE key = "current_money"', (str(amount),))
