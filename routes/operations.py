from flask import Blueprint, request, redirect, url_for, flash, jsonify, Response
from database import get_db
from utils import get_period
import csv
import io

bp = Blueprint('operations', __name__)


@bp.route('/add_operation', methods=['POST'])
def add_operation():
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

    if op_type == 'Расход':
        from services.telegram_service import check_budget_alert
        check_budget_alert(category, amount)

    flash('Операция добавлена', 'success')
    return redirect(url_for('main.index'))


@bp.route('/delete/<int:id>')
def delete(id):
    with get_db() as conn:
        conn.execute('DELETE FROM operations WHERE id = ?', (id,))
    flash('Операция удалена', 'success')
    return redirect(url_for('main.index'))


@bp.route('/get_operation/<int:id>')
def get_operation(id):
    with get_db() as conn:
        op = conn.execute('SELECT * FROM operations WHERE id = ?', (id,)).fetchone()
        if op:
            return jsonify(dict(op))
        return jsonify({'error': 'Operation not found'}), 404


@bp.route('/export_csv')
def export_csv():
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = 'SELECT date, type, category, subcategory, amount, comment, period FROM operations WHERE 1=1'
    params = []

    if date_from:
        query += ' AND date >= ?'
        params.append(date_from)
    if date_to:
        query += ' AND date <= ?'
        params.append(date_to)

    query += ' ORDER BY date DESC'

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Дата', 'Тип', 'Категория', 'Подкатегория', 'Сумма', 'Комментарий', 'Период'])
    for r in rows:
        writer.writerow([r['date'], r['type'], r['category'], r['subcategory'] or '',
                         r['amount'], r['comment'] or '', r['period'] or ''])

    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=operations.csv'}
    )


@bp.route('/edit_operation', methods=['POST'])
def edit_operation():
    data = request.json
    with get_db() as conn:
        conn.execute('''
            UPDATE operations 
            SET date = ?, type = ?, category = ?, subcategory = ?, amount = ?, comment = ?
            WHERE id = ?
        ''', (data['date'], data['type'], data['category'], data['subcategory'],
              data['amount'], data['comment'], data['id']))
    return jsonify({'success': True})