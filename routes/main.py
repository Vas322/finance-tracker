from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from utils import get_next_income_date, get_regular_total, apply_regular_payments, \
    get_unpaid_regular_payments, get_regular_payments_until_date, get_regular_payments_after_date, \
    get_regular_payments_for_period, get_paid_regular_payments_this_month, get_planning_data, \
    get_expenses_for_period, update_period_balance, get_period_dates, get_period, update_current_period_balance, \
    get_due_regular_payments
from datetime import date

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    today = date.today()

    period_filter = request.args.get('period', '')
    type_filter = request.args.get('type', '')
    category_filter = request.args.get('category', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    page = int(request.args.get('page', 1))
    per_page = 50

    where_clause = ''
    where_params = []

    if period_filter:
        where_clause += ' AND period = ?'
        where_params.append(period_filter)

    if type_filter:
        where_clause += ' AND type = ?'
        where_params.append(type_filter)

    if category_filter:
        where_clause += ' AND category = ?'
        where_params.append(category_filter)

    if date_from:
        where_clause += ' AND date >= ?'
        where_params.append(date_from)

    if date_to:
        where_clause += ' AND date <= ?'
        where_params.append(date_to)

    with get_db() as conn:
        total_count = conn.execute(
            'SELECT COUNT(*) FROM operations WHERE 1=1' + where_clause, where_params
        ).fetchone()[0]

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        page = min(page, total_pages)
        offset = (page - 1) * per_page

        operations = conn.execute(
            'SELECT * FROM operations WHERE 1=1' + where_clause + ' ORDER BY date DESC LIMIT ? OFFSET ?',
            where_params + [per_page, offset]
        ).fetchall()

        all_categories = [row['name'] for row in conn.execute(
            'SELECT DISTINCT name FROM categories WHERE parent_id IS NULL ORDER BY name').fetchall()]

        total_income = \
        conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Доход"').fetchone()[0]
        total_expense = \
        conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Расход"').fetchone()[0]
        balance = total_income - total_expense

        planned_salary_row = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()
        planned_salary = float(planned_salary_row['value']) if planned_salary_row else 185000

        advance_row = conn.execute('''
            SELECT amount
            FROM operations
            WHERE type = 'Доход'
            AND category = 'Зарплата'
            AND subcategory = 'Аванс'
            ORDER BY date DESC
            LIMIT 1
        ''').fetchone()

        real_advance = advance_row['amount'] if advance_row else 0

        if real_advance > 0:
            expected_remainder = planned_salary - real_advance
            salary_remainder_text = f"{expected_remainder:,.0f} ₽".replace(",", " ")
            salary_remainder_note = f"(Аванс: {real_advance:,.0f} ₽)".replace(",", " ")
        else:
            expected_remainder = planned_salary
            salary_remainder_text = f"{expected_remainder:,.0f} ₽".replace(",", " ")
            salary_remainder_note = "⚠️ Аванс ещё не внесён"

        income_cats = {}
        expense_cats = {}

        income_main = conn.execute(
            'SELECT * FROM categories WHERE parent_id IS NULL AND type = "Доход" ORDER BY name').fetchall()
        for cat in income_main:
            subcats = conn.execute('SELECT name FROM categories WHERE parent_id = ? ORDER BY name',
                                   (cat['id'],)).fetchall()
            income_cats[cat['name']] = [s['name'] for s in subcats]

        expense_main = conn.execute(
            'SELECT * FROM categories WHERE parent_id IS NULL AND type = "Расход" ORDER BY name').fetchall()
        for cat in expense_main:
            subcats = conn.execute('SELECT name FROM categories WHERE parent_id = ? ORDER BY name',
                                   (cat['id'],)).fetchall()
            expense_cats[cat['name']] = [s['name'] for s in subcats]

    if 10 <= today.day <= 24:
        period_start, period_end = 10, 24
    else:
        period_start, period_end = 25, 9

    next_income = get_next_income_date(today)
    days_to_income = (next_income - today).days

    period_start_date, period_end_date = get_period_dates(today)

    period_balance = update_period_balance(today)

    expenses_this_period = get_expenses_for_period(period_start_date, period_end_date)

    regular_total_month = get_regular_total(period_type='month')
    paid_regular = get_paid_regular_payments_this_month()
    planning = get_planning_data(planned_salary, real_advance, regular_total_month, paid_regular)

    if real_advance > 0 and 25 <= today.day <= 31:
        advance_for_period = real_advance
        saved_from_advance = planning['need_to_save_from_advance']
    else:
        advance_for_period = planning['advance']
        saved_from_advance = planning['need_to_save_from_advance']

    can_spend_today = (advance_for_period - saved_from_advance) + period_balance - expenses_this_period

    regular_this_period = get_regular_payments_for_period(today, period_start, period_end)

    unpaid_regular = get_unpaid_regular_payments(today, period_start, period_end)

    if real_advance > 0:
        expected_income = planned_salary - real_advance
    else:
        expected_income = planned_salary

    future_regular = get_regular_payments_until_date(today, next_income)
    regular_after_income = get_regular_payments_after_date(today, next_income)

    if can_spend_today < 0:
        spend_warning = "⚠️ Внимание! Денег не хватит на регулярные платежи!"
    else:
        spend_warning = ""

    free_money_now = period_balance + total_income - total_expense - unpaid_regular

    due_payments = get_due_regular_payments(today)

    if free_money_now < 0:
        traffic_light = "red"
        traffic_text = "⚠️ КАССОВЫЙ РАЗРЫВ!"
    elif free_money_now < 5000:
        traffic_light = "yellow"
        traffic_text = "⚠️ Осторожно: остаток меньше 5000 ₽"
    else:
        traffic_light = "green"
        traffic_text = "✅ Всё хорошо"

    return render_template('index.html',
                           operations=operations,
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           free_money_now=free_money_now,
                           expected_income=expected_income,
                           future_regular=future_regular,
                           regular_after_income=regular_after_income,
                           can_spend_today=can_spend_today,
                           spend_warning=spend_warning,
                           days_to_income=days_to_income,
                           next_income=next_income,
                           traffic_light=traffic_light,
                           traffic_text=traffic_text,
                           regular_this_period=regular_this_period,
                           period_balance=period_balance,
                           all_categories=all_categories,
                           salary_remainder_text=salary_remainder_text,
                           salary_remainder_note=salary_remainder_note,
                           income_categories=income_cats,
                           expense_categories=expense_cats,
                           planning=planning,
                           regular_total_month=regular_total_month,
                           due_payments=due_payments,
                           page=page, total_pages=total_pages)


@bp.route('/apply_regular', methods=['POST'])
def apply_regular():
    apply_regular_payments()
    flash('Регулярные платежи применены', 'success')
    return redirect(url_for('main.index'))


@bp.route('/apply_regular/<int:payment_id>', methods=['POST'])
def apply_single_regular(payment_id):
    from database import get_db
    from datetime import date, datetime
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    today_day = today.day

    with get_db() as conn:
        p = conn.execute('SELECT * FROM regular_payments WHERE id = ?', (payment_id,)).fetchone()
        if p and p['category']:
            existing = conn.execute(
                'SELECT id FROM operations WHERE date = ? AND category = ? AND subcategory = ? AND amount = ? AND type = \'Расход\'',
                (today_str, p['category'], p['subcategory'], p['amount'])
            ).fetchone()
            if not existing:
                period = "10-24" if 10 <= today_day <= 24 else "25-09"
                conn.execute(
                    'INSERT INTO operations (date, type, category, subcategory, amount, comment, period) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (today_str, 'Расход', p['category'], p['subcategory'], p['amount'],
                     f'Авто: {p["interval"]}', period)
                )
                flash(f'Платёж "{p["category"]}" применён', 'success')
            else:
                flash(f'Платёж "{p["category"]}" уже был применён', 'info')

    return redirect(url_for('main.index'))


@bp.route('/update_money', methods=['POST'])
def update_money():
    new_amount = float(request.form['current_money'])
    today = date.today()
    update_current_period_balance(today, new_amount)
    flash(f'Начальный остаток: {new_amount:,.0f} ₽', 'success')
    return redirect(url_for('main.index'))


@bp.route('/analytics')
def analytics():
    with get_db() as conn:
        expense_by_category_raw = conn.execute('''
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Расход'
            GROUP BY category
            ORDER BY total DESC
        ''').fetchall()

        expense_by_category = [{'category': row['category'], 'total': row['total']} for row in
                               expense_by_category_raw]

        total_expense = \
        conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Расход"').fetchone()[0]

    return render_template('analytics.html',
                           expense_by_category=expense_by_category,
                           total_expense=total_expense)


@bp.route('/budget_planning')
def budget_planning():
    from database import get_db
    from utils import get_regular_total, get_paid_regular_payments_this_month, get_planning_data
    from datetime import date

    today = date.today()
    months_ru = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    month_name = months_ru[today.month]

    with get_db() as conn:
        planned_salary_row = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()
        planned_salary = float(planned_salary_row['value']) if planned_salary_row else 185000

        advance_row = conn.execute('''
            SELECT amount
            FROM operations
            WHERE type = 'Доход'
            AND category = 'Зарплата'
            AND subcategory = 'Аванс'
            ORDER BY date DESC
            LIMIT 1
        ''').fetchone()
        real_advance = advance_row['amount'] if advance_row else 0

    regular_total_month = get_regular_total(period_type='month')
    paid_regular = get_paid_regular_payments_this_month()
    planning = get_planning_data(planned_salary, real_advance, regular_total_month, paid_regular)

    return render_template('budget_planning.html',
                           planning=planning,
                           regular_total_month=regular_total_month,
                           month_name=month_name)
