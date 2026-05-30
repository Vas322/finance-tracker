from flask import render_template, request, redirect, url_for, flash, jsonify
from database import get_db


def register_routes(app):
    @app.route('/categories')
    def categories():
        with get_db() as conn:
            # Получаем все основные категории (parent_id IS NULL)
            main_cats = conn.execute('''
                SELECT * FROM categories WHERE parent_id IS NULL ORDER BY type, name
            ''').fetchall()

            # Получаем подкатегории для каждой основной
            result = []
            for cat in main_cats:
                subcats = conn.execute('''
                    SELECT * FROM categories WHERE parent_id = ? ORDER BY name
                ''', (cat['id'],)).fetchall()
                result.append({
                    'id': cat['id'],
                    'type': cat['type'],
                    'name': cat['name'],
                    'subcategories': subcats
                })
        return render_template('categories.html', categories=result)

    @app.route('/add_category', methods=['POST'])
    def add_category():
        cat_type = request.form['type']
        name = request.form['name']
        parent_id = request.form.get('parent_id')
        if parent_id == '':
            parent_id = None
        else:
            parent_id = int(parent_id)

        with get_db() as conn:
            try:
                conn.execute(
                    'INSERT INTO categories (type, name, parent_id) VALUES (?, ?, ?)',
                    (cat_type, name, parent_id)
                )
                flash(f'Категория "{name}" добавлена', 'success')
            except:
                flash('Такая категория уже существует', 'error')

        return redirect(url_for('categories'))

    @app.route('/delete_category/<int:id>')
    def delete_category(id):
        with get_db() as conn:
            # Сначала удаляем подкатегории
            conn.execute('DELETE FROM categories WHERE parent_id = ?', (id,))
            # Потом саму категорию
            conn.execute('DELETE FROM categories WHERE id = ?', (id,))
        flash('Категория удалена', 'success')
        return redirect(url_for('categories'))
    @app.route('/edit_category/<int:id>', methods=['POST'])
    def edit_category(id):
        name = request.form['name']
        with get_db() as conn:
            conn.execute('UPDATE categories SET name = ? WHERE id = ?', (name, id))
        return jsonify({'success': True})