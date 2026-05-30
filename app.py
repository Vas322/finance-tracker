from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
import sqlite3
from calendar import monthrange

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# ==================== НАСТРОЙКИ ====================
SALARY_DAY = 10
ADVANCE_DAY = 25

# ==================== КАТЕГОРИИ ====================
CATEGORIES = {
    "Расход": {
        "Транспорт": ["Такси", "Метро", "Автобус", "Авиа", "ЖД", "Бензин"],
        "Продукты": ["Супермаркет", "Рынок", "Доставка", "Магазин у дома"],
        "Кафе": ["Ресторан", "Кофейня", "Бизнес-ланч", "Фастфуд"],
        "ЖКХ": ["Квартплата", "Электричество", "Вода", "Газ"],
        "Связь": ["Мобильная связь", "Интернет", "VPN"],
        "Развлечения": ["Кино", "Игры", "Концерты", "Подписки"],
        "Здоровье": ["Аптека", "Врачи", "Спорт", "Анализы"],
        "Одежда": ["Обувь", "Одежда", "Аксессуары"],
        "Другое": [""]
    },
    "Доход": {
        "Зарплата": ["Основная", "Премия", "Подработка"],
        "Фриланс": ["Проекты", "Консультации"],
        "Подарки": ["Семье", "Друзьям"],
        "Кэшбэк": ["Банк", "Карта"],
        "Другое": [""]
    }
}


# ==================== БАЗА ДАННЫХ ====================
def get_db():
    conn = sqlite3.connect('finance.db')
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
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                day TEXT DEFAULT '2024-01-01'
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # Добавляем настройку CURRENT_MONEY если её нет
        existing = conn.execute('SELECT COUNT(*) FROM settings WHERE key = "current_money"').fetchone()[0]
        if existing == 0:
            conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('current_money', '45000'))

        # Добавляем примеры регулярных платежей если таблица пустая
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


init_db()

def get_current_money():
    with get_db() as conn:
        result = conn.execute('SELECT value FROM settings WHERE key = "current_money"').fetchone()
        return float(result['value']) if result else 45000

def set_current_money(amount):
    with get_db() as conn:
        conn.execute('UPDATE settings SET value = ? WHERE key = "current_money"', (str(amount),))

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_period(date_str):
    day = datetime.strptime(date_str, '%Y-%m-%d').day
    return "10-24" if 10 <= day <= 24 else "25-09"


def get_next_income_date(today):
    if today.day < SALARY_DAY:
        return date(today.year, today.month, SALARY_DAY)
    elif today.day < ADVANCE_DAY:
        return date(today.year, today.month, ADVANCE_DAY)
    else:
        next_month = today.month + 1
        year = today.year
        if next_month > 12:
            next_month = 1
            year += 1
        return date(year, next_month, SALARY_DAY)


def get_regular_payments_for_period(today, period_start_day, period_end_day):
    """Возвращает сумму платежей, попадающих в период (по дню месяца из даты)"""
    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    total = 0
    for p in payments:
        # Извлекаем день из даты (формат YYYY-MM-DD)
        if p['day'] and '-' in str(p['day']):
            payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
        else:
            payment_day = int(p['day']) if p['day'] else 1

        # Проверяем попадает ли день в период
        if period_start_day <= period_end_day:
            # Обычный период (10-24)
            if period_start_day <= payment_day <= period_end_day:
                total += p['amount']
        else:
            # Период через конец месяца (25-09)
            if payment_day >= period_start_day or payment_day <= period_end_day:
                total += p['amount']
    return total


def get_regular_total_for_month():
    with get_db() as conn:
        result = conn.execute('SELECT SUM(amount) FROM regular_payments').fetchone()[0]
        return result or 0


# ==================== МАРШРУТЫ ====================
@app.route('/')
def index():
    today = date.today()
    current_money = get_current_money()

    with get_db() as conn:
        operations = conn.execute('SELECT * FROM operations ORDER BY date DESC LIMIT 30').fetchall()
        total_income = conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Доход"').fetchone()[0]
        total_expense = conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Расход"').fetchone()[0]
        balance = total_income - total_expense

    # Определяем текущий период
    if 10 <= today.day <= 24:
        period_start, period_end = 10, 24
    else:
        period_start, period_end = 25, 9

    # Регулярные платежи за текущий период
    regular_this_period = get_regular_payments_for_period(today, period_start, period_end)
    regular_total = get_regular_total_for_month()

    # Свободные деньги = текущие деньги + доходы - расходы - платежи за период
    free_money = current_money + total_income - total_expense - regular_this_period

    # Светофор (исправленная логика)
    if free_money < 0:
        traffic_light = "red"
        traffic_text = "⚠️ КАССОВЫЙ РАЗРЫВ!"
    elif free_money < 5000:
        traffic_light = "yellow"
        traffic_text = "⚠️ Осторожно: остаток меньше 5000 ₽"
    else:
        traffic_light = "green"
        traffic_text = "✅ Всё хорошо"

    # Следующее поступление
    next_income = get_next_income_date(today)
    days_to_income = (next_income - today).days

    return render_template('index.html',
                           operations=operations,
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           free_money=free_money,
                           days_to_income=days_to_income,
                           next_income=next_income,
                           traffic_light=traffic_light,
                           traffic_text=traffic_text,
                           regular_total=regular_total,
                           regular_this_period=regular_this_period,
                           current_money=current_money)


@app.route('/update_money', methods=['POST'])
def update_money():
    new_amount = float(request.form['current_money'])
    set_current_money(new_amount)
    flash(f'Денег сейчас: {new_amount:,.0f} ₽', 'success')
    return redirect(url_for('index'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        date_str = request.form['date']
        op_type = request.form['type']
        category = request.form['category']
        subcategory = request.form.get('subcategory', '')
        amount = float(request.form['amount'])
        comment = request.form.get('comment', '')
        period = get_period(date_str)

        with get_db() as conn:
            conn.execute('''
                INSERT INTO operations (date, type, category, subcategory, amount, comment, period)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date_str, op_type, category, subcategory, amount, comment, period))

        flash('Операция добавлена', 'success')
        return redirect(url_for('index'))

    return render_template('add.html', categories=CATEGORIES)


@app.route('/delete/<int:id>')
def delete(id):
    with get_db() as conn:
        conn.execute('DELETE FROM operations WHERE id = ?', (id,))
    flash('Операция удалена', 'success')
    return redirect(url_for('index'))


@app.route('/regular', methods=['GET', 'POST'])
def regular():
    if request.method == 'POST':
        # Обработка добавления
        if 'add_name' in request.form:
            name = request.form['add_name']
            amount = float(request.form['add_amount'])
            day = request.form['add_day']
            with get_db() as conn:
                conn.execute('INSERT INTO regular_payments (name, amount, day) VALUES (?, ?, ?)', (name, amount, day))
            flash('Платёж добавлен', 'success')

        # Обработка удаления
        elif 'delete_id' in request.form:
            pid = int(request.form['delete_id'])
            with get_db() as conn:
                conn.execute('DELETE FROM regular_payments WHERE id = ?', (pid,))
            flash('Платёж удалён', 'success')

        # Обработка обновления сумм и дат
        else:
            with get_db() as conn:
                for key, value in request.form.items():
                    if key.startswith('amount_'):
                        pid = int(key.split('_')[1])
                        amount = float(value)
                        conn.execute('UPDATE regular_payments SET amount = ? WHERE id = ?', (amount, pid))
                    elif key.startswith('day_'):
                        pid = int(key.split('_')[1])
                        day = value
                        conn.execute('UPDATE regular_payments SET day = ? WHERE id = ?', (day, pid))
            flash('Регулярные платежи обновлены', 'success')

        return redirect(url_for('regular'))

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments ORDER BY day, name').fetchall()
    return render_template('regular.html', payments=payments)


@app.route('/edit/<int:id>', methods=['POST'])
def edit_operation(id):
    date_str = request.form['date']
    op_type = request.form['type']
    category = request.form['category']
    subcategory = request.form['subcategory']
    amount = float(request.form['amount'])
    comment = request.form['comment']
    period = get_period(date_str)

    with get_db() as conn:
        conn.execute('''
            UPDATE operations 
            SET date = ?, type = ?, category = ?, subcategory = ?, amount = ?, comment = ?, period = ?
            WHERE id = ?
        ''', (date_str, op_type, category, subcategory, amount, comment, period, id))

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)