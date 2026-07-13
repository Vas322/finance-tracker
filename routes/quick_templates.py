from flask import Blueprint, jsonify, request
from services.quick_template_service import (
    get_all_templates, get_template, create_template,
    update_template, delete_template, reorder_templates
)
from database import get_db
from datetime import date

bp = Blueprint('quick_templates', __name__)


@bp.route('/api/templates')
def api_list():
    templates = get_all_templates()
    return jsonify(templates)


@bp.route('/api/templates', methods=['POST'])
def api_create():
    data = request.get_json()
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    subcategory = data.get('subcategory', '').strip()
    amount = int(data.get('amount', 0))

    if not name or not category:
        return jsonify({'error': 'Название и категория обязательны'}), 400

    template_id = create_template(name, category, subcategory, amount)
    return jsonify({'id': template_id}), 201


@bp.route('/api/templates/<int:template_id>', methods=['PUT'])
def api_update(template_id):
    data = request.get_json()
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    subcategory = data.get('subcategory', '').strip()
    amount = int(data.get('amount', 0))

    if not name or not category:
        return jsonify({'error': 'Название и категория обязательны'}), 400

    update_template(template_id, name, category, subcategory, amount)
    return jsonify({'ok': True})


@bp.route('/api/templates/<int:template_id>', methods=['DELETE'])
def api_delete(template_id):
    delete_template(template_id)
    return jsonify({'ok': True})


@bp.route('/api/templates/reorder', methods=['POST'])
def api_reorder():
    data = request.get_json()
    ids = data.get('ids', [])
    reorder_templates(ids)
    return jsonify({'ok': True})


@bp.route('/quick_add/<int:template_id>', methods=['POST'])
def quick_add(template_id):
    """Быстрое добавление расхода по шаблону"""
    from services.period_service import get_period
    
    tpl = get_template(template_id)
    if not tpl:
        return jsonify({'error': 'Шаблон не найден'}), 404

    today_str = date.today().strftime('%Y-%m-%d')
    period = get_period(today_str)

    with get_db() as conn:
        conn.execute(
            'INSERT INTO operations (date, type, category, subcategory, amount, comment, period) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (today_str, 'Расход', tpl['category'], tpl['subcategory'] or '', tpl['amount'],
             f'Быстрый: {tpl["name"]}', period)
        )

    return jsonify({'ok': True, 'message': f'{tpl["name"]} — {tpl["amount"] // 100} ₽'})
