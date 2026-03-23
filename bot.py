#!/usr/bin/env python3
import logging
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния
SELECTING_ACTION, SHOWING_POINT = range(2)

# Данные маршрута (те же самые)
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
    user_name = update.effective_user.first_name
    welcome_text = (
        f"🌟 Привет, {user_name}! 🌟\n\n"
        f"Я бот-гид по Минску 🤗\n\n"
        f"Готовы начать путешествие? 🚀"
    )
    keyboard = [
        [InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")],
        [InlineKeyboardButton("ℹ️ О маршруте", callback_data="about_route")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_ACTION

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "start_route":
        context.user_data['current_point'] = 1
        await show_route_point(query, context)
        return SHOWING_POINT
    elif data == "about_route":
        about_text = "📖 *О маршруте:*\n\n6 ключевых достопримечательностей\nОбщая протяженность: ~5 км\nВремя прохождения: 4-6 часов"
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(about_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return SELECTING_ACTION
    elif data == "help":
        help_text = "❓ *Как пользоваться:*\n\n• Нажмите 'Начать маршрут'\n• Бот покажет точки по очереди\n• Используйте кнопки для навигации"
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
        await query.edit_message_text(f"🗺️ [Открыть карту]({map_url})\n\n📍 {ROUTE[current]['address']}", parse_mode='Markdown', disable_web_page_preview=True)
        await show_route_point(query, context)
    elif data == "finish_route":
        await query.edit_message_text("👋 Спасибо за прогулку! Чтобы начать заново, нажмите /start")
        return ConversationHandler.END
    return SHOWING_POINT

async def show_route_point(query, context: ContextTypes.DEFAULT_TYPE):
    current = context.user_data.get('current_point', 1)
    point = ROUTE[current]
    text = f"📍 *Точка {current} из 6*\n\n🏛️ *{point['name']}*\n📍 *Адрес:* {point['address']}\n\n📝 *Описание:*\n{point['description']}\n\n{point['time']}\n{point['tips']}"
    
    keyboard = []
    if point['next']:
        keyboard.append([InlineKeyboardButton("➡️ Следующая точка", callback_data="next_point")])
    else:
        keyboard.append([InlineKeyboardButton("🏁 Завершить маршрут", callback_data="finish_route")])
    keyboard.append([InlineKeyboardButton("🗺️ Показать на карте", callback_data="show_map")])
    keyboard.append([InlineKeyboardButton("❌ Завершить экскурсию", callback_data="finish_route")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_finish(query, context: ContextTypes.DEFAULT_TYPE):
    finish_text = "🎉 *Поздравляю! Вы прошли весь маршрут!* 🎉\n\nСпасибо за путешествие! 💙"
    keyboard = [[InlineKeyboardButton("🔄 Начать заново", callback_data="start_route")]]
    await query.edit_message_text(finish_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Маршрут прерван. Для начала нажмите /start")
    return ConversationHandler.END

def main():
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ Токен не найден!")
        sys.exit(1)
    
    logger.info("✅ Бот запускается...")
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [CallbackQueryHandler(button_handler, pattern='^(start_route|about_route|help)$')],
            SHOWING_POINT: [CallbackQueryHandler(button_handler, pattern='^(next_point|show_map|finish_route)$')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    logger.info("✅ Запускаю polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
