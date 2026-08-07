from typing import Optional
from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify
from database import get_db
from datetime import date
from decimal import Decimal, InvalidOperation
from services.savings_service import (
    get_all_accounts, get_account, create_account, update_account,
    archive_account, reactivate_account, delete_account as svc_delete_account,
    deposit, withdraw, get_transactions, get_savings_stats, get_savings_total
)

bp = Blueprint('savings', __name__, url_prefix='/savings')


def _parse_amount(raw_value: Optional[str]) -> Optional[int]:
    """Конвертирует сумму в рублях в копейки; пустое поле — 0, некорректный ввод — None."""
    if raw_value is None or raw_value == '':
        return 0
    try:
        return int(Decimal(raw_value) * 100)
    except (ValueError, InvalidOperation):
        return None


@bp.route('/')
def savings_index():
    all_accounts = get_all_accounts(active_only=False)
    stats = get_savings_stats()
    active_accounts = []
    archived_accounts = []
    for a in all_accounts:
        a_dict = dict(a)
        a_dict['transactions'] = get_transactions(a['id'], limit=10)
        if a['target_amount'] > 0:
            a_dict['progress_pct'] = min(100, int(a['balance'] * 100 / a['target_amount']))
        else:
            a_dict['progress_pct'] = None
        if a['is_active']:
            active_accounts.append(a_dict)
        else:
            archived_accounts.append(a_dict)
    return render_template('savings.html', accounts=active_accounts, archived_accounts=archived_accounts, stats=stats, today=date.today())


@bp.route('/create', methods=['POST'])
def savings_create():
    name = request.form['name']
    target_amount = _parse_amount(request.form.get('target_amount'))
    if target_amount is None:
        flash('Некорректная сумма цели', 'error')
        return redirect(url_for('savings.savings_index'))
    target_date = request.form.get('target_date', '') or None
    icon = request.form.get('icon', 'bi-piggy-bank')
    color = request.form.get('color', '#17a2b8')
    create_account(name, target_amount, target_date, icon, color)
    flash(f'Счёт «{name}» создан', 'success')
    return redirect(url_for('savings.savings_index'))


@bp.route('/deposit', methods=['POST'])
def savings_deposit():
    account_id = int(request.form['account_id'])
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
    account_id = int(request.form['account_id'])
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
    name = request.form['name']
    target_amount = _parse_amount(request.form.get('target_amount'))
    if target_amount is None:
        flash('Некорректная сумма цели', 'error')
        return redirect(url_for('savings.savings_index'))
    target_date = request.form.get('target_date', '') or None
    icon = request.form.get('icon', 'bi-piggy-bank')
    color = request.form.get('color', '#17a2b8')
    update_account(account_id, name=name, target_amount=target_amount, target_date=target_date, icon=icon, color=color)
    flash('Счёт обновлён', 'success')
    return redirect(url_for('savings.savings_index'))


@bp.route('/archive/<int:account_id>', methods=['POST'])
def savings_archive(account_id: int):
    archive_account(account_id)
    flash('Счёт архивирован', 'info')
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
