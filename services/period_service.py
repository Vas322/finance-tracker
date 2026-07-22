from datetime import datetime, date, timedelta
from database import get_db


def get_salary_day():
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = 'salary_day'").fetchone()
        return int(row['value']) if row else 10


def get_advance_day():
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = 'advance_day'").fetchone()
        return int(row['value']) if row else 25


def get_period(date_str: str) -> str:
    sd = get_salary_day()
    ad = get_advance_day()
    day = datetime.strptime(date_str, '%Y-%m-%d').day
    return f"{sd:02d}-{ad-1:02d}" if sd <= day <= ad-1 else f"{ad:02d}-{sd-1:02d}"


def get_next_income_date(today: date) -> date:
    sd = get_salary_day()
    ad = get_advance_day()
    if today.day < sd:
        return date(today.year, today.month, sd)
    elif today.day < ad:
        return date(today.year, today.month, ad)
    else:
        next_month = today.month + 1
        year = today.year
        if next_month > 12:
            next_month = 1
            year += 1
        return date(year, next_month, sd)


def get_period_dates(today: date):
    sd = get_salary_day()
    ad = get_advance_day()
    if sd <= today.day <= ad - 1:
        period_start = date(today.year, today.month, sd)
        period_end = date(today.year, today.month, ad - 1)
    else:
        if today.day >= ad:
            period_start = date(today.year, today.month, ad)
            if today.month == 12:
                period_end = date(today.year + 1, 1, sd - 1)
            else:
                period_end = date(today.year, today.month + 1, sd - 1)
        else:
            period_start = date(today.year, today.month - 1, ad) if today.month > 1 else date(today.year - 1, 12, ad)
            period_end = date(today.year, today.month, sd - 1)
    return period_start, period_end


def get_previous_period_dates(today: date) -> tuple[date, date]:
    sd = get_salary_day()
    ad = get_advance_day()
    if sd <= today.day <= ad - 1:
        prev_start = date(today.year, today.month - 1, ad) if today.month > 1 else date(today.year - 1, 12, ad)
        prev_end = date(today.year, today.month, sd - 1)
    else:
        if today.day >= ad:
            prev_start = date(today.year, today.month, sd)
            prev_end = date(today.year, today.month, ad - 1)
        else:
            prev_start = date(today.year, today.month - 1, sd) if today.month > 1 else date(today.year - 1, 12, sd)
            prev_end = date(today.year, today.month - 1, ad - 1) if today.month > 1 else date(today.year - 1, 12, ad - 1)
    return prev_start, prev_end


def get_regular_cycle_start(today: date) -> date:
    ad = get_advance_day()
    if today.day >= ad:
        return date(today.year, today.month, ad)
    prev = today.month - 1
    y = today.year
    if prev == 0:
        prev = 12
        y -= 1
    return date(y, prev, ad)


def get_previous_cycle(cursor: date) -> tuple[date, date]:
    return get_previous_period_dates(cursor)


def get_salary_period(today: date) -> tuple[date, date]:
    sd = get_salary_day()
    if today.day >= sd:
        start = date(today.year, today.month, sd)
        if today.month == 12:
            end = date(today.year + 1, 1, sd - 1)
        else:
            end = date(today.year, today.month + 1, sd - 1)
    else:
        if today.month == 1:
            start = date(today.year - 1, 12, sd)
        else:
            start = date(today.year, today.month - 1, sd)
        end = date(today.year, today.month, sd - 1)
    return start, end


def count_working_days(start: date, end: date) -> int:
    import holidays
    ru_holidays = holidays.country_holidays('RU')
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in ru_holidays:
            days += 1
        current += timedelta(days=1)
    return days


def calculate_next_income(today: date, planned_salary_cents: int) -> tuple[int, date]:
    sd = get_salary_day()
    ad = get_advance_day()
    period_start, period_end = get_salary_period(today)
    total_wd = count_working_days(period_start, period_end)

    advance_date = date(period_start.year, period_start.month, ad)

    if today < advance_date:
        advance_wd = count_working_days(period_start, advance_date)
        amount = (planned_salary_cents * advance_wd) // total_wd
        next_date = advance_date
    else:
        advance_wd = count_working_days(period_start, advance_date)
        advance_amount = (planned_salary_cents * advance_wd) // total_wd
        amount = planned_salary_cents - advance_amount
        if period_start.month == 12:
            next_date = date(period_start.year + 1, 1, sd)
        else:
            next_date = date(period_start.year, period_start.month + 1, sd)

    return amount, next_date
