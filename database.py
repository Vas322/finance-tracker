import math
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
                amount INTEGER NOT NULL,
                comment TEXT,
                regular_payment_id INTEGER DEFAULT NULL,
                period TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS regular_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount INTEGER NOT NULL,
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
                balance INTEGER NOT NULL,
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
                amount INTEGER NOT NULL,
                UNIQUE(category, month)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vacations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'planned',
                created_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                problem TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                benefit TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '💡 Предложена',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')

    # Миграция существующих БД: добавление regular_payment_id
    try:
        conn.execute('ALTER TABLE operations ADD COLUMN regular_payment_id INTEGER DEFAULT NULL')
    except Exception:
        pass

    # Индексы для операций
    conn.execute('CREATE INDEX IF NOT EXISTS idx_operations_date ON operations(date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_operations_type ON operations(type)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_operations_category ON operations(category)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_operations_period ON operations(period)')

    migrate_amounts_to_cents()

    from seeds import seed_default_user, seed_planned_salary, seed_categories, seed_regular_payments
    seed_default_user()
    seed_planned_salary()
    seed_categories()
    seed_regular_payments()


def migrate_amounts_to_cents():
    with get_db() as conn:
        # Проверка: уже мигрировано (флаг в settings)
        migrated = conn.execute("SELECT value FROM settings WHERE key = 'migrated_to_cents'").fetchone()
        if migrated and migrated['value'] == '1':
            return

        # Если есть суммы > 1 000 000 000 — значит была двойная миграция (×10 000 от рублей)
        # Откатываем лишнюю ×100: делим всё на 100 → получаем копейки
        repair_row = conn.execute("SELECT COUNT(*) as cnt FROM operations WHERE ABS(amount) > 1000000000").fetchone()
        if repair_row and repair_row['cnt'] > 0:
            conn.execute('UPDATE operations SET amount = CAST(ROUND(amount / 100.0) AS INTEGER) WHERE amount IS NOT NULL')
            conn.execute('UPDATE regular_payments SET amount = CAST(ROUND(amount / 100.0) AS INTEGER) WHERE amount IS NOT NULL')
            conn.execute('UPDATE budgets SET amount = CAST(ROUND(amount / 100.0) AS INTEGER) WHERE amount IS NOT NULL')
            conn.execute('UPDATE period_balance SET balance = CAST(ROUND(balance / 100.0) AS INTEGER) WHERE balance IS NOT NULL')
        else:
            # Миграция рублей → копейки
            conn.execute('UPDATE operations SET amount = CAST(ROUND(amount * 100) AS INTEGER) WHERE amount IS NOT NULL')
            conn.execute('UPDATE regular_payments SET amount = CAST(ROUND(amount * 100) AS INTEGER) WHERE amount IS NOT NULL')
            conn.execute('UPDATE budgets SET amount = CAST(ROUND(amount * 100) AS INTEGER) WHERE amount IS NOT NULL')
            conn.execute('UPDATE period_balance SET balance = CAST(ROUND(balance * 100) AS INTEGER) WHERE balance IS NOT NULL')

        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('migrated_to_cents', '1')")
        conn.commit()
        conn.execute('VACUUM')


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