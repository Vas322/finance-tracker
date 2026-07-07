import ast
import sys

files = [
    'app.py', 'database.py', 'routes/main.py', 'routes/operations.py',
    'routes/regular.py', 'routes/budgets.py', 'routes/planning.py',
    'routes/analytics.py', 'routes/settings.py', 'services/regular_service.py',
    'services/dashboard_service.py', 'services/planning_service.py',
    'services/balance_service.py', 'services/operation_service.py',
    'services/telegram_service.py', 'seeds.py'
]
errors = []
for f in files:
    try:
        with open(f, encoding='utf-8') as fh:
            ast.parse(fh.read())
    except SyntaxError as e:
        errors.append(f'{f}: {e}')
if errors:
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print('ALL SYNTAX OK')
