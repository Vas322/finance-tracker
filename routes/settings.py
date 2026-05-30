from flask import request, redirect, url_for, flash
from database import set_current_money

def register_routes(app):
    @app.route('/update_money', methods=['POST'])
    def update_money():
        new_amount = float(request.form['current_money'])
        set_current_money(new_amount)
        flash(f'Начальный остаток: {new_amount:,.0f} ₽', 'success')
        return redirect(url_for('index'))