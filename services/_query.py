from services.balance_service import get_expenses_for_period, get_income_for_period
from datetime import date
from database import get_db

today = date.today()
prev_start = date(2026, 6, 10)
prev_end = date(2026, 6, 24)

print('=== DOHODY (10-24 iunya) ===')
with get_db() as conn:
    rows = conn.execute(
        "SELECT date, category, subcategory, amount, comment FROM operations WHERE type = ? AND date >= ? AND date <= ? ORDER BY date",
        ('Dohod', prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d'))
    ).fetchall()
total_inc = 0
for r in rows:
    sub = '/' + r['subcategory'] if r['subcategory'] else ''
    cmt = ' (' + r['comment'] + ')' if r['comment'] else ''
    line = f'  {r["date"]}  {r["category"]}{sub:25s} {r["amount"]:>8,.0f} RUB{cmt}'
    print(line)
    total_inc += r['amount']
print(f'  {"-"*50}')
print(f'  {"ITOGO DOHODOV":>40s} {total_inc:>8,.0f} RUB')

print()
print('=== RASHODY (10-24 iunya) ===')
with get_db() as conn:
    rows = conn.execute(
        "SELECT date, category, subcategory, amount, comment FROM operations WHERE type = ? AND date >= ? AND date <= ? ORDER BY date",
        ('Rashod', prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d'))
    ).fetchall()
total_exp = 0
for r in rows:
    sub = '/' + r['subcategory'] if r['subcategory'] else ''
    cmt = ' (' + r['comment'] + ')' if r['comment'] else ''
    line = f'  {r["date"]}  {r["category"]}{sub:25s} {r["amount"]:>8,.0f} RUB{cmt}'
    print(line)
    total_exp += r['amount']
print(f'  {"-"*50}')
print(f'  {"ITOGO RASHODOV":>40s} {total_exp:>8,.0f} RUB')

print()
print(f'leftover_from_prev = {total_inc} - {total_exp} = {total_inc - total_exp} RUB')
