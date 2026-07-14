from datetime import datetime, date, timedelta
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


def get_previous_period_dates(today: date) -> tuple[date, date]:
    if 10 <= today.day <= 24:
        # Current period is 10-24, previous was 25-09 (from previous month)
        prev_start = date(today.year, today.month - 1, 25) if today.month > 1 else date(today.year - 1, 12, 25)
        prev_end = date(today.year, today.month, 9)
    else:
        # Current period is 25-09
        if today.day >= 25:
            # Current period is 25-09, previous was 10-24 of the same month
            prev_start = date(today.year, today.month, 10)
            prev_end = date(today.year, today.month, 24)
        else:
            # Current period is 25-09 (because day is <= 9), previous was 10-24 previous month
            prev_start = date(today.year, today.month - 1, 10) if today.month > 1 else date(today.year - 1, 12, 10)
            prev_end = date(today.year, today.month - 1, 24) if today.month > 1 else date(today.year - 1, 12, 24)
    return prev_start, prev_end


def get_salary_period(today: date) -> tuple[date, date]:
    """Зарплатный месяц: с SALARY_DAY месяца M до SALARY_DAY-1 месяца M+1."""
    if today.day >= SALARY_DAY:
        start = date(today.year, today.month, SALARY_DAY)
        if today.month == 12:
            end = date(today.year + 1, 1, SALARY_DAY - 1)
        else:
            end = date(today.year, today.month + 1, SALARY_DAY - 1)
    else:
        if today.month == 1:
            start = date(today.year - 1, 12, SALARY_DAY)
        else:
            start = date(today.year, today.month - 1, SALARY_DAY)
        end = date(today.year, today.month, SALARY_DAY - 1)
    return start, end


def count_working_days(start: date, end: date) -> int:
    """Рабочие дни (Пн–Пт, без российских праздников) между start и end включительно."""
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
    """Рассчитать следующий ожидаемый доход.

    Возвращает:
        (amount_cents, next_date)
    """
    period_start, period_end = get_salary_period(today)
    total_wd = count_working_days(period_start, period_end)

    advance_date = date(period_start.year, period_start.month, ADVANCE_DAY)

    if today < advance_date:
        advance_wd = count_working_days(period_start, advance_date)
        amount = (planned_salary_cents * advance_wd) // total_wd
        next_date = advance_date
    else:
        advance_wd = count_working_days(period_start, advance_date)
        advance_amount = (planned_salary_cents * advance_wd) // total_wd
        amount = planned_salary_cents - advance_amount
        if period_start.month == 12:
            next_date = date(period_start.year + 1, 1, SALARY_DAY)
        else:
            next_date = date(period_start.year, period_start.month + 1, SALARY_DAY)

    return amount, next_date
