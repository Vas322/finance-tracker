from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from datetime import date

from services.period_service import get_next_income_date, get_period_dates, get_period
from services.regular_service import (
    get_regular_total, apply_regular_payments,
    get_unpaid_regular_payments, get_regular_payments_until_date,
    get_regular_payments_after_date, get_regular_payments_for_period,
    get_paid_regular_payments_this_month, get_due_regular_payments,
)
from services.planning_service import get_planning_data
from services.balance_service import (
    get_expenses_for_period, get_income_for_period,
    update_period_balance, update_current_period_balance,
)
from services.operation_service import get_operations_page, get_totals, get_latest_advance, get_planned_salary
from services.category_service import get_all_category_names, get_income_categories, get_expense_categories
from services.vacation_service import get_upcoming_vacation

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

    operations, total_pages, page = get_operations_page(
        page=page, per_page=50,
        period_filter=period_filter, type_filter=type_filter,
        category_filter=category_filter, date_from=date_from, date_to=date_to,
    )

    total_income, total_expense, balance = get_totals()
    planned_salary = get_planned_salary()
    real_advance = get_latest_advance()

    if 10 <= today.day <= 24:
        period_start, period_end = 10, 24
    else:
        period_start, period_end = 25, 9

    days_to_income = (get_next_income_date(today) - today).days
    period_start_date, period_end_date = get_period_dates(today)
    period_balance = update_period_balance(today)
    expenses_this_period = get_expenses_for_period(period_start_date, period_end_date)
    income_this_period = get_income_for_period(period_start_date, period_end_date)

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

    expected_income = planned_salary - real_advance if real_advance > 0 else planned_salary
    next_income = get_next_income_date(today)
    upcoming_vacation = get_upcoming_vacation()

    vacation_pay = upcoming_vacation['estimated_pay'] if upcoming_vacation else 0
    if vacation_pay > 0:
        expected_income_breakdown = (
            f"ЗП: {'{:,.0f}'.format(expected_income).replace(',', ' ')} ₽"
            f" + Отпускные: {'{:,.0f}'.format(vacation_pay).replace(',', ' ')} ₽"
        )
        expected_income += vacation_pay
    else:
        expected_income_breakdown = ''
    future_regular = get_regular_payments_until_date(today, next_income)
    regular_after_income = get_regular_payments_after_date(today, next_income)

    spend_warning = "⚠️ Внимание! Денег не хватит на регулярные платежи!" if can_spend_today < 0 else ""
    free_money_now = period_balance + income_this_period - expenses_this_period - unpaid_regular
    due_payments = get_due_regular_payments(today)
    all_categories = get_all_category_names()

    if real_advance > 0:
        expected_remainder = planned_salary - real_advance
        salary_remainder_text = f"{expected_remainder:,.0f} ₽".replace(",", " ")
        salary_remainder_note = f"(Аванс: {real_advance:,.0f} ₽)".replace(",", " ")
    else:
        expected_remainder = planned_salary
        salary_remainder_text = f"{expected_remainder:,.0f} ₽".replace(",", " ")
        salary_remainder_note = "⚠️ Аванс ещё не внесён"

    # Светофор Сегодня — хватит ли денег на сегодня
    unpaid_regular_month = regular_total_month - paid_regular
    cash_on_hand = period_balance + income_this_period - expenses_this_period

    # Сколько из оставшейся зарплаты (не аванс) уже получено в этом периоде
    with get_db() as conn:
        remaining_received = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM operations
            WHERE type = 'Доход' AND category = 'Зарплата'
              AND (subcategory != 'Аванс' OR subcategory IS NULL)
              AND date >= ? AND date <= ?
        ''', (period_start_date.strftime('%Y-%m-%d'), period_end_date.strftime('%Y-%m-%d'))).fetchone()[0]

    future_income = max(0, expected_income - remaining_received)
    available_for_month = cash_on_hand + future_income - unpaid_regular_month

    if can_spend_today < 0:
        today_light, today_text = "red", "⚠️ КАССОВЫЙ РАЗРЫВ!"
    elif can_spend_today < 5000:
        today_light, today_text = "yellow", "⚠️ Осторожно: остаток меньше 5000 ₽"
    else:
        today_light, today_text = "green", "✅ Всё хорошо"

    # Светофор До конца зарплатного месяца — хватит ли с учётом будущей ЗП на все регулярные
    if available_for_month < 0:
        month_light, month_text = "red", "⚠️ КАССОВЫЙ РАЗРЫВ!"
    elif available_for_month < 5000:
        month_light, month_text = "yellow", "⚠️ Осторожно: остаток меньше 5000 ₽"
    else:
        month_light, month_text = "green", "✅ Всё хорошо"

    # Ежедневный лимит: сколько можно тратить в день из того, что уже на руках
    daily_limit = can_spend_today / days_to_income if days_to_income > 0 else can_spend_today

    income_cats = get_income_categories()
    expense_cats = get_expense_categories()

    return render_template('index.html',
                           operations=operations,
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           free_money_now=free_money_now,
                            expected_income=expected_income,
                            expected_income_breakdown=expected_income_breakdown,
                            future_regular=future_regular,
                           regular_after_income=regular_after_income,
                           can_spend_today=can_spend_today,
                           spend_warning=spend_warning,
                           days_to_income=days_to_income,
                           next_income=next_income,
                            today_light=today_light,
                            today_text=today_text,
                            month_light=month_light,
                            month_text=month_text,
                            available_for_month=available_for_month,
                            daily_limit=daily_limit,
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
                            upcoming_vacation=upcoming_vacation,
                            page=page, total_pages=total_pages)


@bp.route('/apply_regular', methods=['POST'])
def apply_regular():
    apply_regular_payments()
    flash('Регулярные платежи применены', 'success')
    return redirect(url_for('main.index'))


@bp.route('/apply_regular/<int:payment_id>', methods=['POST'])
def apply_single_regular(payment_id):
    from database import get_db
    from datetime import datetime
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
