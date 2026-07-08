from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.idea_service import (
    get_all_ideas, get_idea, create_idea, update_idea, delete_idea, get_idea_stats
)

bp = Blueprint('ideas', __name__)

STATUSES = ['💡 Предложена', '✅ Одобрена', '🚧 В разработке', '🧪 Тестирование', '🎉 Реализована', '❌ Отклонена']

ROI_LABELS = {0: '—', 1: '★☆☆☆☆ (Очень низкий)', 2: '★★☆☆☆ (Низкий)', 3: '★★★☆☆ (Средний)', 4: '★★★★☆ (Высокий)', 5: '★★★★★ (Очень высокий)'}
COMPLEXITY_LABELS = {0: '—', 1: '★☆☆☆☆ (Очень низкая)', 2: '★★☆☆☆ (Низкая)', 3: '★★★☆☆ (Средняя)', 4: '★★★★☆ (Высокая)', 5: '★★★★★ (Очень высокая)'}
RISK_LABELS = {'': '—', 'LOW': '🟢 Низкий', 'MEDIUM': '🟧 Средний', 'HIGH': '🟥 Высокий'}


# --- Jinja2 template filters ---

@bp.app_template_filter('stars')
def stars_filter(n: int) -> str:
    try:
        n = int(n)
    except (ValueError, TypeError):
        n = 0
    return '★' * n + '☆' * max(0, 5 - n)


@bp.app_template_filter('risk_label')
def risk_label_filter(risk: str) -> str:
    return RISK_LABELS.get(risk, '—')


@bp.app_template_filter('risk_color')
def risk_color_filter(risk: str) -> str:
    colors = {'LOW': 'success', 'MEDIUM': 'warning', 'HIGH': 'danger'}
    return colors.get(risk, 'secondary')


@bp.app_template_filter('roi_color')
def roi_color_filter(n) -> str:
    try:
        n = int(n)
    except (ValueError, TypeError):
        n = 0
    if n >= 4:
        return 'success'
    elif n >= 3:
        return 'warning'
    elif n >= 1:
        return 'danger'
    return 'secondary'


@bp.app_template_filter('status_color')
def status_color_filter(status: str) -> str:
    if status.startswith('💡'):
        return 'info'
    elif status.startswith('✅'):
        return 'success'
    elif status.startswith('🚧'):
        return 'warning'
    elif status.startswith('🧪'):
        return 'secondary'
    elif status.startswith('🎉'):
        return 'success'
    elif status.startswith('❌'):
        return 'danger'
    return 'secondary'


# --- Routes ---

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
        roi = int(request.form.get('roi', 0))
        complexity = int(request.form.get('complexity', 0))
        risk = request.form.get('risk', '').strip()

        if not title:
            flash('Название обязательно', 'error')
            return render_template('development_form.html', idea=None, statuses=STATUSES)

        create_idea(title, problem, description, benefit, roi, complexity, risk)
        flash('Идея создана', 'success')
        return redirect(url_for('ideas.development'))

    return render_template('development_form.html', idea=None, statuses=STATUSES,
                           roi_labels=ROI_LABELS, complexity_labels=COMPLEXITY_LABELS, risk_labels=RISK_LABELS)


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
        roi = int(request.form.get('roi', 0))
        complexity = int(request.form.get('complexity', 0))
        risk = request.form.get('risk', '').strip()

        if status not in STATUSES:
            flash('Некорректный статус', 'error')
            return render_template('development_form.html', idea=idea, statuses=STATUSES,
                                   roi_labels=ROI_LABELS, complexity_labels=COMPLEXITY_LABELS, risk_labels=RISK_LABELS)

        if not title:
            flash('Название обязательно', 'error')
            return render_template('development_form.html', idea=idea, statuses=STATUSES,
                                   roi_labels=ROI_LABELS, complexity_labels=COMPLEXITY_LABELS, risk_labels=RISK_LABELS)

        update_idea(id, title, problem, description, benefit, status, roi, complexity, risk)
        flash(f'Идея {idea["code"]} обновлена', 'success')
        return redirect(url_for('ideas.development'))

    return render_template('development_form.html', idea=idea, statuses=STATUSES,
                           roi_labels=ROI_LABELS, complexity_labels=COMPLEXITY_LABELS, risk_labels=RISK_LABELS)


@bp.route('/development/<int:id>/delete', methods=['POST'])
def development_delete(id: int):
    idea = get_idea(id)
    if not idea:
        flash('Идея не найдена', 'error')
    else:
        delete_idea(id)
        flash(f'Идея {idea["code"]} удалена', 'success')
    return redirect(url_for('ideas.development'))
