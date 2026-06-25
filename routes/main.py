from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db
from datetime import date

from services.regular_service import (
    apply_regular_payments,
    get_regular_payments_after_date, get_due_regular_payments,
)
from services.balance_service import update_current_period_balance
from services.operation_service import get_operations_page, get_totals
from services.category_service import get_all_category_names, get_income_categories, get_expense_categories
from services.vacation_service import get_upcoming_vacation
from services.dashboard_service import compute_dashboard_stats

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

    total_income, total_expense, balance, total_expense_without_regulars = get_totals()
    stats = compute_dashboard_stats(today)

    planned_salary = stats['planned_salary']
    real_advance = stats['real_advance']
    can_spend_today = stats['can_spend_today']
    expected_income = stats['expected_income']
    next_income = stats['next_income']
    days_to_income = stats['days_to_income']
    daily_limit = stats['daily_limit']

    if 10 <= today.day <= 24:
        period_start, period_end = 10, 24
    else:
        period_start, period_end = 25, 9

    upcoming_vacation = get_upcoming_vacation()
    regular_after_income = get_regular_payments_after_date(today, next_income)
    confirmed = session.get('confirmed_payments', {})
    this_month = today.strftime('%Y-%m')
    due_payments = [p for p in get_due_regular_payments(today) if confirmed.get(str(p['id'])) != this_month]
    all_categories = get_all_category_names()

    if real_advance > 0:
        salary_remainder_note = f"(Аванс: {real_advance:,.0f} ₽)".replace(",", " ")
    else:
        salary_remainder_note = "⚠️ Аванс ещё не внесён"

    if can_spend_today < 0:
        today_light, today_text = "red", "⚠️ КАССОВЫЙ РАЗРЫВ!"
    elif can_spend_today < 5000:
        today_light, today_text = "yellow", "⚠️ Осторожно: остаток меньше 5000 ₽"
    else:
        today_light, today_text = "green", "✅ Всё хорошо"

    income_cats = get_income_categories()
    expense_cats = get_expense_categories()

    return render_template('index.html',
                           operations=operations,
                           total_income=total_income,
                           total_expense=total_expense,
                           total_expense_without_regulars=total_expense_without_regulars,
                           balance=balance,
                           expected_income=expected_income,
                           regular_after_income=regular_after_income,
                           can_spend_today=can_spend_today,
                           days_to_income=days_to_income,
                           next_income=next_income,
                           today_light=today_light,
                           today_text=today_text,
                           daily_limit=daily_limit,
                           all_categories=all_categories,
                           salary_remainder_note=salary_remainder_note,
                           income_categories=income_cats,
                           expense_categories=expense_cats,
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
    from datetime import datetime
    amount = float(request.form.get('amount', 0))
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    today_day = today.day

    with get_db() as conn:
        p = conn.execute('SELECT * FROM regular_payments WHERE id = ?', (payment_id,)).fetchone()
        if p and p['category'] and amount > 0:
            period = "10-24" if 10 <= today_day <= 24 else "25-09"
            conn.execute(
                'INSERT INTO operations (date, type, category, subcategory, amount, comment, period) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (today_str, 'Расход', p['category'], p['subcategory'], amount,
                 f'Авто: {p["interval"]}', period)
            )
            confirmed = session.get('confirmed_payments', {})
            confirmed[str(payment_id)] = today.strftime('%Y-%m')
            session['confirmed_payments'] = confirmed
            flash(f'Платёж "{p["category"]}" — {amount:,.0f} ₽ применён', 'success')
    return redirect(url_for('main.index'))


@bp.route('/update_money', methods=['POST'])
def update_money():
    new_amount = float(request.form['current_money'])
    today = date.today()
    update_current_period_balance(today, new_amount)
    flash(f'Начальный остаток: {new_amount:,.0f} ₽', 'success')
    return redirect(url_for('main.index'))
