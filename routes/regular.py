from flask import request, redirect, url_for, flash, render_template
from database import get_db


def register_routes(app):
    @app.route('/regular', methods=['GET', 'POST'])
    def regular():
        if request.method == 'POST':
            # Добавление нового платежа
            if 'add_category' in request.form and 'add_amount' in request.form:
                amount = float(request.form['add_amount'])
                day = request.form['add_day']
                category = request.form['add_category']
                subcategory = request.form.get('add_subcategory', '')
                interval = request.form.get('add_interval', 'monthly')

                with get_db() as conn:
                    conn.execute('''
                        INSERT INTO regular_payments (amount, day, category, subcategory, interval)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (amount, day, category, subcategory, interval))
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
                flash('Регулярные платежи обновлены', 'success')

            return redirect(url_for('regular'))

        # GET запрос — показываем страницу
        with get_db() as conn:
            # Получаем категории расходов для выпадающих списков
            expense_cats = {}

            expense_main = conn.execute('''
                SELECT * FROM categories WHERE parent_id IS NULL AND type = 'Расход' ORDER BY name
            ''').fetchall()

            for cat in expense_main:
                subcats = conn.execute('''
                    SELECT name FROM categories WHERE parent_id = ? ORDER BY name
                ''', (cat['id'],)).fetchall()
                expense_cats[cat['name']] = [s['name'] for s in subcats]

            # Получаем все регулярные платежи
            payments = conn.execute('SELECT * FROM regular_payments ORDER BY day, category, subcategory').fetchall()

        return render_template('regular.html', payments=payments, expense_categories=expense_cats)