from services.regular_service import get_regular_total, get_paid_regular_payments_this_month


def get_planning_data(planned_salary: float, real_advance: float, regular_total: float, paid_regular: float = 0):
    if real_advance > 0:
        advance = real_advance
        remaining_salary = planned_salary - advance
        advance_percent = advance / planned_salary if planned_salary > 0 else 0
    else:
        advance_percent = 0.5
        advance = planned_salary * advance_percent
        remaining_salary = planned_salary - advance
    regular_to_save = max(0, regular_total - paid_regular)
    need_to_save_from_advance = regular_to_save * advance_percent
    need_to_save_from_remaining = regular_to_save * (1 - advance_percent)
    return {
        'advance': advance,
        'remaining_salary': remaining_salary,
        'advance_percent': advance_percent,
        'regular_to_save': regular_to_save,
        'need_to_save_from_advance': need_to_save_from_advance,
        'need_to_save_from_remaining': need_to_save_from_remaining,
        'left_from_advance': advance - need_to_save_from_advance,
        'left_from_remaining': remaining_salary - need_to_save_from_remaining,
    }
