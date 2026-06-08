from datetime import datetime, date
from config import SALARY_DAY, ADVANCE_DAY


def get_period(date_str: str) -> str:
    day = datetime.strptime(date_str, '%Y-%m-%d').day
    return "10-24" if 10 <= day <= 24 else "25-09"


def get_next_income_date(today: date) -> date:
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


def get_period_dates(today: date):
    if 10 <= today.day <= 24:
        period_start = date(today.year, today.month, 10)
        period_end = date(today.year, today.month, 24)
    else:
        if today.day >= 25:
            period_start = date(today.year, today.month, 25)
            if today.month == 12:
                period_end = date(today.year + 1, 1, 9)
            else:
                period_end = date(today.year, today.month + 1, 9)
        else:
            period_start = date(today.year, today.month - 1, 25) if today.month > 1 else date(today.year - 1, 12, 25)
            period_end = date(today.year, today.month, 9)
    return period_start, period_end
