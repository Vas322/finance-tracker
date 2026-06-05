from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from datetime import date

bp = Blueprint('budgets', __name__)


@bp.route('/budgets', methods=['GET', 'POST'])
def budgets():
    if request.method == 'POST':
        month = request.form.get('month', date.today().strftime('%Y-%m'))

        with get_db() as conn:
            conn.execute('DELETE FROM budgets WHERE month = ?', (month,))

            for key, value in request.form.items():
                if key.startswith('budget_'):
                    category = key.replace('budget_', '', 1)
                    amount = float(value) if value else 0
                    if amount > 0:
                        conn.execute(
                            'INSERT INTO budgets (category, month, amount) VALUES (?, ?, ?)',
                            (category, month, amount)
                        )

        flash('Бюджеты сохранены', 'success')
        return redirect(url_for('budgets.budgets', month=month))

    month = request.args.get('month', date.today().strftime('%Y-%m'))

    with get_db() as conn:
        expense_cats = [row['name'] for row in conn.execute(
            'SELECT DISTINCT name FROM categories WHERE parent_id IS NULL AND type = \'Расход\' ORDER BY name'
        ).fetchall()]

        budgets_raw = conn.execute(
            'SELECT category, amount FROM budgets WHERE month = ?', (month,)
        ).fetchall()
        budgets_map = {r['category']: r['amount'] for r in budgets_raw}

        start = month + '-01'
        if month[5:7] == '12':
            end = str(int(month[:4]) + 1) + '-01-01'
        else:
            end = month[:5] + str(int(month[5:7]) + 1).zfill(2) + '-01'

        spent_raw = conn.execute('''
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Расход' AND date >= ? AND date < ?
            GROUP BY category
        ''', (start, end)).fetchall()
        spent_map = {r['category']: r['total'] for r in spent_raw}

    return render_template('budgets.html', month=month, expense_categories=expense_cats,
                           budgets_map=budgets_map, spent_map=spent_map)
