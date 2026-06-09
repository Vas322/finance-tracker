import json
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
