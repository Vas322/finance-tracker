import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    SALARY_DAY = int(os.environ.get('SALARY_DAY', '10'))
    ADVANCE_DAY = int(os.environ.get('ADVANCE_DAY', '25'))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    DB_PATH = os.environ.get('DB_PATH', 'finance.db')
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')


SALARY_DAY = Config.SALARY_DAY
ADVANCE_DAY = Config.ADVANCE_DAY

CATEGORIES = {
    "Расход": {
        "Транспорт": ["Такси", "Метро", "Автобус", "Авиа", "ЖД", "Бензин"],
        "Продукты": ["Супермаркет", "Рынок", "Доставка", "Магазин у дома"],
        "Кафе": ["Ресторан", "Кофейня", "Бизнес-ланч", "Фастфуд"],
        "ЖКХ": ["Квартплата", "Электричество", "Вода", "Газ"],
        "Связь": ["Мобильная связь", "Интернет", "VPN"],
        "Развлечения": ["Кино", "Игры", "Концерты", "Подписки"],
        "Здоровье": ["Аптека", "Врачи", "Спорт", "Анализы"],
        "Одежда": ["Обувь", "Одежда", "Аксессуары"],
        "Другое": [""]
    },
    "Доход": {
        "Зарплата": ["Основная", "Премия", "Подработка"],
        "Фриланс": ["Проекты", "Консультации"],
        "Подарки": ["Семье", "Друзьям"],
        "Кэшбэк": ["Банк", "Карта"],
        "Другое": [""]
    }
}
