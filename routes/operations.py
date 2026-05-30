from flask import render_template, request, redirect, url_for, flash, jsonify
from database import get_db
from utils import get_period


def register_routes(app):
    @app.route('/add', methods=['GET', 'POST'])
    def add():
        if request.method == 'POST':
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

            flash('Операция добавлена', 'success')
            return redirect(url_for('index'))

        # Получаем категории из БД для JavaScript
        with get_db() as conn:
            categories = {}
            rows = conn.execute('SELECT * FROM categories ORDER BY type, name').fetchall()

            # Сначала добавляем основные категории
            for row in rows:
                if row['parent_id'] is None:
                    categories[row['name']] = []

            # Затем добавляем подкатегории к соответствующим родителям
            for row in rows:
                if row['parent_id'] is not None:
                    parent = conn.execute('SELECT name FROM categories WHERE id = ?', (row['parent_id'],)).fetchone()
                    if parent and parent['name'] in categories:
                        categories[parent['name']].append(row['name'])

        return render_template('add.html', categories=categories)

    @app.route('/delete/<int:id>')
    def delete(id):
        with get_db() as conn:
            conn.execute('DELETE FROM operations WHERE id = ?', (id,))
        flash('Операция удалена', 'success')
        return redirect(url_for('index'))

    @app.route('/edit/<int:id>', methods=['POST'])
    def edit_operation(id):
        date_str = request.form['date']
        op_type = request.form['type']
        category = request.form['category']
        subcategory = request.form['subcategory']
        amount = float(request.form['amount'])
        comment = request.form['comment']
        period = get_period(date_str)

        with get_db() as conn:
            conn.execute('''
                UPDATE operations 
                SET date = ?, type = ?, category = ?, subcategory = ?, amount = ?, comment = ?, period = ?
                WHERE id = ?
            ''', (date_str, op_type, category, subcategory, amount, comment, period, id))

        return jsonify({'success': True})
