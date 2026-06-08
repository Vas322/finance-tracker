from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from services.vacation_service import add_vacation, get_all_vacations

bp = Blueprint('vacations', __name__)


@bp.route('/vacations', methods=['GET', 'POST'])
def vacations():
    if request.method == 'POST':
        start_str = request.form['start_date']
        end_str = request.form['end_date']

        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

        if end_date < start_date:
            flash('Дата окончания не может быть раньше даты начала', 'error')
            return redirect(url_for('vacations.vacations'))

        add_vacation(start_date, end_date)
        flash(f'Отпуск с {start_str} по {end_str} добавлен', 'success')
        return redirect(url_for('vacations.vacations'))

    all_vacations = get_all_vacations()
    return render_template('vacations.html', vacations=all_vacations)
