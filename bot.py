#!/usr/bin/env python3
import logging
import os
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

# Настройка подробного логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Меняем INFO на DEBUG для деталей
)
logger = logging.getLogger(__name__)

SELECTING_ACTION, SHOWING_POINT = range(2)

ROUTE = {
    1: {
        "name": "📍 Национальная библиотека",
        "address": "пр. Независимости, 116",
        "description": "🏛️ Легендарный алмаз знаний. Поднимитесь на смотровую площадку.",
        "time": "⏰ 1-1.5 часа",
        "tips": "💡 Совет: Приходите к закату",
        "next": 2,
        "coordinates": "53.9317, 27.6459"
    },
    2: {
        "name": "🎭 Верхний город",
        "address": "ул. Интернациональная, пл. Свободы",
        "description": "Историческое сердце Минска: Ратуша, Кафедральный собор.",
        "time": "⏰ 2-3 часа",
        "tips": "💡 Совет: Загляните в кафе 'Бернардинский дворик'",
        "next": 3,
        "coordinates": "53.9045, 27.5556"
    },
    3: {
        "name": "🚶‍♂️ Троицкое предместье",
        "address": "ул. Троицкая, 1",
        "description": "Отреставрированный исторический квартал на берегу Свислочи.",
        "time": "⏰ 1-1.5 часа",
        "tips": "💡 Совет: Попробуйте драники в ресторане 'Троицкий'",
        "next": 4,
        "coordinates": "53.9083, 27.5547"
    },
    4: {
        "name": "🏰 Остров слез",
        "address": "парк ул. Янки Купалы",
        "description": "Мемориальный комплекс 'Сыновьям Отечества, погибшим за его пределами'.",
        "time": "⏰ 30-40 мин",
        "tips": "💡 Совет: Вечером включается подсветка",
        "next": 5,
        "coordinates": "53.9107, 27.5568"
    },
    5: {
        "name": "🌳 Парк Горького",
        "address": "ул. Фрунзе, 2",
        "description": "Центральный парк с аттракционами и колесом обозрения.",
        "time": "⏰ 1-2 часа",
        "tips": "💡 Совет: Прокатитесь на колесе обозрения",
        "next": 6,
        "coordinates": "53.9019, 27.5710"
    },
    6: {
        "name": "🎨 Октябрьская улица",
        "address": "ул. Октябрьская",
        "description": "Креативный кластер Минска. Стрит-арт, бары, арт-галереи.",
        "time": "⏰ 1.5-2 часа",
        "tips": "💡 Совет: Завершите вечер в локальном баре",
        "next": None,
        "coordinates": "53.8995, 27.5528"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    logger.info(f"📨 Получена команда /start от пользователя {update.effective_user.id}")
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
    
    logger.info("📤 Отправляю приветственное сообщение")
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_ACTION

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    logger.info(f"🔘 Получен callback: {query.data} от пользователя {update.effective_user.id}")
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
            "• Интересные факты и советы\n\n"
            "Общая протяженность: ~5 км\n"
            "Время прохождения: 4-6 часов"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(about_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return SELECTING_ACTION
    elif data == "help":
        help_text = (
            "❓ *Как пользоваться ботом:*\n\n"
            "• Нажмите 'Начать маршрут' для начала путешествия\n"
            "• Бот будет показывать точки маршрута по очереди\n"
            "• Используйте кнопки для навигации\n"
            "• Можете посмотреть местоположение на карте"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return SELECTING_ACTION
    elif data == "next_point":
        current = context.user_data.get('current_point', 1)
        if ROUTE[current]['next']:
            context.user_data['current_point'] = ROUTE[current]['next']
            await show_route_point(query, context)
        else:
            await show_finish(query, context)
            return ConversationHandler.END
    elif data == "show_map":
        current = context.user_data.get('current_point', 1)
        coords = ROUTE[current]['coordinates']
        map_url = f"https://www.google.com/maps/search/?api=1&query={coords}"
        await query.edit_message_text(
            f"🗺️ *Как добраться:*\n\n[Открыть в Google Maps]({map_url})\n\n📍 {ROUTE[current]['address']}",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        await show_route_point(query, context)
    elif data == "finish_route":
        await query.edit_message_text(
            "👋 Спасибо за прогулку по Минску!\n\n"
            "Поделитесь впечатлениями в Instagram с хештегом #МинскСБлогером\n\n"
            "Чтобы начать заново, нажмите /start"
        )
        return ConversationHandler.END
    return SHOWING_POINT

async def show_route_point(query, context: ContextTypes.DEFAULT_TYPE):
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
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_finish(query, context: ContextTypes.DEFAULT_TYPE):
    finish_text = (
        "🎉 *Поздравляю! Вы прошли весь маршрут!* 🎉\n\n"
        "Спасибо за путешествие! 💙"
    )
    keyboard = [[InlineKeyboardButton("🔄 Начать заново", callback_data="start_route")]]
    await query.edit_message_text(finish_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Маршрут прерван. Для начала нажмите /start")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ Ошибка: {context.error}", exc_info=True)

async def run_bot():
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ Токен не найден!")
        return
    
    logger.info("✅ Бот запускается...")
    
    application = Application.builder().token(TOKEN).build()
    
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
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Запускаю polling...")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("✅ Бот работает! Ожидаю сообщения...")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Остановка бота...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def main():
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(run_bot())
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
