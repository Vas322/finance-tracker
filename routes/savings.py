from typing import Optional
from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify
from datetime import date
from decimal import Decimal, InvalidOperation
from services.savings_service import (
    get_all_accounts, get_account, create_account, update_account,
    archive_account, reactivate_account, delete_account as svc_delete_account,
    deposit, withdraw, get_transactions, get_savings_stats, get_savings_total,
    accrued_income, projected_income
)

bp = Blueprint('savings', __name__, url_prefix='/savings')

# Для расчёта накопленного дохода методом среднего дневного баланса нужно учитывать
# все движения по счёту (даже если их много), поэтому берём большой лимит.
MAX_TXNS_FOR_ACCRUAL = 10000

# Значение select "Другое значение..." для поля "Банк / место".
BANK_OTHER = '__other__'


def _parse_amount(raw_value: Optional[str]) -> Optional[int]:
    """Конвертирует сумму в рублях в копейки; пустое поле — 0, некорректный ввод — None."""
    if raw_value is None or raw_value == '':
        return 0
    try:
        return int(Decimal(raw_value) * 100)
    except (ValueError, InvalidOperation):
        return None


def _parse_optional_date(raw_value: Optional[str]) -> Optional[str]:
    """Пустое поле — None; некорректная ISO-дата — ValueError."""
    if raw_value is None or raw_value == '':
        return None
    try:
        date.fromisoformat(raw_value)
    except ValueError:
        raise ValueError('Некорректная дата')
    return raw_value


def _parse_optional_int(raw_value: Optional[str]) -> Optional[int]:
    if raw_value is None or raw_value == '' or raw_value == '0':
        return None
    try:
        return int(raw_value)
    except (ValueError, TypeError):
        return None


def _parse_optional_rate(raw_value: Optional[str]) -> Optional[Decimal]:
    if raw_value is None or raw_value == '':
        return None
    try:
        val = Decimal(raw_value)
    except (ValueError, InvalidOperation):
        return None
    if val == 0:
        return None
    return val


def _parse_optional_text(raw_value: Optional[str]) -> Optional[str]:
    """Пустая строка — None."""
    if raw_value is None or raw_value.strip() == '':
        return None
    return raw_value.strip()


def _parse_account_id(raw_value: Optional[str]) -> Optional[int]:
    """Пустое/некорректное значение — None."""
    if raw_value is None or raw_value == '':
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


@bp.route('/')
def savings_index():
    all_accounts = get_all_accounts(active_only=False)
    stats = get_savings_stats()
    active_accounts = []
    archived_accounts = []
    for a in all_accounts:
        a_dict = dict(a)
        a_dict['transactions'] = get_transactions(a['id'], limit=MAX_TXNS_FOR_ACCRUAL)
        a_dict['accrued_income'] = accrued_income(a_dict['transactions'], a['start_date'], a['interest_rate'])
        a_dict['projected_income'] = projected_income(a['balance'], a['end_date'], a['interest_rate'])
        if a['target_amount'] > 0:
            a_dict['progress_pct'] = min(100, a['balance'] * 100 // a['target_amount'])
        else:
            a_dict['progress_pct'] = None
        if a['is_active']:
            active_accounts.append(a_dict)
        else:
            archived_accounts.append(a_dict)
    return render_template('savings.html', accounts=active_accounts, archived_accounts=archived_accounts, stats=stats, today=date.today())


@bp.route('/create', methods=['POST'])
def savings_create():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Название обязательно', 'error')
        return redirect(url_for('savings.savings_index'))
    target_amount = _parse_amount(request.form.get('target_amount'))
    if target_amount is None:
        flash('Некорректная сумма цели', 'error')
        return redirect(url_for('savings.savings_index'))
    icon = request.form.get('icon', 'bi-piggy-bank')
    color = request.form.get('color', '#17a2b8')
    try:
        target_date = _parse_optional_date(request.form.get('target_date'))
        start_date = _parse_optional_date(request.form.get('start_date'))
        end_date = _parse_optional_date(request.form.get('end_date'))
    except ValueError:
        flash('Некорректная дата', 'error')
        return redirect(url_for('savings.savings_index'))
    duration_months = _parse_optional_int(request.form.get('duration_months'))
    interest_rate = _parse_optional_rate(request.form.get('interest_rate'))
    bank = _parse_optional_text(request.form.get('bank'))
    if bank == BANK_OTHER:
        bank = _parse_optional_text(request.form.get('bank_custom'))
    create_account(name, target_amount, target_date, icon, color,
                   start_date=start_date, end_date=end_date,
                   duration_months=duration_months,
                   interest_rate=interest_rate, bank=bank)
    flash(f'Счёт «{name}» создан', 'success')
    return redirect(url_for('savings.savings_index'))


@bp.route('/deposit', methods=['POST'])
def savings_deposit():
    account_id = _parse_account_id(request.form.get('account_id'))
    if account_id is None or not get_account(account_id):
        flash('Некорректный идентификатор счёта', 'error')
        return redirect(url_for('savings.savings_index'))
    amount = _parse_amount(request.form.get('amount'))
    if amount is None:
        flash('Некорректная сумма', 'error')
        return redirect(url_for('savings.savings_index'))
    if amount <= 0:
        flash('Сумма должна быть больше нуля', 'error')
        return redirect(url_for('savings.savings_index'))
    date_str = request.form.get('date', date.today().strftime('%Y-%m-%d'))
    comment = request.form.get('comment', '')
    try:
        deposit(account_id, amount, date_str, comment)
        flash('Счёт пополнен', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('savings.savings_index'))


@bp.route('/withdraw', methods=['POST'])
def savings_withdraw():
    account_id = _parse_account_id(request.form.get('account_id'))
    if account_id is None or not get_account(account_id):
        flash('Некорректный идентификатор счёта', 'error')
        return redirect(url_for('savings.savings_index'))
    amount = _parse_amount(request.form.get('amount'))
    if amount is None:
        flash('Некорректная сумма', 'error')
        return redirect(url_for('savings.savings_index'))
    if amount <= 0:
        flash('Сумма должна быть больше нуля', 'error')
        return redirect(url_for('savings.savings_index'))
    date_str = request.form.get('date', date.today().strftime('%Y-%m-%d'))
    comment = request.form.get('comment', '')
    try:
        withdraw(account_id, amount, date_str, comment)
        flash('Средства сняты с накоплений', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('savings.savings_index'))


@bp.route('/update/<int:account_id>', methods=['POST'])
def savings_update(account_id: int):
    name = request.form.get('name', '').strip()
    if not name:
        flash('Название обязательно', 'error')
        return redirect(url_for('savings.savings_index'))
    target_amount = _parse_amount(request.form.get('target_amount'))
    if target_amount is None:
        flash('Некорректная сумма цели', 'error')
        return redirect(url_for('savings.savings_index'))
    icon = request.form.get('icon', 'bi-piggy-bank')
    color = request.form.get('color', '#17a2b8')
    try:
        target_date = _parse_optional_date(request.form.get('target_date'))
        start_date = _parse_optional_date(request.form.get('start_date'))
        end_date = _parse_optional_date(request.form.get('end_date'))
    except ValueError:
        flash('Некорректная дата', 'error')
        return redirect(url_for('savings.savings_index'))
    duration_months = _parse_optional_int(request.form.get('duration_months'))
    interest_rate = _parse_optional_rate(request.form.get('interest_rate'))
    bank = _parse_optional_text(request.form.get('bank'))
    if bank == BANK_OTHER:
        bank = _parse_optional_text(request.form.get('bank_custom'))
    update_account(account_id, name=name, target_amount=target_amount, target_date=target_date,
                   icon=icon, color=color, start_date=start_date, end_date=end_date,
                   duration_months=duration_months, interest_rate=interest_rate, bank=bank)
    flash('Счёт обновлён', 'success')
    return redirect(url_for('savings.savings_index'))


@bp.route('/archive/<int:account_id>', methods=['POST'])
def savings_archive(account_id: int):
    try:
        archive_account(account_id)
        flash('Счёт архивирован', 'info')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('savings.savings_index'))


@bp.route('/restore/<int:account_id>', methods=['POST'])
def savings_restore(account_id: int):
    reactivate_account(account_id)
    flash('Счёт разархивирован', 'success')
    return redirect(url_for('savings.savings_index'))


@bp.route('/delete/<int:account_id>', methods=['POST'])
def savings_delete(account_id: int):
    try:
        svc_delete_account(account_id)
        flash('Счёт удалён', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('savings.savings_index'))


@bp.route('/get/<int:account_id>')
def savings_get(account_id: int):
    account = get_account(account_id)
    if not account:
        return jsonify({'error': 'Not found'}), 404
    account['target_amount'] = account['target_amount'] // 100
    account['balance'] = account['balance'] // 100
    return jsonify(dict(account))


@bp.route('/transactions/<int:account_id>')
def savings_transactions(account_id: int):
    txns = get_transactions(account_id)
    result = []
    for t in txns:
        t_dict = dict(t)
        t_dict['amount'] = t_dict['amount'] // 100
        result.append(t_dict)
    return jsonify(result)
