from flask import Blueprint, request, redirect, url_for, flash, render_template
from database import get_db
from datetime import datetime, date

bp = Blueprint('regular', __name__)


@bp.route('/regular', methods=['GET', 'POST'])
def regular():
    if request.method == 'POST':
        # Добавление нового платежа
        if 'add_category' in request.form and 'add_amount' in request.form:
            amount = float(request.form['add_amount'])
            day = request.form['add_day']
            category = request.form['add_category']
            subcategory = request.form.get('add_subcategory', '')
            interval = request.form.get('add_interval', 'monthly')
            comment = request.form.get('add_comment', '')

            with get_db() as conn:
                conn.execute('''
                    INSERT INTO regular_payments (amount, day, category, subcategory, interval, comment)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (amount, day, category, subcategory, interval, comment))
            flash('Платёж добавлен', 'success')

        # Удаление платежа
        elif 'delete_id' in request.form:
            pid = int(request.form['delete_id'])
            with get_db() as conn:
                conn.execute('DELETE FROM regular_payments WHERE id = ?', (pid,))
            flash('Платёж удалён', 'success')

        # Обновление существующих платежей
        else:
            with get_db() as conn:
                for key, value in request.form.items():
                    if key.startswith('amount_'):
                        pid = int(key.split('_')[1])
                        amount = float(value)
                        conn.execute('UPDATE regular_payments SET amount = ? WHERE id = ?', (amount, pid))
                    elif key.startswith('day_'):
                        pid = int(key.split('_')[1])
                        day = value
                        conn.execute('UPDATE regular_payments SET day = ? WHERE id = ?', (day, pid))
                    elif key.startswith('category_'):
                        pid = int(key.split('_')[1])
                        category = value
                        conn.execute('UPDATE regular_payments SET category = ? WHERE id = ?', (category, pid))
                    elif key.startswith('subcategory_'):
                        pid = int(key.split('_')[1])
                        subcategory = value
                        conn.execute('UPDATE regular_payments SET subcategory = ? WHERE id = ?', (subcategory, pid))
                    elif key.startswith('interval_'):
                        pid = int(key.split('_')[1])
                        interval = value
                        conn.execute('UPDATE regular_payments SET interval = ? WHERE id = ?', (interval, pid))
                    elif key.startswith('comment_'):
                        pid = int(key.split('_')[1])
                        comment = value
                        conn.execute('UPDATE regular_payments SET comment = ? WHERE id = ?', (comment, pid))
            flash('Регулярные платежи обновлены', 'success')

        return redirect(url_for('regular.regular'))

    filter_type = request.args.get('filter', 'all')
    now = date.today()

    with get_db() as conn:
        expense_cats = {}
        expense_main = conn.execute('''
            SELECT * FROM categories WHERE parent_id IS NULL AND type = 'Расход' ORDER BY name
        ''').fetchall()

        for cat in expense_main:
            subcats = conn.execute('''
                SELECT name FROM categories WHERE parent_id = ? ORDER BY name
            ''', (cat['id'],)).fetchall()
            expense_cats[cat['name']] = [s['name'] for s in subcats]

        if filter_type == 'current':
            if 10 <= now.day <= 24:
                period_start, period_end = 10, 24
            else:
                period_start, period_end = 25, 9

            payments = []
            all_payments = conn.execute(
                'SELECT * FROM regular_payments ORDER BY day, category, subcategory').fetchall()

            for p in all_payments:
                if p['day']:
                    payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
                    if period_start <= period_end:
                        if period_start <= payment_day <= period_end:
                            payments.append(p)
                    else:
                        if payment_day >= period_start or payment_day <= period_end:
                            payments.append(p)
        else:
            payments = conn.execute('SELECT * FROM regular_payments ORDER BY day, category, subcategory').fetchall()

    return render_template('regular.html', payments=payments, expense_categories=expense_cats,
                           filter_type=filter_type, now=now,
                           regular_total=sum(p['amount'] for p in payments))
