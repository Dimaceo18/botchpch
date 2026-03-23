#!/bin/bash
echo "========================================="
echo "🚀 Запуск Telegram бота"
echo "========================================="

echo "🐍 Python version:"
python --version

echo "📦 Устанавливаю зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

python -c "import telegram; print(f'✅ python-telegram-bot {telegram.__version__}')"

echo "========================================="
echo "🤖 Запускаем бота..."
echo "========================================="

exec python bot.py
