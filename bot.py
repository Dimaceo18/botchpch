#!/usr/bin/env python3
import logging
import os
import sys
import asyncio
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# МАРШРУТ ПО МИНСКУ С ФОТОГРАФИЯМИ И СОВЕТАМИ
ROUTE = {
    1: {
        "name": "🎨 Улица Октябрьская",
        "address": "ул. Октябрьская, Минск",
        "description": "Креативное сердце Минска! Здесь расположены легендарные арт-площадки, граффити на стенах, модные бары и галереи. Это место, где старая промышленная архитектура встречается с современным стрит-артом.",
        "time": "⏰ 1-1.5 часа",
        "tips": "💡 Совет: Обязательно найдите знаменитую надпись 'Я люблю Минск' и сделайте фото!",
        "photo_tips": "📸 Лучшее место для фото: у входа в арт-центр 'Октябрьская', особенно красиво в золотой час (закат)",
        "next": 2,
        "coordinates": "53.8995, 27.5528",
        "photo": "1.jpg"
    },
    2: {
        "name": "🕰️ Барахолка на Кирова (Ретротерапия)",
        "address": "ул. Кирова, 39",
        "description": "Настоящий портал в прошлое! Здесь можно найти винтажную одежду, старые пластинки, советские значки и уникальные вещи с историей. Атмосфера настоящего минского антиквариата.",
        "time": "⏰ 1 час",
        "tips": "💡 Совет: Приходите в выходные - больше всего продавцов и интересных находок!",
        "photo_tips": "📸 Снимайте детали: старые значки, пластинки, винтажную одежду. Отлично получаются кадры в стиле ретро",
        "next": 3,
        "coordinates": "53.9035, 27.5627",
        "photo": "2.jpg"
    },
    3: {
        "name": "✨ Новые витрины ГУМа с зеркалом в прошлое",
        "address": "пр. Независимости, 21",
        "description": "Знаменитый ГУМ преобразился! Современные витрины с интерактивными зеркалами создают удивительный эффект путешествия во времени. Можно увидеть, как выглядел главный универмаг Минска в разные эпохи.",
        "time": "⏰ 30-40 мин",
        "tips": "💡 Совет: Подойдите к зеркалу - оно показывает исторические фото места, где вы стоите!",
        "photo_tips": "📸 Обязательно сфотографируйтесь у интерактивного зеркала. Лучшие кадры получаются, когда на зеркале появляется историческое фото",
        "next": 4,
        "coordinates": "53.9019, 27.5635",
        "photo": "3.jpg"
    },
    4: {
        "name": "🏨 Новая зона отдыха у Waldorf Astoria",
        "address": "пр. Победителей, 9",
        "description": "Элегантное общественное пространство у одного из самых роскошных отелей Минска. Современный ландшафтный дизайн, уютные лавочки, фонтаны и потрясающий вид на набережную Свислочи.",
        "time": "⏰ 45 мин",
        "tips": "💡 Совет: Идеальное место для закатной прогулки - открывается красивый вид на вечерний город",
        "photo_tips": "📸 Лучшее время для фото - закат. Снимайте на фоне фонтанов и набережной. Панорамные снимки получаются особенно эффектными",
        "next": 5,
        "coordinates": "53.9112, 27.5545",
        "photo": "4.jpg"
    },
    5: {
        "name": "🏛️ Дворик М15 и Осмоловке",
        "address": "ул. Осмоловка, 15",
        "description": "Уютный дворик в самом сердце города, где сохранилась атмосфера старого Минска. Аутентичные постройки, оригинальная архитектура и камерное пространство для неспешных прогулок.",
        "time": "⏰ 30-40 мин",
        "tips": "💡 Совет: Обратите внимание на детали - здесь много интересных архитектурных элементов",
        "photo_tips": "📸 Снимайте детали архитектуры, старые окна, двери. Получаются атмосферные кадры в стиле 'старого Минска'",
        "next": 6,
        "coordinates": "53.9088, 27.5589",
        "photo": "5.jpg"
    },
    6: {
        "name": "🥬 Комаровка",
        "address": "ул. Веры Хоружей, 8",
        "description": "Легендарный минский рынок с богатой историей. Здесь можно купить свежие фермерские продукты, попробовать белорусские деликатесы и прочувствовать настоящий колорит столицы.",
        "time": "⏰ 1-2 часа",
        "tips": "💡 Совет: Попробуйте местные сыры и копчености - это визитная карточка Комаровки!",
        "photo_tips": "📸 Снимайте яркие прилавки с фруктами, овощами, местными деликатесами. Получаются сочные, красочные кадры",
        "next": None,
        "coordinates": "53.9098, 27.5819",
        "photo": "6.jpg"
    }
}

def get_progress_bar(current, total):
    """Создаёт визуальную полосу прогресса"""
    filled = int(current / total * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"📊 Прогресс: [{bar}] {current}/{total}"

async def get_weather(coordinates):
    """Получает погоду для координат"""
    try:
        lat, lon = coordinates.split(', ')
        # Используем бесплатный API Open-Meteo (без ключа)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&language=ru"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'current_weather' in data:
            temp = data['current_weather']['temperature']
            wind = data['current_weather']['windspeed']
            
            # Определяем иконку погоды
            weather_icon = "☀️" if temp > 20 else "🌤️" if temp > 10 else "⛅" if temp > 0 else "❄️"
            
            return f"{weather_icon} Погода сейчас: {temp}°C, ветер {wind} м/с"
        return "🌡️ Данные о погоде временно недоступны"
    except Exception as e:
        logger.error(f"Ошибка получения погоды: {e}")
        return "🌡️ Не удалось получить данные о погоде"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    logger.info(f"📨 Получена команда /start от пользователя {update.effective_user.id}")
    user_name = update.effective_user.first_name
    
    welcome_text = (
        f"🌟 Привет, {user_name}! 🌟\n\n"
        f"Меня зовут Илья и я создал для тебя гид-бот чтобы гулять по Минску было интереснее! 🤗\n\n"
        f"Это крутой, авторский маршрут на 6 локаций на которых мы погуляем, пофоткаемся и перекусим.\n\n"
        f"Готовы отправиться в путешествие? 🚀"
    )
    
    keyboard = [
        [InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")],
        [InlineKeyboardButton("ℹ️ О маршруте", callback_data="about_route")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    logger.info("📤 Отправляю приветственное сообщение")
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый обработчик"""
    logger.info("🔧 TEST: Получено сообщение: /test")
    await update.message.reply_text("✅ Бот работает! Это тестовое сообщение.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"🔘 Получен callback: {data} от пользователя {update.effective_user.id}")
    
    if data == "start_route":
        context.user_data['current_point'] = 1
        await send_route_point(query, context, is_first=True)
    
    elif data == "about_route":
        about_text = (
            "📖 *О маршруте:*\n\n"
            "Это авторский маршрут по новым и культовым местам Минска, который включает:\n"
            "• 6 уникальных локаций\n"
            "• Современные арт-пространства\n"
            "• Исторические места с новой жизнью\n"
            "• Атмосферные уголки города\n\n"
            "✨ *Новые функции:*\n"
            "• Прогресс-бар - видите сколько осталось\n"
            "• Погода в каждой локации\n"
            "• Советы для красивых фото\n"
            "• Поделиться локацией с друзьями\n\n"
            "Общая протяженность: ~4 км\n"
            "Время прохождения: 4-6 часов\n\n"
            "Готовы начать? Нажмите 'Начать маршрут'! 🗺️"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(about_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif data == "help":
        help_text = (
            "❓ *Как пользоваться ботом:*\n\n"
            "• Нажмите 'Начать маршрут' для начала путешествия\n"
            "• Бот будет отправлять каждую точку маршрута с фото\n"
            "• 📊 Прогресс-бар показывает сколько локаций пройдено\n"
            "• 🌤️ Погода подскажет, как одеться\n"
            "• 📸 Советы по фото помогут сделать красивые снимки\n"
            "• 📤 Поделиться - отправить локацию друзьям\n"
            "• Нажмите 'Идём дальше' - появится следующая локация\n"
            "• Нажмите 'Показать на карте' - откроется Google Maps\n\n"
            "Приятной прогулки! 🌟"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif data == "next_point":
        current = context.user_data.get('current_point', 1)
        if ROUTE[current]['next']:
            context.user_data['current_point'] = ROUTE[current]['next']
            await send_route_point(query, context, is_first=False)
        else:
            await show_finish(query, context)
    
    elif data == "show_map":
        current = context.user_data.get('current_point', 1)
        if current in ROUTE:
            coords = ROUTE[current]['coordinates']
            map_url = f"https://www.google.com/maps/search/?api=1&query={coords}"
            
            await query.message.reply_text(
                f"🗺️ *Как добраться:*\n\n"
                f"[Открыть в Google Maps]({map_url})\n\n"
                f"📍 *Адрес:* {ROUTE[current]['address']}\n\n"
                f"🏛️ *Место:* {ROUTE[current]['name']}",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
    
    elif data.startswith("share_"):
        # Поделиться локацией
        point_num = int(data.split("_")[1])
        point = ROUTE[point_num]
        share_text = (
            f"📍 *{point['name']}*\n"
            f"Адрес: {point['address']}\n\n"
            f"{point['description'][:100]}...\n\n"
            f"Путешествую с ботом-гидом по Минску! 🤗\n"
            f"Начни и ты: @ваш_бот_username"
        )
        keyboard = [[InlineKeyboardButton("📤 Поделиться", switch_inline_query=share_text)]]
        await query.message.reply_text(
            "📱 *Поделиться локацией:*\n\n"
            f"{share_text}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "finish_route":
        await query.message.reply_text(
            "👋 Спасибо за прогулку по Минску!\n\n"
            "Надеюсь, вам понравился новый маршрут! "
            "Поделитесь впечатлениями в комментариях у блогера 📸\n\n"
            "Чтобы начать заново, нажмите /start"
        )

async def send_route_point(query, context: ContextTypes.DEFAULT_TYPE, is_first=False):
    """Отправляет текущую точку маршрута с фото и всеми плюшками"""
    current = context.user_data.get('current_point', 1)
    point = ROUTE[current]
    total = len(ROUTE)
    
    # Прогресс-бар
    progress_bar = get_progress_bar(current, total)
    
    # Получаем погоду
    weather = await get_weather(point['coordinates'])
    
    # Формируем текст
    text = (
        f"{progress_bar}\n\n"
        f"📍 *Точка {current} из {total}*\n\n"
        f"{point['name']}\n"
        f"📍 *Адрес:* {point['address']}\n\n"
        f"📝 *Описание:*\n{point['description']}\n\n"
        f"{point['time']}\n"
        f"{point['tips']}\n\n"
        f"{point['photo_tips']}\n\n"
        f"{weather}\n"
    )
    
    # Кнопки для текущей локации
    keyboard = []
    
    if point['next']:
        keyboard.append([InlineKeyboardButton("🚶‍♂️ Идём дальше", callback_data="next_point")])
    else:
        keyboard.append([InlineKeyboardButton("🏁 Завершить маршрут", callback_data="finish_route")])
    
    keyboard.append([InlineKeyboardButton("🗺️ Показать на карте", callback_data="show_map")])
    keyboard.append([InlineKeyboardButton("📤 Поделиться локацией", callback_data=f"share_{current}")])
    keyboard.append([InlineKeyboardButton("❌ Завершить экскурсию", callback_data="finish_route")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем фото с подписью
    photo_path = point['photo']
    
    try:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        else:
            logger.warning(f"⚠️ Фото {photo_path} не найдено")
            await query.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке фото: {e}")
        await query.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # Если это первая локация, удаляем стартовое сообщение
    if is_first:
        try:
            await query.message.delete()
            logger.info("🗑️ Стартовое сообщение удалено")
        except Exception as e:
            logger.warning(f"Не удалось удалить стартовое сообщение: {e}")

async def show_finish(query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает финальное сообщение"""
    finish_text = (
        "🎉 *Поздравляю! Вы прошли весь маршрут!* 🎉\n\n"
        "📊 *Статистика:*\n"
        "✅ Пройдено 6 из 6 локаций\n"
        "📸 Сделано отличных фото\n"
        "🌤️ Погода была прекрасной\n\n"
        "Спасибо, что путешествуете с нами по обновленному Минску!\n"
        "Надеюсь, вам открылись новые грани любимого города! 💙\n\n"
        "Поделитесь своими фотографиями в Instagram с хештегом #МинскСБлогером\n\n"
        "Чтобы пройти маршрут заново, нажмите /start"
    )
    
    keyboard = [[InlineKeyboardButton("🔄 Начать заново", callback_data="start_route")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(finish_text, reply_markup=reply_markup, parse_mode='Markdown')

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
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_handler))
    
    # Регистрируем обработчик для кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.add_error_handler(error_handler)
    
    logger.info("✅ Запускаю polling...")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("✅ Бот работает! Ожидаю сообщения...")
    logger.info("📝 Отправьте /start для начала или /test для проверки")
    
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
