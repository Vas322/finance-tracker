from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.idea_service import (
    get_all_ideas, get_idea, create_idea, update_idea, delete_idea, get_idea_stats
)

bp = Blueprint('ideas', __name__)


STATUSES = ['💡 Предложена', '✅ Одобрена', '🚧 В разработке', '🧪 Тестирование', '🎉 Реализована', '❌ Отклонена']


@bp.before_request
def check_admin():
    if session.get('username') != 'admin':
        return 'Доступ запрещён', 403


@bp.route('/development')
def development():
    ideas = get_all_ideas()
    stats = get_idea_stats()
    return render_template('development.html', ideas=ideas, stats=stats, statuses=STATUSES)


@bp.route('/development/create', methods=['GET', 'POST'])
def development_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        problem = request.form.get('problem', '').strip()
        description = request.form.get('description', '').strip()
        benefit = request.form.get('benefit', '').strip()

        if not title:
            flash('Название обязательно', 'error')
            return render_template('development_form.html', idea=None, statuses=STATUSES)

        create_idea(title, problem, description, benefit)
        flash(f'Идея создана', 'success')
        return redirect(url_for('ideas.development'))

    return render_template('development_form.html', idea=None, statuses=STATUSES)


@bp.route('/development/<int:id>')
def development_card(id: int):
    idea = get_idea(id)
    if not idea:
        flash('Идея не найдена', 'error')
        return redirect(url_for('ideas.development'))
    return render_template('development_card.html', idea=idea)


@bp.route('/development/<int:id>/edit', methods=['GET', 'POST'])
def development_edit(id: int):
    idea = get_idea(id)
    if not idea:
        flash('Идея не найдена', 'error')
        return redirect(url_for('ideas.development'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        problem = request.form.get('problem', '').strip()
        description = request.form.get('description', '').strip()
        benefit = request.form.get('benefit', '').strip()
        status = request.form.get('status', '💡 Предложена').strip()

        if status not in STATUSES:
            flash('Некорректный статус', 'error')
            return render_template('development_form.html', idea=idea, statuses=STATUSES)

        if not title:
            flash('Название обязательно', 'error')
            return render_template('development_form.html', idea=idea, statuses=STATUSES)

        update_idea(id, title, problem, description, benefit, status)
        flash(f'Идея {idea["code"]} обновлена', 'success')
        return redirect(url_for('ideas.development'))

    return render_template('development_form.html', idea=idea, statuses=STATUSES)


@bp.route('/development/<int:id>/delete', methods=['POST'])
def development_delete(id: int):
    idea = get_idea(id)
    if not idea:
        flash('Идея не найдена', 'error')
    else:
        delete_idea(id)
        flash(f'Идея {idea["code"]} удалена', 'success')
    return redirect(url_for('ideas.development'))



