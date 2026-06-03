from flask import render_template, request, redirect, url_for, flash, jsonify
from database import get_db
from utils import get_period

def register_routes(app):
    @app.route('/add_operation', methods=['POST'])
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

        flash('Операция добавлена', 'success')
        return redirect(url_for('index'))

    @app.route('/delete/<int:id>')
    def delete(id):
        with get_db() as conn:
            conn.execute('DELETE FROM operations WHERE id = ?', (id,))
        flash('Операция удалена', 'success')
        return redirect(url_for('index'))

    @app.route('/get_operation/<int:id>')
    def get_operation(id):
        with get_db() as conn:
            op = conn.execute('SELECT * FROM operations WHERE id = ?', (id,)).fetchone()
            if op:
                return jsonify(dict(op))
            return jsonify({'error': 'Operation not found'}), 404

    @app.route('/edit_operation', methods=['POST'])
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