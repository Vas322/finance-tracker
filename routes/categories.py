from flask import render_template, request, redirect, url_for, flash, jsonify
from database import get_db


def register_routes(app):
    @app.route('/categories')
    def categories():
        with get_db() as conn:
            main_cats = conn.execute('''
                SELECT * FROM categories WHERE parent_id IS NULL ORDER BY type, name
            ''').fetchall()

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
        name = request.form['name'].strip()
        parent_id = request.form.get('parent_id')

        if not name:
            flash('Введите название', 'error')
            return redirect(url_for('categories'))

        # Преобразуем parent_id
        if parent_id and parent_id != '':
            parent_id = int(parent_id)
        else:
            parent_id = None

        with get_db() as conn:
            try:
                conn.execute(
                    'INSERT INTO categories (type, name, parent_id) VALUES (?, ?, ?)',
                    (cat_type, name, parent_id)
                )
                if parent_id:
                    flash(f'Подкатегория "{name}" добавлена', 'success')
                else:
                    flash(f'Категория "{name}" добавлена', 'success')
            except Exception as e:
                flash('Такая категория уже существует', 'error')

        return redirect(url_for('categories'))

    @app.route('/delete_category/<int:id>')
    def delete_category(id):
        with get_db() as conn:
            conn.execute('DELETE FROM categories WHERE parent_id = ?', (id,))
            conn.execute('DELETE FROM categories WHERE id = ?', (id,))
        flash('Категория удалена', 'success')
        return redirect(url_for('categories'))

    @app.route('/edit_category/<int:id>', methods=['POST'])
    def edit_category(id):
        name = request.form['name']
        with get_db() as conn:
            conn.execute('UPDATE categories SET name = ? WHERE id = ?', (name, id))
        return jsonify({'success': True})

    @app.route('/update_subcategories/<int:cat_id>', methods=['POST'])
    def update_subcategories(cat_id):
        import json
        data = json.loads(request.data)
        new_subcats = data.get('subcategories', [])

        with get_db() as conn:
            # Удаляем старые подкатегории
            conn.execute('DELETE FROM categories WHERE parent_id = ?', (cat_id,))
            # Добавляем новые
            for sub_name in new_subcats:
                if sub_name:
                    # Определяем тип от родителя
                    parent = conn.execute('SELECT type FROM categories WHERE id = ?', (cat_id,)).fetchone()
                    if parent:
                        conn.execute(
                            'INSERT INTO categories (type, name, parent_id) VALUES (?, ?, ?)',
                            (parent['type'], sub_name, cat_id)
                        )
        return jsonify({'success': True})