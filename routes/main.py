from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db
from datetime import date

from services.regular_service import (
    apply_regular_payments,
    get_due_regular_payments, get_paid_regulars_in_period,
    get_cycle_regulars_list, get_skipped_total, skip_regular_payment,
)
from services.period_service import get_regular_cycle_start, get_advance_day
from services.operation_service import get_operations_page
from services.category_service import get_all_category_names, get_income_categories, get_expense_categories
from services.vacation_service import get_upcoming_vacation
from services.dashboard_service import compute_dashboard_stats
from services.telegram_service import notify_traffic_change

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
    cycle_start = get_regular_cycle_start(today)
    paid_this_cycle = get_paid_regulars_in_period(cycle_start, today)
    skipped_this_cycle = get_skipped_total(cycle_start)
    regular_until_income = max(0, stats['regular_total_month'] - paid_this_cycle - skipped_this_cycle)
    cycle_regulars_all = get_cycle_regulars_list(today)
    upcoming_regulars = [r for r in cycle_regulars_all if not r['paid'] and not r['skipped']]
    due_payments = get_due_regular_payments(today)
    all_categories = get_all_category_names()

    if next_income.day == get_advance_day():
        salary_remainder_note = f"(Аванс: {expected_income//100:,.0f} ₽)".replace(",", " ")
    else:
        salary_remainder_note = f"(Зарплата: {expected_income//100:,.0f} ₽)".replace(",", " ")

    if can_spend_today < 0:
        today_light, today_text = "red", "⚠️ КАССОВЫЙ РАЗРЫВ!"
    elif can_spend_today < 500000:
        today_light, today_text = "yellow", "⚠️ Осторожно: остаток меньше 5000 ₽"
    else:
        today_light, today_text = "green", "✅ Всё хорошо"

    # --- Уведомление при ухудшении светофора ---
    traffic_levels = {'green': 0, 'yellow': 1, 'red': 2}
    new_level = traffic_levels[today_light]

    with get_db() as conn:
        row = conn.execute(
            'SELECT value FROM settings WHERE key = "last_traffic_light"'
        ).fetchone()

    if row and row['value']:
        old_level = int(row['value'])
        if new_level > old_level:
            notify_traffic_change(old_level, new_level, stats)

    with get_db() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            ('last_traffic_light', str(new_level))
        )

    income_cats = get_income_categories()
    expense_cats = get_expense_categories()

    return render_template('index.html',
                           operations=operations,
                           total_income=stats['income_this_period'],
                           total_expense=stats['expenses_this_period'],
                           total_expense_without_regulars=stats['total_expense_without_regulars'],
                           balance=stats['cash_on_hand'],
                           expected_income=expected_income,
                            regular_until_income=regular_until_income,
                           can_spend_today=can_spend_today,
                           days_to_income=days_to_income,
                           next_income=next_income,
                           today=today,
                           today_light=today_light,
                           today_text=today_text,
                           daily_limit=daily_limit,
                           all_categories=all_categories,
                           salary_remainder_note=salary_remainder_note,
                           income_categories=income_cats,
                           expense_categories=expense_cats,
                            due_payments=due_payments,
                            upcoming_vacation=upcoming_vacation,
                            upcoming_regulars=upcoming_regulars,
                           page=page, total_pages=total_pages)


@bp.route('/apply_regular', methods=['POST'])
def apply_regular():
    apply_regular_payments()
    flash('Регулярные платежи применены', 'success')
    return redirect(url_for('main.index'))


@bp.route('/apply_regular/<int:payment_id>', methods=['POST'])
def apply_single_regular(payment_id):
    from datetime import datetime
    amount = int(Decimal(request.form.get('amount', 0)) * 100)
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    today_day = today.day

    with get_db() as conn:
        p = conn.execute('SELECT * FROM regular_payments WHERE id = ?', (payment_id,)).fetchone()
        if p and p['category'] and amount > 0:
            period = "10-24" if 10 <= today_day <= 24 else "25-09"
            conn.execute(
                'INSERT INTO operations (date, type, category, subcategory, amount, comment, period, regular_payment_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (today_str, 'Расход', p['category'], p['subcategory'], amount,
                 f'Авто: {p["interval"]}', period, payment_id)
            )
            flash(f'Платёж "{p["category"]}" — {amount//100:,.0f} ₽ применён', 'success')
    return redirect(url_for('main.index'))


@bp.route('/skip_regular/<int:payment_id>', methods=['POST'])
def skip_regular(payment_id):
    today = date.today()
    cycle_start = get_regular_cycle_start(today)
    skip_regular_payment(payment_id, cycle_start)
    flash('Платёж отменён в текущем цикле', 'info')
    return redirect(url_for('main.index'))



