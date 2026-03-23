#!/bin/bash

echo "========================================="
echo "🚀 Запуск Telegram бота"
echo "========================================="

# Используем установленный Python 3.11
export PATH=/opt/python311/bin:$PATH
export PYTHONPATH=/opt/python311/lib/python3.11/site-packages

# Выводим версию
echo "🐍 Python version:"
python --version

# Запускаем бота
exec python bot.py
