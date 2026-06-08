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


def check_and_notify():
    from datetime import date, timedelta, datetime
    from database import get_db

    today = date.today()
    upcoming = []
    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments WHERE category != ""').fetchall()
        for p in payments:
            if not p['day']:
                continue
            payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
            interval = p['interval']
            for offset in range(1, 4):
                check_date = today + timedelta(days=offset)
                check_day = check_date.day
                due = False
                if interval == 'monthly' and payment_day == check_day:
                    due = True
                elif interval == 'weekly':
                    pd = datetime.strptime(p['day'], '%Y-%m-%d')
                    if pd.weekday() == check_date.weekday():
                        due = True
                elif interval == 'yearly':
                    pd = datetime.strptime(p['day'], '%Y-%m-%d')
                    if pd.month == check_date.month and pd.day == check_day:
                        due = True
                if due:
                    upcoming.append({'date': check_date, 'category': p['category'], 'subcategory': p['subcategory'] or '', 'amount': p['amount']})
                    break

    if not upcoming:
        return

    lines = ['<b>Напоминание о регулярных платежах</b>\n']
    upcoming.sort(key=lambda x: x['date'])
    for u in upcoming:
        date_str = u['date'].strftime('%d.%m')
        sub = f' ({u["subcategory"]})' if u['subcategory'] else ''
        amount_str = "{:,.0f}".format(u["amount"]).replace(",", " ")
        lines.append(f'📅 {date_str} — {u["category"]}{sub} — {amount_str} ₽')
    send_message('\n'.join(lines))
