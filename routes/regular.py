from flask import request, redirect, url_for, flash, render_template
from database import get_db


def register_routes(app):
    @app.route('/regular', methods=['GET', 'POST'])
    def regular():
        if request.method == 'POST':
            if 'add_name' in request.form:
                name = request.form['add_name']
                amount = float(request.form['add_amount'])
                day = request.form['add_day']
                with get_db() as conn:
                    conn.execute('INSERT INTO regular_payments (name, amount, day) VALUES (?, ?, ?)',
                                 (name, amount, day))
                flash('Платёж добавлен', 'success')

            elif 'delete_id' in request.form:
                pid = int(request.form['delete_id'])
                with get_db() as conn:
                    conn.execute('DELETE FROM regular_payments WHERE id = ?', (pid,))
                flash('Платёж удалён', 'success')

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
                flash('Регулярные платежи обновлены', 'success')

            return redirect(url_for('regular'))

        with get_db() as conn:
            payments = conn.execute('SELECT * FROM regular_payments ORDER BY day, name').fetchall()
        return render_template('regular.html', payments=payments)
