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
                interval TEXT DEFAULT 'monthly',
                comment TEXT DEFAULT ''
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

        # Таблица остатков по периодам
        conn.execute('''
            CREATE TABLE IF NOT EXISTS period_balance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                start_date TEXT NOT NULL,
                balance REAL NOT NULL,
                UNIQUE(period, start_date)
            )
        ''')

        # Плановая зарплата (если нет)
        existing_plan = conn.execute('SELECT COUNT(*) FROM settings WHERE key = "planned_salary"').fetchone()[0]
        if existing_plan == 0:
            conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('planned_salary', '185000'))

        # Заполняем категории, если таблица пустая
        existing_cats = conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
        if existing_cats == 0:
            from config import CATEGORIES
            for cat_type, categories in CATEGORIES.items():
                for cat_name, subcats in categories.items():
                    cursor = conn.execute(
                        'INSERT INTO categories (type, name) VALUES (?, ?)',
                        (cat_type, cat_name)
                    )
                    parent_id = cursor.lastrowid
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


def get_period_balance(period, start_date):
    """Получить остаток на начало периода"""
    with get_db() as conn:
        result = conn.execute('SELECT balance FROM period_balance WHERE period = ? AND start_date = ?',
                              (period, start_date)).fetchone()
        return result['balance'] if result else None


def set_period_balance(period, start_date, balance):
    """Сохранить остаток на начало периода"""
    with get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO period_balance (period, start_date, balance)
            VALUES (?, ?, ?)
        ''', (period, start_date, balance))