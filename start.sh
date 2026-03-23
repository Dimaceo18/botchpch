#!/bin/bash
echo "========================================="
echo "🚀 Запуск Telegram бота"
echo "========================================="

# Выводим версию Python
echo "🐍 Python version:"
python --version

# Устанавливаем зависимости
echo "📦 Устанавливаю зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# Проверяем установку
python -c "import telegram; print(f'✅ python-telegram-bot {telegram.__version__}')"

echo "========================================="
echo "🤖 Запускаем бота..."
echo "========================================="

# Запускаем бота
exec python bot.py
