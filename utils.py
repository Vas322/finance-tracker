from datetime import datetime, date
from config import SALARY_DAY, ADVANCE_DAY


def get_period(date_str):
    day = datetime.strptime(date_str, '%Y-%m-%d').day
    return "10-24" if 10 <= day <= 24 else "25-09"


def get_next_income_date(today):
    if today.day < SALARY_DAY:
        return date(today.year, today.month, SALARY_DAY)
    elif today.day < ADVANCE_DAY:
        return date(today.year, today.month, ADVANCE_DAY)
    else:
        next_month = today.month + 1
        year = today.year
        if next_month > 12:
            next_month = 1
            year += 1
        return date(year, next_month, SALARY_DAY)


def get_regular_payments_for_period(today, period_start_day, period_end_day):
    """Возвращает сумму регулярных платежей за период с учётом периодичности"""
    from database import get_db

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    total = 0
    for p in payments:
        if not p['day']:
            continue

        # Получаем день месяца из даты
        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

        # Проверяем попадает ли день в период
        in_period = False
        if period_start_day <= period_end_day:
            if period_start_day <= payment_day <= period_end_day:
                in_period = True
        else:
            if payment_day >= period_start_day or payment_day <= period_end_day:
                in_period = True

        if in_period:
            # Учитываем периодичность
            interval = p['interval'] if p['interval'] else 'monthly'
            amount = p['amount']

            if interval == 'monthly':
                total += amount
            elif interval == 'weekly':
                # В полумесяце примерно 2 недели
                total += amount * 2
            elif interval == 'yearly':
                # Доля от года: (дней в периоде / 365) * сумма
                # Упрощённо: 1/24 от года (полумесяц)
                total += amount / 24
            else:
                total += amount

    return total


def get_regular_total_for_month():
    from database import get_db
    with get_db() as conn:
        result = conn.execute('SELECT SUM(amount) FROM regular_payments').fetchone()[0]
        return result or 0


from datetime import datetime, date, timedelta
from config import SALARY_DAY, ADVANCE_DAY
import calendar


def get_period(date_str):
    day = datetime.strptime(date_str, '%Y-%m-%d').day
    return "10-24" if 10 <= day <= 24 else "25-09"


def get_next_income_date(today):
    if today.day < SALARY_DAY:
        return date(today.year, today.month, SALARY_DAY)
    elif today.day < ADVANCE_DAY:
        return date(today.year, today.month, ADVANCE_DAY)
    else:
        next_month = today.month + 1
        year = today.year
        if next_month > 12:
            next_month = 1
            year += 1
        return date(year, next_month, SALARY_DAY)


def get_regular_payments_for_period(today, period_start_day, period_end_day):
    """Возвращает сумму регулярных платежей за период с учётом периодичности"""
    from database import get_db

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    total = 0
    for p in payments:
        if not p['day']:
            continue

        # Получаем день месяца из даты
        payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

        # Проверяем попадает ли день в период
        in_period = False
        if period_start_day <= period_end_day:
            if period_start_day <= payment_day <= period_end_day:
                in_period = True
        else:
            if payment_day >= period_start_day or payment_day <= period_end_day:
                in_period = True

        if in_period:
            # Учитываем периодичность
            interval = p['interval'] if p['interval'] else 'monthly'
            amount = p['amount']

            if interval == 'monthly':
                total += amount
            elif interval == 'weekly':
                # В полумесяце примерно 2 недели
                total += amount * 2
            elif interval == 'yearly':
                # Доля от года: (дней в периоде / 365) * сумма
                # Упрощённо: 1/24 от года (полумесяц)
                total += amount / 24
            else:
                total += amount

    return total


def get_regular_total_for_month():
    from database import get_db
    with get_db() as conn:
        result = conn.execute('SELECT SUM(amount) FROM regular_payments').fetchone()[0]
        return result or 0


def apply_regular_payments():
    """Автоматически добавляет операции по регулярным платежам за сегодня"""
    from database import get_db
    from datetime import date, datetime
    import calendar

    today = date.today()
    today_day = today.day
    today_str = today.strftime('%Y-%m-%d')

    with get_db() as conn:
        # Получаем все регулярные платежи
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

        for p in payments:
            if not p['day']:
                continue

            payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day

            # Проверяем, нужно ли применять сегодня
            should_apply = False

            if p['interval'] == 'monthly':
                if payment_day == today_day:
                    should_apply = True
            elif p['interval'] == 'weekly':
                # Упрощённо: проверяем, совпадает ли день недели
                payment_date = datetime.strptime(p['day'], '%Y-%m-%d')
                if payment_date.weekday() == today.weekday():
                    should_apply = True
            elif p['interval'] == 'yearly':
                payment_date = datetime.strptime(p['day'], '%Y-%m-%d')
                if payment_date.month == today.month and payment_date.day == today_day:
                    should_apply = True

            if should_apply:
                # Проверяем, не добавлена ли уже операция за сегодня
                existing = conn.execute('''
                    SELECT id FROM operations 
                    WHERE date = ? AND category = ? AND subcategory = ? AND amount = ? AND type = 'Расход'
                ''', (today_str, p['category'], p['subcategory'], p['amount'])).fetchone()

                if not existing and p['category']:
                    # Добавляем операцию
                    period = "10-24" if 10 <= today_day <= 24 else "25-09"
                    conn.execute('''
                        INSERT INTO operations (date, type, category, subcategory, amount, comment, period)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (today_str, 'Расход', p['category'], p['subcategory'], p['amount'],
                          f'Авто: {p["interval"]}', period))
                    print(f'Автоматически добавлен платёж: {p["category"]} - {p["subcategory"]} ({p["amount"]} ₽)')
