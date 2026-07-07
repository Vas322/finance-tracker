from decimal import Decimal
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
                    amount = Decimal(value) if value else Decimal('0')
                    if amount > 0:
                        conn.execute(
                            'INSERT INTO budgets (category, month, amount) VALUES (?, ?, ?)',
                            (category, month, float(amount))
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

        if not budgets_map:
            year, m = map(int, month.split('-'))
            if m == 1:
                prev_month = f'{year - 1:04d}-12'
            else:
                prev_month = f'{year:04d}-{m - 1:02d}'

            prev_raw = conn.execute(
                'SELECT category, amount FROM budgets WHERE month = ?', (prev_month,)
            ).fetchall()

            if prev_raw:
                for row in prev_raw:
                    conn.execute(
                        'INSERT OR IGNORE INTO budgets (category, month, amount) VALUES (?, ?, ?)',
                        (row['category'], month, row['amount'])
                    )
                conn.commit()
                budgets_map = {r['category']: r['amount'] for r in prev_raw}

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

    total_budget = sum(v for v in budgets_map.values())
    total_spent = sum(v for v in spent_map.values())

    return render_template('budgets.html', month=month, expense_categories=expense_cats,
                           budgets_map=budgets_map, spent_map=spent_map,
                           total_budget=total_budget, total_spent=total_spent)
