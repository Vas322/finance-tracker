import json
import time
import threading
from urllib.request import Request, urlopen
from urllib.error import URLError
from config import Config


def send_message(text: str) -> bool:
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return False
    payload = json.dumps({'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}).encode()
    req = Request(f'https://api.telegram.org/bot{token}/sendMessage', data=payload,
                  headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except URLError:
        return False


def _get_payments_for_date(target_date):
    from datetime import datetime
    from database import get_db

    result = []
    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments WHERE category != ""').fetchall()
        for p in payments:
            if not p['day']:
                continue
            payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
            interval = p['interval']
            due = False
            if interval == 'monthly' and payment_day == target_date.day:
                due = True
            elif interval == 'weekly':
                pd = datetime.strptime(p['day'], '%Y-%m-%d')
                if pd.weekday() == target_date.weekday():
                    due = True
            elif interval == 'yearly':
                pd = datetime.strptime(p['day'], '%Y-%m-%d')
                if pd.month == target_date.month and pd.day == target_date.day:
                    due = True
            if due:
                result.append({
                    'category': p['category'],
                    'subcategory': p['subcategory'] or '',
                    'amount': p['amount']
                })
    return result


def _format_payments(payments):
    lines = []
    for p in payments:
        sub = f' ({p["subcategory"]})' if p['subcategory'] else ''
        amount_str = "{:,.0f}".format(p["amount"]).replace(",", " ")
        lines.append(f'— {p["category"]}{sub} — {amount_str} ₽')
    return '\n'.join(lines)


def notify_tomorrow():
    from datetime import date, timedelta
    tomorrow = date.today() + timedelta(days=1)
    payments = _get_payments_for_date(tomorrow)
    if not payments:
        return
    text = (
        f'<b>⏰ Напоминание: завтра регулярные платежи</b>\n'
        f'📅 {tomorrow.strftime("%d.%m")}\n\n'
        f'{_format_payments(payments)}\n\n'
        f'Не забудь пополнить баланс!'
    )
    send_message(text)


def notify_due_today():
    from datetime import date
    today = date.today()
    payments = _get_payments_for_date(today)
    if not payments:
        return
    text = (
        f'<b>📢 Сегодня — день платежа!</b>\n'
        f'📅 {today.strftime("%d.%m")}\n\n'
        f'{_format_payments(payments)}\n\n'
        f'Обязательно оплати сегодня!'
    )
    send_message(text)


# ─── Daily Digest ───────────────────────────────────────────────

def send_daily_digest():
    from datetime import date, datetime
    from database import get_db
    from services.period_service import get_period_dates, get_next_income_date
    from services.balance_service import get_expenses_for_period, get_income_for_period, update_period_balance

    today = date.today()
    period_start, period_end = get_period_dates(today)
    period_balance = update_period_balance(today)

    expenses_period = get_expenses_for_period(period_start, period_end)
    income_period = get_income_for_period(period_start, period_end)

    with get_db() as conn:
        planned_salary_row = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()
        planned_salary = float(planned_salary_row['value']) if planned_salary_row else 185000

    advance_amount = planned_salary * 0.5
    advance_day = 25

    if today.day >= advance_day:
        advance_received = income_period
        advance_for_period = advance_received
    else:
        last_advance = 0
        advance_for_period = advance_amount

    with get_db() as conn:
        total_regular = sum(
            row['amount'] for row in conn.execute('SELECT amount FROM regular_payments').fetchall()
        )
    saved_from_advance = min(total_regular * 0.5, advance_for_period)

    can_spend_today = advance_for_period - saved_from_advance + period_balance - expenses_period

    next_income = get_next_income_date(today)
    days_to_income = (next_income - today).days
    daily_limit = can_spend_today / days_to_income if days_to_income > 0 else can_spend_today

    cash_on_hand = period_balance + income_period - expenses_period
    if today.day >= advance_day:
        remaining_salary = planned_salary - advance_received if advance_received < planned_salary else 0
    else:
        remaining_salary = planned_salary
    available_for_month = cash_on_hand + remaining_salary - total_regular

    today_payments = _get_payments_for_date(today)
    today_expenses = get_expenses_for_period(today, today)

    today_emoji = "🟢" if can_spend_today >= 5000 else ("🟡" if can_spend_today >= 0 else "🔴")
    month_emoji = "🟢" if available_for_month >= 5000 else ("🟡" if available_for_month >= 0 else "🔴")

    lines = [
        f'<b>☀️ Доброе утро!</b>',
        f'📅 {today.strftime("%d.%m.%Y")}\n',
        f'{today_emoji} Сегодня: {"{:,.0f}".format(can_spend_today).replace(",", " ")} ₽',
        f'{month_emoji} До зарплаты: {"{:,.0f}".format(available_for_month).replace(",", " ")} ₽',
        f'📊 Средний лимит: {"{:,.0f}".format(daily_limit).replace(",", " ")} ₽/день',
        f'📆 Дохода через: {days_to_income} дн.\n',
    ]

    if today_payments:
        lines.append('<b>📢 Платежи сегодня:</b>')
        lines.append(_format_payments(today_payments))
        lines.append('')

    if today_expenses > 0:
        lines.append(f'💸 Уже потрачено сегодня: {"{:,.0f}".format(today_expenses).replace(",", " ")} ₽')

    send_message('\n'.join(lines))


# ─── Budget Alert ───────────────────────────────────────────────

def check_budget_alert(category: str, amount: float):
    from datetime import date
    from database import get_db

    today = date.today()
    month = today.strftime('%Y-%m')

    with get_db() as conn:
        budget = conn.execute(
            'SELECT amount FROM budgets WHERE category = ? AND month = ?',
            (category, month)
        ).fetchone()
        if not budget:
            return

        start = month + '-01'
        if month[5:7] == '12':
            end = str(int(month[:4]) + 1) + '-01-01'
        else:
            end = month[:5] + str(int(month[5:7]) + 1).zfill(2) + '-01'

        spent = conn.execute(
            'SELECT COALESCE(SUM(amount), 0) as total FROM operations WHERE type = "Расход" AND category = ? AND date >= ? AND date < ?',
            (category, start, end)
        ).fetchone()['total']

        budget_amount = budget['amount']
        if spent > budget_amount:
            pct = int((spent / budget_amount) * 100)
            amount_str = "{:,.0f}".format(spent).replace(",", " ")
            budget_str = "{:,.0f}".format(budget_amount).replace(",", " ")
            text = (
                f'<b>⚠️ Превышение бюджета!</b>\n'
                f'Категория: {category}\n'
                f'Лимит: {budget_str} ₽\n'
                f'Потрачено: {amount_str} ₽ ({pct}%)\n'
                f'Перерасход: {"{:,.0f}".format(spent - budget_amount).replace(",", " ")} ₽'
            )
            send_message(text)


# ─── Bot Polling ────────────────────────────────────────────────

_polling_active = False
_last_update_id = 0


def _api_call(method: str, payload: dict):
    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        return None
    data = json.dumps(payload).encode()
    req = Request(f'https://api.telegram.org/bot{token}/{method}', data=data,
                  headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError):
        return None


def set_my_commands():
    _api_call('setMyCommands', {
        'commands': [
            {'command': 'start', 'description': 'Приветствие и помощь'},
            {'command': 'status', 'description': 'Финансовый статус'},
        ]
    })


def start_polling():
    global _polling_active
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return
    set_my_commands()
    _polling_active = True
    thread = threading.Thread(target=_polling_loop, daemon=True)
    thread.start()


def stop_polling():
    global _polling_active
    _polling_active = False


def _polling_loop():
    global _last_update_id, _polling_active
    token = Config.TELEGRAM_BOT_TOKEN

    while _polling_active:
        try:
            url = f'https://api.telegram.org/bot{token}/getUpdates?offset={_last_update_id + 1}&timeout=30'
            req = Request(url)
            with urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode())
                for update in data.get('result', []):
                    _last_update_id = update['update_id']
                    _process_update(update)
        except (URLError, json.JSONDecodeError, ConnectionError):
            time.sleep(10)


def _process_update(update):
    msg = update.get('message') or update.get('edited_message')
    if not msg:
        return
    text = msg.get('text', '').strip()
    if not text:
        return

    if text.startswith('/'):
        _handle_command(text)
    else:
        _handle_add_expense(text)


def _handle_command(text: str):
    if text == '/start':
        send_message(
            f'<b>👋 Привет! Я бот Finance Tracker</b>\n\n'
            f'Доступные команды:\n'
            f'/status — текущее финансовое состояние\n\n'
            f'<b>Добавить расход:</b>\n'
            f'Просто напиши категорию и сумму, например:\n'
            f'<code>такси 500</code>\n'
            f'<code>продукты супермаркет 1500</code>'
        )
    elif text == '/status':
        _handle_status()


def _handle_status():
    from datetime import date
    from database import get_db
    from services.period_service import get_period_dates, get_next_income_date
    from services.balance_service import get_expenses_for_period, get_income_for_period, update_period_balance

    today = date.today()
    period_start, period_end = get_period_dates(today)
    period_balance = update_period_balance(today)

    expenses_period = get_expenses_for_period(period_start, period_end)
    income_period = get_income_for_period(period_start, period_end)

    with get_db() as conn:
        planned_salary_row = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()
        planned_salary = float(planned_salary_row['value']) if planned_salary_row else 185000

    advance_amount = planned_salary * 0.5
    if today.day >= 25:
        advance_for_period = income_period
    else:
        advance_for_period = advance_amount

    with get_db() as conn:
        total_regular = sum(
            row['amount'] for row in conn.execute('SELECT amount FROM regular_payments').fetchall()
        )
    saved_from_advance = min(total_regular * 0.5, advance_for_period)

    can_spend_today = advance_for_period - saved_from_advance + period_balance - expenses_period

    next_income = get_next_income_date(today)
    days_to_income = (next_income - today).days
    daily_limit = can_spend_today / days_to_income if days_to_income > 0 else can_spend_today

    cash_on_hand = period_balance + income_period - expenses_period
    if today.day >= 25:
        remaining_salary = planned_salary - advance_for_period if advance_for_period < planned_salary else 0
    else:
        remaining_salary = planned_salary
    available_for_month = cash_on_hand + remaining_salary - total_regular

    def light(val):
        if val < 0:
            return '🔴'
        if val < 5000:
            return '🟡'
        return '🟢'

    today_payments = _get_payments_for_date(today)

    lines = [
        f'<b>📊 Финансовый статус</b>\n',
        f'{light(can_spend_today)} Сегодня: {"{:,.0f}".format(can_spend_today).replace(",", " ")} ₽',
        f'{light(available_for_month)} До зарплаты: {"{:,.0f}".format(available_for_month).replace(",", " ")} ₽',
        f'📊 Лимит на день: {"{:,.0f}".format(daily_limit).replace(",", " ")} ₽',
        f'💰 Остаток периода: {"{:,.0f}".format(period_balance).replace(",", " ")} ₽',
        f'📆 Следующий доход: {next_income.strftime("%d.%m")} (через {days_to_income} дн.)',
    ]

    if today_payments:
        lines.append(f'\n<b>📢 Платежи сегодня:</b>')
        lines.append(_format_payments(today_payments))

    send_message('\n'.join(lines))


def _handle_add_expense(text: str):
    from datetime import date
    from database import get_db
    from utils import get_period

    words = text.strip().split()
    if len(words) < 2:
        send_message('❌ Формат: <code>категория сумма</code> или <code>категория подкатегория сумма</code>')
        return

    last = words[-1]
    try:
        amount = abs(float(last.replace(',', '.')))
    except ValueError:
        send_message('❌ Не могу распознать сумму. Пример: <code>такси 500</code>')
        return

    query = ' '.join(words[:-1]).strip().lower()

    with get_db() as conn:
        all_cats = conn.execute(
            'SELECT id, type, name, parent_id FROM categories WHERE type = "Расход" ORDER BY name'
        ).fetchall()

    parent_map = {}
    sub_map = {}
    for c in all_cats:
        if c['parent_id'] is None:
            parent_map[c['name'].lower()] = c['name']
        else:
            sub_map[c['name'].lower()] = c['name']

    parent_children = {}
    for c in all_cats:
        if c['parent_id'] is not None:
            pname = None
            for p in all_cats:
                if p['id'] == c['parent_id'] and p['parent_id'] is None:
                    pname = p['name']
                    break
            if pname:
                parent_children.setdefault(pname.lower(), {})[c['name'].lower()] = c['name']

    category = None
    subcategory = ''
    comment = ''

    matched_sub = None
    matched_parent = None

    for sub_name_lower, sub_name in sub_map.items():
        if sub_name_lower in query or query == sub_name_lower:
            matched_sub = sub_name
            break

    if matched_sub:
        for c in all_cats:
            if c['name'].lower() == sub_name_lower and c['parent_id'] is not None:
                for p in all_cats:
                    if p['id'] == c['parent_id'] and p['parent_id'] is None:
                        matched_parent = p['name']
                        break
                break
        if matched_parent:
            category = matched_parent
            subcategory = matched_sub
            comment = query.replace(matched_sub.lower(), '').strip()
    else:
        for cat_name_lower, cat_name in parent_map.items():
            if cat_name_lower in query or query == cat_name_lower:
                matched_parent = cat_name
                break
        if matched_parent:
            category = matched_parent
            remaining = query.replace(matched_parent.lower(), '').strip()
            if remaining:
                subcategory = remaining
                comment = ''
            else:
                subcategory = ''
                comment = ''
        else:
            category = 'Другое'
            comment = query

    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    period = get_period(today_str)

    with get_db() as conn:
        conn.execute(
            'INSERT INTO operations (date, type, category, subcategory, amount, comment, period) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (today_str, 'Расход', category, subcategory, amount, comment, period)
        )

    sub = f' ({subcategory})' if subcategory else ''
    amount_str = "{:,.0f}".format(amount).replace(",", " ")
    send_message(f'✅ Расход добавлен: {category}{sub} — {amount_str} ₽')

    check_budget_alert(category, amount)
