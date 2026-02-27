# turbot-arhangelsk-max

Бот для мессенджера **МАКС** (MAX) — подбор туров с отправкой заявок в CRM **МоиДокументы-Туризм**.

## Возможности
- Форма подбора тура (направление, даты, люди, бюджет, телефон)
- Валидация всех полей (телефон, бюджет, количество людей)
- Отправка лида в МоиДокументы-Туризм через API
- Health-check endpoint для Render Web Service

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен бота в МАКС (обязательно) |
| `ADMIN_ID` | Chat ID администратора (опционально) |
| `MDT_DOMAIN` | Домен кабинета МоиДокументы-Туризм (например: `apreltour.moidokumenti.ru`) |
| `MDT_API_KEY` | API-ключ МоиДокументы-Туризм |
| `PORT` | Порт для Flask (по умолчанию 5000, Render установит автоматически) |

## API МоиДокументы-Туризм

Используется метод `api/add-lead` (POST):
- URL: `https://<MDT_DOMAIN>/api/add-lead`
- Body: `params` (JSON) и `key` (API ключ)

## Локальный запуск

```bash
pip install -r requirements.txt
export BOT_TOKEN=your_token
export MDT_DOMAIN=apreltour.moidokumenti.ru
export MDT_API_KEY=your_key
python bot.py
```

## Деплой на Render

1. Создайте **Web Service** (не Background Worker)
2. Подключите этот GitHub-репозиторий
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. Добавьте Environment Variables:
   - `BOT_TOKEN`
   - `MDT_DOMAIN`
   - `MDT_API_KEY`

Render автоматически установит `PORT`, Flask будет слушать его для health-check.

## Валидации

- **Телефон**: +7/8/7 + 10 цифр (например: +79123456789, 89123456789)
- **Люди**: от 1 до 50 человек
- **Бюджет**: число больше 0
- **Даты**: минимум 5 символов
- **Направление**: минимум 2 символа

## Структура проекта

```
turbot-arhangelsk-max/
├── bot.py              # Основной код бота
├── requirements.txt    # Зависимости
├── .env.example        # Пример переменных окружения
└── README.md          # Документация
```

## Health-check endpoints

- `GET /` — возвращает "MAX bot running"
- `GET /health` — возвращает JSON с количеством активных чатов

Render использует эти endpoints для проверки работоспособности сервиса.
