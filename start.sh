#!/bin/bash

echo "========================================="
echo "🚀 Запуск Telegram бота"
echo "========================================="

# Используем установленный Python
export PATH=/opt/python311/bin:$PATH
export PYTHONPATH=/opt/python311/lib/python3.11/site-packages

# Выводим версию
echo "🐍 Python version:"
/opt/python311/bin/python --version

# Проверяем наличие telegram
echo "📦 Проверка библиотек:"
/opt/python311/bin/python -c "import telegram; print(f'✅ python-telegram-bot {telegram.__version__}')" || {
    echo "❌ Библиотеки не установлены, запускаю установку..."
    /opt/python311/bin/python -m pip install -r requirements.txt
}

echo "========================================="
echo "🤖 Запускаем бота..."
echo "========================================="

# Запускаем бота
exec /opt/python311/bin/python bot.py
