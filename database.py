import sqlite3
from config import Config

DB_PATH = Config.DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                parent_id INTEGER DEFAULT NULL,
                UNIQUE(type, name, parent_id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS period_balance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                start_date TEXT NOT NULL,
                balance REAL NOT NULL,
                UNIQUE(period, start_date)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                amount REAL NOT NULL,
                UNIQUE(category, month)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vacations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'planned', -- planned, taken, cancelled
                created_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vacations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'planned', -- planned, taken, cancelled
                created_at TEXT DEFAULT (datetime('now'))
            )
        ''')

    from seeds import seed_default_user, seed_planned_salary, seed_categories, seed_regular_payments
    seed_default_user()
    seed_planned_salary()
    seed_categories()
    seed_regular_payments()


def backup_db():
    import shutil, os, glob
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    src = DB_PATH if os.path.isabs(DB_PATH) else os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_PATH)

    if os.path.exists(src):
        dst = os.path.join(backup_dir, f'finance_{timestamp}.db')
        shutil.copy2(src, dst)

    # Храним максимум 30 бэкапов
    backups = sorted(glob.glob(os.path.join(backup_dir, 'finance_*.db')))
    while len(backups) > 30:
        os.remove(backups.pop(0))


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


def get_user(username):
    with get_db() as conn:
        return conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()


def create_user(username, password):
    from werkzeug.security import generate_password_hash
    with get_db() as conn:
        try:
            conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            return True
        except Exception:
            return False