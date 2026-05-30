from flask import Flask
from routes import main, operations, regular, settings, categories

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Регистрируем все маршруты
main.register_routes(app)
operations.register_routes(app)
regular.register_routes(app)
settings.register_routes(app)
categories.register_routes(app)

if __name__ == '__main__':
    from database import init_db
    init_db()
    app.run(debug=True)