#!/bin/bash
# Запуск TesterFaSOAP.py в правильном виртуальном окружении

VENV="$HOME/python/.venv3.14"
SCRIPT="$HOME/python/TesterFaSOAP.py/TesterFaSOAP.py"

# Проверки
if [ ! -f "$VENV/bin/activate" ]; then
    echo "❌ Не найдено venv: $VENV" >&2
    exit 1
fi

if [ ! -f "$SCRIPT" ]; then
    echo "❌ Не найден скрипт: $SCRIPT" >&2
    exit 1
fi

# Активируем venv и запускаем
source "$VENV/bin/activate"
exec python "$SCRIPT" "$@"