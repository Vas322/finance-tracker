from flask import Blueprint, render_template
from database import get_db
from datetime import date

bp = Blueprint('analytics', __name__)


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

        expense_by_category = [
            {'category': row['category'], 'total': row['total']}
            for row in expense_by_category_raw
        ]

        total_expense = conn.execute(
            'SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Расход"'
        ).fetchone()[0]

        monthly_raw = conn.execute('''
            SELECT strftime('%Y-%m', date) as month,
                   COALESCE(SUM(CASE WHEN type='Доход' THEN amount ELSE 0 END), 0) as income,
                   COALESCE(SUM(CASE WHEN type='Расход' THEN amount ELSE 0 END), 0) as expense
            FROM operations
            WHERE date >= date('now', '-11 months', 'start of month')
            GROUP BY month
            ORDER BY month
        ''').fetchall()

        monthly_data = [
            {'month': r['month'], 'income': r['income'], 'expense': r['expense']}
            for r in monthly_raw
        ]

        curr_month = date.today().strftime('%Y-%m')
        budgets_raw = conn.execute(
            'SELECT category, amount FROM budgets WHERE month = ?', (curr_month,)
        ).fetchall()
        budgets_map = {r['category']: r['amount'] for r in budgets_raw}

        for item in expense_by_category:
            item['budget'] = budgets_map.get(item['category'], 0)

    return render_template('analytics.html',
                           expense_by_category=expense_by_category,
                           total_expense=total_expense,
                           monthly_data=monthly_data)
