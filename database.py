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
                roi INTEGER NOT NULL DEFAULT 0,
                complexity INTEGER NOT NULL DEFAULT 0,
                risk TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '💡 Предложена',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS regular_skips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regular_payment_id INTEGER NOT NULL,
                cycle_start TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(regular_payment_id, cycle_start)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS quick_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                amount INTEGER NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
        ''')

    # Миграция существующих БД: добавление regular_payment_id
    try:
        conn.execute('ALTER TABLE operations ADD COLUMN regular_payment_id INTEGER DEFAULT NULL')
    except Exception:
        pass

    # Миграция существующих БД: добавление полей ROI, сложность, риск
    try:
        conn.execute("ALTER TABLE ideas ADD COLUMN roi INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE ideas ADD COLUMN complexity INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE ideas ADD COLUMN risk TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass

    migrate_idea_fields()

    # Миграция: добавление email в users
    try:
        conn.execute('ALTER TABLE users ADD COLUMN email TEXT')
    except Exception:
        pass

    # Миграция: начальные значения salary_day / advance_day
    row = conn.execute("SELECT value FROM settings WHERE key = 'salary_day'").fetchone()
    if not row:
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('salary_day', '10')")
    row = conn.execute("SELECT value FROM settings WHERE key = 'advance_day'").fetchone()
    if not row:
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('advance_day', '25')")

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
        return conn.execute('SELECT * FROM users WHERE LOWER(username) = LOWER(?)', (username,)).fetchone()


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


def get_user_by_email(email):
    with get_db() as conn:
        return conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()


def update_user_email(username, email):
    with get_db() as conn:
        conn.execute('UPDATE users SET email = ? WHERE username = ?', (email, username))


def update_user_password(username, password):
    from werkzeug.security import generate_password_hash
    with get_db() as conn:
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE username = ?',
            (generate_password_hash(password), username)
        )


def migrate_idea_fields():
    """Миграция ideas: старый текстовый формат → INTEGER для roi/complexity, TEXT enum для risk"""
    with get_db() as conn:
        migrated = conn.execute("SELECT value FROM settings WHERE key = 'ideas_migrated_v2'").fetchone()
        if migrated and migrated['value'] == '1':
            return

        # Конвертация ROI: ★★★★★ → 5, ★★★★☆ → 4, ★★★☆☆ → 3, ★★☆☆☆ → 2, ★☆☆☆☆ → 1, иначе 0
        conn.execute("""
            UPDATE ideas SET roi = CASE
                WHEN roi LIKE '★★★★★%' THEN 5
                WHEN roi LIKE '★★★★☆%' THEN 4
                WHEN roi LIKE '★★★☆☆%' THEN 3
                WHEN roi LIKE '★★☆☆☆%' THEN 2
                WHEN roi LIKE '★☆☆☆☆%' THEN 1
                ELSE 0
            END
        """)

        # Конвертация Сложности: ★★★★★ → 5, ★★★★☆ → 4, ★★★☆☆ → 3, ★★☆☆☆ → 2, ★☆☆☆☆ → 1, иначе 0
        conn.execute("""
            UPDATE ideas SET complexity = CASE
                WHEN complexity LIKE '★★★★★%' THEN 5
                WHEN complexity LIKE '★★★★☆%' THEN 4
                WHEN complexity LIKE '★★★☆☆%' THEN 3
                WHEN complexity LIKE '★★☆☆☆%' THEN 2
                WHEN complexity LIKE '★☆☆☆☆%' THEN 1
                ELSE 0
            END
        """)

        # Конвертация Риска: текстовые строки → LOW/MEDIUM/HIGH
        conn.execute("""
            UPDATE ideas SET risk = CASE
                WHEN risk LIKE '%Высокий%' THEN 'HIGH'
                WHEN risk LIKE '%Средний%' THEN 'MEDIUM'
                WHEN risk LIKE '%Низкий%' THEN 'LOW'
                WHEN risk = 'LOW' OR risk = 'MEDIUM' OR risk = 'HIGH' THEN risk
                ELSE ''
            END
        """)

        # Исправление типа колонок: TEXT → INTEGER для существующих БД
        try:
            col_info = conn.execute("PRAGMA table_info('ideas')").fetchall()
            col_types = {c['name']: c['type'] for c in col_info}

            for col_name in ('roi', 'complexity'):
                if col_types.get(col_name, '').upper() == 'TEXT':
                    new_name = col_name + '_int'
                    conn.execute(f"ALTER TABLE ideas ADD COLUMN {new_name} INTEGER DEFAULT 0")
                    conn.execute(f"UPDATE ideas SET {new_name} = CAST({col_name} AS INTEGER)")
                    conn.execute(f"ALTER TABLE ideas DROP COLUMN {col_name}")
                    conn.execute(f"ALTER TABLE ideas RENAME COLUMN {new_name} TO {col_name}")
        except Exception:
            # Не все версии SQLite поддерживают DROP COLUMN; это не критично для новых БД
            pass

        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('ideas_migrated_v2', '1')")
        conn.commit()