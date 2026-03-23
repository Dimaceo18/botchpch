#!/usr/bin/env python3
import logging
import os
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SELECTING_ACTION, SHOWING_POINT = range(2)

# НОВЫЙ МАРШРУТ ПО МИНСКУ
ROUTE = {
    1: {
        "name": "🎨 Улица Октябрьская",
        "address": "ул. Октябрьская, Минск",
        "description": "Креативное сердце Минска! Здесь расположены легендарные арт-площадки, граффити на стенах, модные бары и галереи. Это место, где старая промышленная архитектура встречается с современным стрит-артом.",
        "time": "⏰ 1-1.5 часа",
        "tips": "💡 Совет: Обязательно найдите знаменитую надпись 'Я люблю Минск' и сделайте фото!",
        "next": 2,
        "coordinates": "53.8995, 27.5528"
    },
    2: {
        "name": "🕰️ Барахолка на Кирова (Ретротерапия)",
        "address": "ул. Кирова, 39",
        "description": "Настоящий портал в прошлое! Здесь можно найти винтажную одежду, старые пластинки, советские значки и уникальные вещи с историей. Атмосфера настоящего минского антиквариата.",
        "time": "⏰ 1 час",
        "tips": "💡 Совет: Приходите в выходные - больше всего продавцов и интересных находок!",
        "next": 3,
        "coordinates": "53.9035, 27.5627"
    },
    3: {
        "name": "✨ Новые витрины ГУМа с зеркалом в прошлое",
        "address": "пр. Независимости, 21",
        "description": "Знаменитый ГУМ преобразился! Современные витрины с интерактивными зеркалами создают удивительный эффект путешествия во времени. Можно увидеть, как выглядел главный универмаг Минска в разные эпохи.",
        "time": "⏰ 30-40 мин",
        "tips": "💡 Совет: Подойдите к зеркалу - оно показывает исторические фото места, где вы стоите!",
        "next": 4,
        "coordinates": "53.9019, 27.5635"
    },
    4: {
        "name": "🏨 Новая зона отдыха у Waldorf Astoria",
        "address": "пр. Победителей, 9",
        "description": "Элегантное общественное пространство у одного из самых роскошных отелей Минска. Современный ландшафтный дизайн, уютные лавочки, фонтаны и потрясающий вид на набережную Свислочи.",
        "time": "⏰ 45 мин",
        "tips": "💡 Совет: Идеальное место для закатной прогулки - открывается красивый вид на вечерний город",
        "next": 5,
        "coordinates": "53.9112, 27.5545"
    },
    5: {
        "name": "🏛️ Дворик М15 и Осмоловке",
        "address": "ул. Осмоловка, 15",
        "description": "Уютный дворик в самом сердце города, где сохранилась атмосфера старого Минска. Аутентичные постройки, оригинальная архитектура и камерное пространство для неспешных прогулок.",
        "time": "⏰ 30-40 мин",
        "tips": "💡 Совет: Обратите внимание на детали - здесь много интересных архитектурных элементов",
        "next": 6,
        "coordinates": "53.9088, 27.5589"
    },
    6: {
        "name": "🥬 Комаровка",
        "address": "ул. Веры Хоружей, 8",
        "description": "Легендарный минский рынок с богатой историей. Здесь можно купить свежие фермерские продукты, попробовать белорусские деликатесы и прочувствовать настоящий колорит столицы.",
        "time": "⏰ 1-2 часа",
        "tips": "💡 Совет: Попробуйте местные сыры и копчености - это визитная карточка Комаровки!",
        "next": None,
        "coordinates": "53.9098, 27.5819"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    logger.info(f"📨 Получена команда /start от пользователя {update.effective_user.id}")
    user_name = update.effective_user.first_name
    
    welcome_text = (
        f"🌟 Привет, {user_name}! 🌟\n\n"
        f"Я бот-гид по Минску от вашего любимого блогера! 🤗\n\n"
        f"Я подготовил для вас новый уникальный маршрут по самым интересным местам столицы Беларуси.\n\n"
        f"Готовы отправиться в путешествие? 🚀"
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
        # Отправляем первую локацию новым сообщением
        await send_route_point(query.message.chat_id, context, query)
        return SHOWING_POINT
    
    elif data == "about_route":
        about_text = (
            "📖 *О маршруте:*\n\n"
            "Это авторский маршрут по новым и культовым местам Минска, который включает:\n"
            "• 6 уникальных локаций\n"
            "• Современные арт-пространства\n"
            "• Исторические места с новой жизнью\n"
            "• Атмосферные уголки города\n\n"
            "Общая протяженность: ~4 км\n"
            "Время прохождения: 4-6 часов\n\n"
            "Готовы начать? Нажмите 'Начать маршрут'! 🗺️"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(about_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return SELECTING_ACTION
    
    elif data == "help":
        help_text = (
            "❓ *Как пользоваться ботом:*\n\n"
            "• Нажмите 'Начать маршрут' для начала путешествия\n"
            "• Бот будет отправлять каждую точку маршрута новым сообщением\n"
            "• Нажмите 'Идём дальше' - появится следующая локация\n"
            "• Нажмите 'Показать на карте' - откроется Google Maps\n"
            "• В любой момент можете завершить маршрут\n\n"
            "Приятной прогулки! 🌟"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return SELECTING_ACTION
    
    elif data == "next_point":
        current = context.user_data.get('current_point', 1)
        if ROUTE[current]['next']:
            context.user_data['current_point'] = ROUTE[current]['next']
            # Отправляем следующую локацию новым сообщением
            await send_route_point(query.message.chat_id, context, query)
        else:
            await show_finish(query.message.chat_id, context, query)
            return ConversationHandler.END
        return SHOWING_POINT
    
    elif data == "show_map":
        current = context.user_data.get('current_point', 1)
        if current in ROUTE:
            coords = ROUTE[current]['coordinates']
            map_url = f"https://www.google.com/maps/search/?api=1&query={coords}"
            
            # Отправляем новое сообщение с картой
            await query.message.reply_text(
                f"🗺️ *Как добраться:*\n\n"
                f"[Открыть в Google Maps]({map_url})\n\n"
                f"📍 *Адрес:* {ROUTE[current]['address']}\n\n"
                f"🏛️ *Место:* {ROUTE[current]['name']}",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
    
    elif data == "finish_route":
        await query.message.reply_text(
            "👋 Спасибо за прогулку по Минску!\n\n"
            "Надеюсь, вам понравился новый маршрут! "
            "Поделитесь впечатлениями в комментариях у блогера 📸\n\n"
            "Чтобы начать заново, нажмите /start"
        )
        # Удаляем сообщение с кнопками, если нужно
        try:
            await query.message.delete()
        except:
            pass
        return ConversationHandler.END
    
    return SHOWING_POINT

async def send_route_point(chat_id, context: ContextTypes.DEFAULT_TYPE, query=None):
    """Отправляет текущую точку маршрута новым сообщением"""
    current = context.user_data.get('current_point', 1)
    point = ROUTE[current]
    total = len(ROUTE)
    
    text = (
        f"📍 *Точка {current} из {total}*\n\n"
        f"{point['name']}\n"
        f"📍 *Адрес:* {point['address']}\n\n"
        f"📝 *Описание:*\n{point['description']}\n\n"
        f"{point['time']}\n"
        f"{point['tips']}\n"
    )
    
    # Создаем кнопки
    keyboard = []
    
    if point['next']:
        keyboard.append([InlineKeyboardButton("🚶‍♂️ Идём дальше", callback_data="next_point")])
    else:
        keyboard.append([InlineKeyboardButton("🏁 Завершить маршрут", callback_data="finish_route")])
    
    keyboard.append([InlineKeyboardButton("🗺️ Показать на карте", callback_data="show_map")])
    keyboard.append([InlineKeyboardButton("❌ Завершить экскурсию", callback_data="finish_route")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем новое сообщение
    if query:
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        # Удаляем предыдущее сообщение с кнопками (опционально)
        try:
            await query.message.delete()
        except:
            pass
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_finish(chat_id, context: ContextTypes.DEFAULT_TYPE, query=None):
    """Показывает финальное сообщение"""
    finish_text = (
        "🎉 *Поздравляю! Вы прошли весь маршрут!* 🎉\n\n"
        "Спасибо, что путешествуете с нами по обновленному Минску!\n"
        "Надеюсь, вам открылись новые грани любимого города! 💙\n\n"
        "Поделитесь своими фотографиями в Instagram с хештегом #МинскСБлогером\n\n"
        "Чтобы пройти маршрут заново, нажмите /start"
    )
    
    keyboard = [[InlineKeyboardButton("🔄 Начать заново", callback_data="start_route")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.message.reply_text(finish_text, reply_markup=reply_markup, parse_mode='Markdown')
        # Удаляем последнее сообщение с точкой
        try:
            await query.message.delete()
        except:
            pass
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=finish_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена маршрута"""
    await update.message.reply_text(
        "👋 Маршрут прерван. Если захотите продолжить, просто нажмите /start"
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"❌ Ошибка: {context.error}", exc_info=True)

async def run_bot():
    """Запуск бота"""
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ Токен не найден!")
        return
    
    logger.info("✅ Бот запускается...")
    
    application = Application.builder().token(TOKEN).build()
    
    # Тестовый обработчик для проверки работы
    async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f"🔧 TEST: Получено сообщение: {update.message.text}")
        await update.message.reply_text("✅ Бот работает! Это тестовое сообщение.")
    
    application.add_handler(CommandHandler("test", test_handler))
    
    # Основной ConversationHandler
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
    logger.info("📝 Отправьте /test для проверки или /start для начала маршрута")
    
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
