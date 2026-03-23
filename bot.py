#!/usr/bin/env python3
import logging
import os
import sys
import asyncio
import requests
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
def init_db():
    """Создаёт таблицы для хранения рейтингов"""
    conn = sqlite3.connect('ratings.db')
    c = conn.cursor()
    
    # Таблица для рейтингов локаций
    c.execute('''CREATE TABLE IF NOT EXISTS location_ratings
                 (location_id INTEGER, user_id INTEGER, rating INTEGER, 
                  date TEXT, PRIMARY KEY (location_id, user_id))''')
    
    # Таблица для средних рейтингов
    c.execute('''CREATE TABLE IF NOT EXISTS location_avg_ratings
                 (location_id INTEGER PRIMARY KEY, avg_rating REAL, votes_count INTEGER)''')
    
    conn.commit()
    conn.close()
    logger.info("✅ База данных рейтингов инициализирована")

def save_rating(location_id, user_id, rating):
    """Сохраняет оценку пользователя"""
    conn = sqlite3.connect('ratings.db')
    c = conn.cursor()
    
    # Сохраняем оценку
    c.execute('''INSERT OR REPLACE INTO location_ratings 
                 (location_id, user_id, rating, date) 
                 VALUES (?, ?, ?, ?)''',
              (location_id, user_id, rating, datetime.now().isoformat()))
    
    # Обновляем средний рейтинг
    c.execute('''SELECT AVG(rating), COUNT(*) FROM location_ratings 
                 WHERE location_id = ?''', (location_id,))
    avg_rating, votes_count = c.fetchone()
    
    c.execute('''INSERT OR REPLACE INTO location_avg_ratings 
                 (location_id, avg_rating, votes_count) 
                 VALUES (?, ?, ?)''',
              (location_id, avg_rating or 0, votes_count or 0))
    
    conn.commit()
    conn.close()
    return avg_rating or 0, votes_count or 0

def get_rating(location_id):
    """Получает средний рейтинг локации"""
    conn = sqlite3.connect('ratings.db')
    c = conn.cursor()
    c.execute('SELECT avg_rating, votes_count FROM location_avg_ratings WHERE location_id = ?', 
              (location_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (0, 0)

def get_user_rating(location_id, user_id):
    """Получает оценку пользователя для локации"""
    conn = sqlite3.connect('ratings.db')
    c = conn.cursor()
    c.execute('SELECT rating FROM location_ratings WHERE location_id = ? AND user_id = ?', 
              (location_id, user_id))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# МАРШРУТ ПО МИНСКУ
ROUTE = {
    1: {
        "name": "🎨 Улица Октябрьская",
        "address": "ул. Октябрьская, Минск",
        "description": "Креативное сердце Минска! Здесь расположены легендарные арт-площадки, граффити на стенах, модные бары и галереи.",
        "time": "⏰ 1-1.5 часа",
        "tips": "💡 Совет: Обязательно найдите знаменитую надпись 'Я люблю Минск' и сделайте фото!",
        "photo_tips": "📸 Лучшее место для фото: у входа в арт-центр 'Октябрьская'",
        "next": 2,
        "coordinates": "53.8995, 27.5528",
        "photo": "1.jpg"
    },
    2: {
        "name": "🕰️ Барахолка на Кирова (Ретротерапия)",
        "address": "ул. Кирова, 39",
        "description": "Настоящий портал в прошлое! Здесь можно найти винтажную одежду, старые пластинки, советские значки.",
        "time": "⏰ 1 час",
        "tips": "💡 Совет: Приходите в выходные - больше всего продавцов!",
        "photo_tips": "📸 Снимайте детали: старые значки, пластинки, винтажную одежду",
        "next": 3,
        "coordinates": "53.9035, 27.5627",
        "photo": "2.jpg"
    },
    3: {
        "name": "✨ Новые витрины ГУМа",
        "address": "пр. Независимости, 21",
        "description": "Знаменитый ГУМ преобразился! Современные витрины с интерактивными зеркалами.",
        "time": "⏰ 30-40 мин",
        "tips": "💡 Совет: Подойдите к зеркалу - оно показывает исторические фото!",
        "photo_tips": "📸 Сфотографируйтесь у интерактивного зеркала",
        "next": 4,
        "coordinates": "53.9019, 27.5635",
        "photo": "3.jpg"
    },
    4: {
        "name": "🏨 Waldorf Astoria",
        "address": "пр. Победителей, 9",
        "description": "Элегантное общественное пространство, фонтаны и вид на набережную.",
        "time": "⏰ 45 мин",
        "tips": "💡 Совет: Идеальное место для закатной прогулки",
        "photo_tips": "📸 Лучшее время для фото - закат",
        "next": 5,
        "coordinates": "53.9112, 27.5545",
        "photo": "4.jpg"
    },
    5: {
        "name": "🏛️ Дворик М15 и Осмоловке",
        "address": "ул. Осмоловка, 15",
        "description": "Уютный дворик с атмосферой старого Минска.",
        "time": "⏰ 30-40 мин",
        "tips": "💡 Совет: Обратите внимание на детали архитектуры",
        "photo_tips": "📸 Снимайте детали: старые окна, двери",
        "next": 6,
        "coordinates": "53.9088, 27.5589",
        "photo": "5.jpg"
    },
    6: {
        "name": "🥬 Комаровка",
        "address": "ул. Веры Хоружей, 8",
        "description": "Легендарный рынок с богатой историей. Местные сыры и деликатесы.",
        "time": "⏰ 1-2 часа",
        "tips": "💡 Совет: Попробуйте местные сыры и копчености!",
        "photo_tips": "📸 Снимайте яркие прилавки с продуктами",
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

def get_star_rating(rating):
    """Преобразует числовой рейтинг в звёздочки"""
    if rating == 0:
        return "⭐ Нет оценок"
    full_stars = int(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    stars = "★" * full_stars + "½" * half_star + "☆" * empty_stars
    return f"{stars} {rating:.1f}"

async def get_weather(coordinates):
    """Получает погоду для координат"""
    try:
        lat, lon = coordinates.split(', ')
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'current_weather' in data:
            temp = data['current_weather']['temperature']
            weather_icon = "☀️" if temp > 20 else "🌤️" if temp > 10 else "⛅" if temp > 0 else "❄️"
            return f"{weather_icon} {temp}°C"
        return "🌡️ Нет данных"
    except Exception as e:
        return "🌡️ Нет данных"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_name = update.effective_user.first_name
    
    welcome_text = (
        f"🌟 Привет, {user_name}! 🌟\n\n"
        f"Меня зовут Илья и я создал для тебя гид-бот! 🤗\n\n"
        f"Это авторский маршрут на 6 локаций.\n\n"
        f"Готов отправиться в путешествие? 🚀"
    )
    
    keyboard = [
        [InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")],
        [InlineKeyboardButton("⭐ Топ локаций", callback_data="top_ratings")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    
    if data == "start_route":
        context.user_data['current_point'] = 1
        await send_route_point(query, context, is_first=True)
    
    elif data == "top_ratings":
        # Показываем топ локаций по рейтингу
        ratings = []
        for loc_id, point in ROUTE.items():
            avg_rating, votes = get_rating(loc_id)
            ratings.append((point['name'], avg_rating, votes, loc_id))
        
        ratings.sort(key=lambda x: x[1], reverse=True)
        
        text = "⭐ *Топ локаций по рейтингу:*\n\n"
        for i, (name, rating, votes, loc_id) in enumerate(ratings[:5], 1):
            stars = get_star_rating(rating)
            text += f"{i}. {name}\n   {stars} ({votes} оценок)\n\n"
        
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif data == "help":
        help_text = (
            "❓ *Как пользоваться:*\n\n"
            "• Нажмите 'Начать маршрут'\n"
            "• Оценивайте каждую локацию ⭐\n"
            "• Смотрите топ локаций в меню\n"
            "• Делитесь впечатлениями!"
        )
        keyboard = [[InlineKeyboardButton("🗺️ Начать маршрут", callback_data="start_route")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif data.startswith("rate_"):
        # Обработка оценки
        parts = data.split("_")
        location_id = int(parts[1])
        rating = int(parts[2])
        
        avg_rating, votes_count = save_rating(location_id, user_id, rating)
        
        await query.edit_message_text(
            f"✅ Спасибо за оценку!\n\n"
            f"⭐ Ваша оценка: {rating}/5\n"
            f"📊 Средний рейтинг: {get_star_rating(avg_rating)} ({votes_count} оценок)",
            parse_mode='Markdown'
        )
        
        # Возвращаемся к локации
        context.user_data['current_point'] = location_id
        await send_route_point(query, context, is_first=False)
    
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
                f"🗺️ [Открыть карту]({map_url})\n\n📍 {ROUTE[current]['address']}",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
    
    elif data.startswith("share_"):
        point_num = int(data.split("_")[1])
        point = ROUTE[point_num]
        share_text = f"📍 {point['name']}\nАдрес: {point['address']}\n\nПутешествую с ботом-гидом по Минску! 🤗"
        await query.message.reply_text(f"📱 *Поделиться:*\n\n{share_text}", parse_mode='Markdown')
    
    elif data == "finish_route":
        await query.message.reply_text(
            "👋 Спасибо за прогулку! Чтобы начать заново, нажмите /start"
        )

async def send_route_point(query, context: ContextTypes.DEFAULT_TYPE, is_first=False):
    current = context.user_data.get('current_point', 1)
    point = ROUTE[current]
    total = len(ROUTE)
    user_id = query.from_user.id
    
    # Получаем рейтинг локации
    avg_rating, votes_count = get_rating(current)
    user_rating = get_user_rating(current, user_id)
    
    # Прогресс-бар
    progress_bar = get_progress_bar(current, total)
    
    # Погода
    weather = await get_weather(point['coordinates'])
    
    # Рейтинг
    rating_display = get_star_rating(avg_rating)
    user_rating_text = f"\n👤 Ваша оценка: {user_rating}/5" if user_rating else ""
    
    text = (
        f"{progress_bar}\n\n"
        f"📍 *Точка {current} из {total}*\n\n"
        f"{point['name']}\n"
        f"📍 *Адрес:* {point['address']}\n\n"
        f"📝 *Описание:*\n{point['description']}\n\n"
        f"{point['time']}\n"
        f"{point['tips']}\n\n"
        f"{point['photo_tips']}\n\n"
        f"{weather}\n\n"
        f"⭐ *Рейтинг:* {rating_display} ({votes_count} оценок){user_rating_text}\n"
    )
    
    # Кнопки для оценки
    rating_buttons = []
    for i in range(1, 6):
        emoji = "⭐" if i <= (user_rating or 0) else "☆"
        rating_buttons.append(InlineKeyboardButton(f"{emoji} {i}", callback_data=f"rate_{current}_{i}"))
    
    # Основные кнопки
    keyboard = []
    
    if point['next']:
        keyboard.append([InlineKeyboardButton("🚶‍♂️ Идём дальше", callback_data="next_point")])
    else:
        keyboard.append([InlineKeyboardButton("🏁 Завершить маршрут", callback_data="finish_route")])
    
    keyboard.append([InlineKeyboardButton("🗺️ Показать на карте", callback_data="show_map")])
    keyboard.append([InlineKeyboardButton("📤 Поделиться", callback_data=f"share_{current}")])
    keyboard.append(rating_buttons)  # Кнопки оценки
    keyboard.append([InlineKeyboardButton("❌ Завершить", callback_data="finish_route")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем фото
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
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    if is_first:
        try:
            await query.message.delete()
        except:
            pass

async def show_finish(query, context: ContextTypes.DEFAULT_TYPE):
    finish_text = (
        "🎉 *Поздравляю! Вы прошли весь маршрут!* 🎉\n\n"
        "Спасибо за путешествие! 💙\n\n"
        "Не забудьте оценить локации, которые вам понравились!\n"
        "⭐ Топ локаций можно посмотреть в меню /start\n\n"
        "Чтобы начать заново, нажмите /start"
    )
    
    keyboard = [[InlineKeyboardButton("🔄 Начать заново", callback_data="start_route")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(finish_text, reply_markup=reply_markup, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ Ошибка: {context.error}", exc_info=True)

async def run_bot():
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ Токен не найден!")
        return
    
    # Инициализируем базу данных
    init_db()
    
    logger.info("✅ Бот запускается...")
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_handler))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)
    
    logger.info("✅ Запускаю polling...")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("✅ Бот работает!")
    
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
