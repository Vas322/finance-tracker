from flask import render_template, request
from database import get_db, get_current_money
from utils import get_next_income_date, get_regular_payments_for_period, get_regular_total_for_month, \
    apply_regular_payments, get_unpaid_regular_payments, get_regular_payments_until_date, \
    get_regular_payments_after_date, get_regular_payments_for_month, get_paid_regular_payments_this_month, \
    get_planning_data
from datetime import date


def register_routes(app):
    @app.route('/')
    def index():
        # Автоматически добавляем регулярные платежи
        apply_regular_payments()

        today = date.today()
        current_money = get_current_money()

        # Получаем параметры фильтров из URL
        period_filter = request.args.get('period', '')
        type_filter = request.args.get('type', '')
        category_filter = request.args.get('category', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        # Базовый запрос
        query = 'SELECT * FROM operations WHERE 1=1'
        params = []

        if period_filter:
            query += ' AND period = ?'
            params.append(period_filter)

        if type_filter:
            query += ' AND type = ?'
            params.append(type_filter)

        if category_filter:
            query += ' AND category = ?'
            params.append(category_filter)

        if date_from:
            query += ' AND date >= ?'
            params.append(date_from)

        if date_to:
            query += ' AND date <= ?'
            params.append(date_to)

        query += ' ORDER BY date DESC LIMIT 100'

        with get_db() as conn:
            operations = conn.execute(query, params).fetchall()

            # Все категории для выпадающего списка
            all_categories = [row['name'] for row in conn.execute(
                'SELECT DISTINCT name FROM categories WHERE parent_id IS NULL ORDER BY name').fetchall()]

            # Доходы и расходы (без фильтра по периоду, для общей статистики)
            total_income = \
            conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Доход"').fetchone()[0]
            total_expense = \
            conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Расход"').fetchone()[0]
            balance = total_income - total_expense

            # Расчёт ожидаемого остатка зарплаты
            planned_salary_row = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()
            planned_salary = float(planned_salary_row['value']) if planned_salary_row else 185000

            # Берём последний аванс по дате
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

            # Категории для модального окна добавления
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

        # Определяем текущий период
        if 10 <= today.day <= 24:
            period_start, period_end = 10, 24
        else:
            period_start, period_end = 25, 9

        next_income = get_next_income_date(today)
        days_to_income = (next_income - today).days

        # Новая логика расчёта свободных денег
        regular_this_period = get_regular_payments_for_period(today, period_start, period_end)
        regular_total = get_regular_total_for_month()

        # 1. Неоплаченные регулярные платежи (которые уже прошли по дате)
        unpaid_regular = get_unpaid_regular_payments(today, period_start, period_end)

        # 2. Свободные деньги сейчас (реальные)
        free_money_now = current_money + total_income - total_expense - unpaid_regular

        # 3. Ожидаемое поступление (зарплата после вычета аванса)
        if real_advance > 0:
            expected_income = planned_salary - real_advance
        else:
            expected_income = planned_salary

        # 4. Будущие регулярные платежи до следующего поступления
        future_regular = get_regular_payments_until_date(today, next_income)

        # 5. Сколько можно потратить сегодня с учётом будущих регулярных платежей
        can_spend_today = free_money_now - future_regular

        # 6. Регулярные платежи после получения зарплаты
        regular_after_income = get_regular_payments_after_date(today, next_income)

        # 7. Данные для планирования бюджета
        regular_total_month = get_regular_payments_for_month()
        paid_regular = get_paid_regular_payments_this_month()
        planning = get_planning_data(planned_salary, real_advance, regular_total_month, paid_regular)

        if can_spend_today < 0:
            spend_warning = "⚠️ Внимание! Денег не хватит на регулярные платежи!"
        else:
            spend_warning = ""

        # Светофор (смотрим на свободные деньги сейчас)
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
                               regular_total=regular_total,
                               regular_this_period=regular_this_period,
                               current_money=current_money,
                               all_categories=all_categories,
                               salary_remainder_text=salary_remainder_text,
                               salary_remainder_note=salary_remainder_note,
                               income_categories=income_cats,
                               expense_categories=expense_cats,
                               planning=planning,
                               regular_total_month=regular_total_month)

    @app.route('/analytics')
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