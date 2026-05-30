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
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                day TEXT DEFAULT '2024-01-01'
            )
        ''')

        # Таблица настроек
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # Начальный остаток (если нет)
        existing = conn.execute('SELECT COUNT(*) FROM settings WHERE key = "current_money"').fetchone()[0]
        if existing == 0:
            conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('current_money', '45000'))

        # Примеры регулярных платежей (если таблица пустая)
        existing_payments = conn.execute('SELECT COUNT(*) FROM regular_payments').fetchone()[0]
        if existing_payments == 0:
            examples = [
                ("Ипотека", 35000, "2024-01-05"),
                ("Потребительский", 8000, "2024-01-15"),
                ("Интернет", 900, "2024-01-20"),
                ("VPN", 300, "2024-01-01"),
                ("Связь", 600, "2024-01-10"),
                ("Подписки", 500, "2024-01-25"),
            ]
            for name, amount, day in examples:
                conn.execute('INSERT INTO regular_payments (name, amount, day) VALUES (?, ?, ?)', (name, amount, day))


def get_current_money():
    with get_db() as conn:
        result = conn.execute('SELECT value FROM settings WHERE key = "current_money"').fetchone()
        return float(result['value']) if result else 45000


def set_current_money(amount):
    with get_db() as conn:
        conn.execute('UPDATE settings SET value = ? WHERE key = "current_money"', (str(amount),))