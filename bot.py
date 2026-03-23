#!/usr/bin/env python3
"""
Telegram бот-гид по Минску
"""

import sys
import logging
import os
import platform
from datetime import datetime

# Проверка версии Python
REQUIRED_PYTHON = (3, 8, 0)
CURRENT_PYTHON = sys.version_info

if CURRENT_PYTHON < REQUIRED_PYTHON:
    print(f"❌ Ошибка: Требуется Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+")
    print(f"Текущая версия: {platform.python_version()}")
    sys.exit(1)

# Проверка на нестабильные версии
if CURRENT_PYTHON >= (3, 13, 0):
    print(f"⚠️  Внимание: Python {platform.python_version()} может быть нестабильным")
    print("Рекомендуется Python 3.11 или 3.12")

try:
    import telegram
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
    print(f"✅ python-telegram-bot версия: {telegram.__version__}")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Запустите: pip install -r requirements.txt")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Выводим информацию о запуске
logger.info("=" * 50)
logger.info("🤖 Telegram Bot - Маршрут по Минску")
logger.info(f"🐍 Python: {platform.python_version()}")
logger.info(f"📦 python-telegram-bot: {telegram.__version__}")
logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 50)

# Состояния для ConversationHandler
SELECTING_ACTION, SHOWING_POINT = range(2)

# Данные маршрута по Минску
ROUTE = {
    1: {
        "name": "📍 Национальная библиотека",
        "address": "пр. Независимости, 116",
        "description": "🏛️ Легендарный алмаз знаний. Начните с самой iconic достопримечательности Минска. Поднимитесь на смотровую площадку (22 этаж) для панорамного вида на город.",
        "time": "⏰ 1-1.5 часа",
        "tips": "💡 Совет: Приходите к закату - виды потрясающие!",
        "next": 2,
        "coordinates": "53.9317, 27.6459"
    },
    2: {
        "name": "🎭 Верхний город",
        "address": "ул. Интернациональная, пл. Свободы",
        "description": "Историческое сердце Минска: Ратуша, Кафедральный собор, Костел Святого Симеона и Елены (Красный костел). Атмосферные улочки и архитектура XVII-XIX веков.",
        "time": "⏰ 2-3 часа",
        "tips": "💡 Совет: Загляните в кафе 'Бернардинский дворик' на обед",
        "next": 3,
        "coordinates": "53.9045, 27.5556"
    },
    3: {
        "name": "🚶‍♂️ Троицкое предместье",
        "address": "ул. Троицкая, 1",
        "description": "Отреставрированный исторический квартал на берегу Свислочи. Брусчатка, уютные домики, музеи. Отличное место для фотосессий и неспешных прогулок.",
        "time": "⏰ 1-1.5 часа",
        "tips": "💡 Совет: Попробуйте драники в ресторане 'Троицкий'",
        "next": 4,
        "coordinates": "53.9083, 27.5547"
    },
    4: {
        "name": "🏰 Остров слез",
        "address": "парк ул. Янки Купалы",
        "description": "Мемориальный комплекс 'Сыновьям Отечества, погибшим за его пределами'. Эмоциональное место с часовней и скульптурами.",
        "time": "⏰ 30-40 мин",
        "tips": "💡 Совет: Вечером включается подсветка - очень атмосферно",
        "next": 5,
        "coordinates": "53.9107, 27.5568"
    },
    5: {
        "name": "🌳 Парк Горького",
        "address": "ул. Фрунзе, 2",
        "description": "Центральный парк с аттракционами, колесом обозрения и уютными аллеями. Отличное место для отдыха после насыщенной прогулки.",
        "time": "⏰ 1-2 часа",
        "tips": "💡 Совет: Прокатитесь на колесе обозрения",
        "next": 6,
        "coordinates": "53.9019, 27.5710"
    },
    6: {
        "name": "🎨 Октябрьская улица",
        "address": "ул. Октябрьская",
        "description": "Креативный кластер Минска. Стрит-арт, граффити, бары, арт-галереи. Современное лицо города.",
        "time": "⏰ 1.5-2 часа",
        "tips": "💡 Совет: Завершите вечер в одном из локальных баров",
        "next": None,
        "coordinates": "53.8995, 27.5528"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user_name = update.effective_user.first_name
    
    welcome_text = (
        f"🌟 Привет, {user_name}! 🌟\n\n"
        f"Я бот-гид по Минску от вашего любимого блогера! 🤗\n\n"
        f"Я помогу вам пройти уникальный маршрут по самым интересным местам столицы Беларуси.\n\n"
        f"Готовы начать путешествие? 🚀"
    )
    
    keyboard = [
        [InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")],
        [InlineKeyboardButton("ℹ️ О маршруте", callback_data="about_route")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return SELECTING_ACTION

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "start_route":
        context.user_data['current_point'] = 1
        await show_route_point(query, context)
        return SHOWING_POINT
    
    elif data == "about_route":
        about_text = (
            "📖 *О маршруте:*\n\n"
            "Это авторский маршрут по Минску, который включает:\n"
            "• 6 ключевых достопримечательностей\n"
            "• Оптимальный маршрут для прогулки\n"
            "• Интересные факты и советы\n"
            "• Рекомендации по времени\n"
            "• Подсказки для фото\n\n"
            "Общая протяженность: ~5 км\n"
            "Время прохождения: 4-6 часов\n\n"
            "Готовы начать? Нажмите 'Начать маршрут'! 🗺️"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(about_text, reply_markup=reply_markup, parse_mode='Markdown')
        return SELECTING_ACTION
    
    elif data == "help":
        help_text = (
            "❓ *Как пользоваться ботом:*\n\n"
            "• Нажмите 'Начать маршрут' для начала путешествия\n"
            "• Бот будет показывать точки маршрута по очереди\n"
            "• Используйте кнопки для навигации\n"
            "• Можете посмотреть местоположение на карте\n"
            "• В любой момент можете завершить маршрут\n\n"
            "Если остались вопросы - задавайте их блогеру в Instagram! 📱"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
        return SELECTING_ACTION
    
    elif data == "next_point":
        current = context.user_data.get('current_point', 1)
        if current in ROUTE and ROUTE[current]['next']:
            context.user_data['current_point'] = ROUTE[current]['next']
            await show_route_point(query, context)
        else:
            await show_finish(query, context)
            return ConversationHandler.END
    
    elif data == "show_map":
        current = context.user_data.get('current_point', 1)
        if current in ROUTE:
            coords = ROUTE[current]['coordinates']
            map_url = f"https://www.google.com/maps/search/?api=1&query={coords}"
            await query.edit_message_text(
                f"🗺️ *Как добраться:*\n\n"
                f"[Открыть в Google Maps]({map_url})\n\n"
                f"📍 {ROUTE[current]['address']}",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            await show_route_point(query, context)
    
    elif data == "finish_route":
        await query.edit_message_text(
            "👋 Спасибо за прогулку по Минску!\n\n"
            "Надеюсь, вам понравился маршрут! "
            "Поделитесь впечатлениями в комментариях у блогера 📸\n\n"
            "Чтобы начать заново, нажмите /start"
        )
        return ConversationHandler.END
    
    return SHOWING_POINT

async def show_route_point(query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущую точку маршрута"""
    current = context.user_data.get('current_point', 1)
    point = ROUTE[current]
    
    text = (
        f"📍 *Точка {current} из 6*\n\n"
        f"🏛️ *{point['name']}*\n"
        f"📍 *Адрес:* {point['address']}\n\n"
        f"📝 *Описание:*\n{point['description']}\n\n"
        f"{point['time']}\n"
        f"{point['tips']}\n"
    )
    
    keyboard = []
    
    if point['next']:
        keyboard.append([InlineKeyboardButton("➡️ Следующая точка", callback_data="next_point")])
    else:
        keyboard.append([InlineKeyboardButton("🏁 Завершить маршрут", callback_data="finish_route")])
    
    keyboard.append([InlineKeyboardButton("🗺️ Показать на карте", callback_data="show_map")])
    keyboard.append([InlineKeyboardButton("❌ Завершить экскурсию", callback_data="finish_route")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_finish(query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает финальное сообщение"""
    finish_text = (
        "🎉 *Поздравляю! Вы прошли весь маршрут!* 🎉\n\n"
        "Спасибо, что путешествуете с нами!\n"
        "Надеюсь, вам понравился Минск так же, как и мне! 💙\n\n"
        "Поделитесь своими фотографиями в Instagram с хештегом #МинскСБлогером\n\n"
        "Чтобы пройти маршрут заново, нажмите /start"
    )
    
    keyboard = [[InlineKeyboardButton("🔄 Начать заново", callback_data="start_route")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(finish_text, reply_markup=reply_markup, parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена маршрута"""
    await update.message.reply_text(
        "👋 Маршрут прерван. Если захотите продолжить, просто нажмите /start"
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"❌ Ошибка: {context.error}", exc_info=True)

def main():
    """Запуск бота"""
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("❌ Токен бота не найден в переменных окружения!")
        sys.exit(1)
    
    logger.info("✅ Токен найден")
    logger.info("🤖 Создаю приложение...")
    
    try:
        # Создаем приложение с явными параметрами
        application = (
            Application.builder()
            .token(TOKEN)
            .concurrent_updates(True)  # Включаем поддержку конкурентных обновлений
            .build()
        )
        
        # Добавляем обработчики
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                SELECTING_ACTION: [
                    CallbackQueryHandler(button_handler, pattern='^(start_route|about_route|help)$')
                ],
                SHOWING_POINT: [
                    CallbackQueryHandler(button_handler, pattern='^(next_point|show_map|finish_route)$')
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True  # Разрешаем повторный вход в диалог
        )
        
        application.add_handler(conv_handler)
        application.add_error_handler(error_handler)
        
        logger.info("✅ Обработчики добавлены")
        logger.info("🚀 Запускаю polling...")
        
        # Запускаем polling с базовыми настройками
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            stop_signals=None  # Отключаем сигналы для совместимости
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
