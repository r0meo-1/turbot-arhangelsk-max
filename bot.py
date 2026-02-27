import asyncio
import json
import logging
import os
import re
import threading

import requests
from flask import Flask

from maxapi import Bot, Dispatcher, F
from maxapi.context import MemoryContext, State, StatesGroup
from maxapi.types import MessageCreated, BotStarted, Command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# МоиДокументы-Туризм
MDT_API_KEY = os.getenv("MDT_API_KEY", "")
MDT_DOMAIN = os.getenv("MDT_DOMAIN", "")  # например: apreltour.moidokumenti.ru

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN обязателен")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


class TourForm(StatesGroup):
    destination = State()
    dates = State()
    people = State()
    budget = State()
    phone = State()


all_chats: set[int] = set()


def get_chat_id(event: MessageCreated) -> int:
    """Извлечь chat_id из события."""
    if getattr(event, "chat", None) and getattr(event.chat, "chat_id", None):
        return int(event.chat.chat_id)
    return int(getattr(event, "chat_id", 0) or 0)


def mdt_post(method: str, params: dict, timeout: int = 20) -> requests.Response:
    """POST в API МоиДокументы-Туризм.

    POST на https://DOMAIN/api/METHOD
    Body: params (JSON) и key (API key)
    """
    if not MDT_DOMAIN or not MDT_API_KEY:
        raise RuntimeError("MDT_DOMAIN/MDT_API_KEY не установлены")

    url = f"https://{MDT_DOMAIN}/api/{method}"
    data = {
        "params": json.dumps(params, ensure_ascii=False),
        "key": MDT_API_KEY,
    }
    return requests.post(url, data=data, timeout=timeout)


def send_to_mdt_lead(destination: str, dates: str, people: str, budget: str, phone: str, chat_id: int | None = None):
    """Создать лид в МоиДокументы-Туризм через api/add-lead."""
    if not MDT_DOMAIN or not MDT_API_KEY:
        logger.warning("MDT интеграция отключена: нет MDT_DOMAIN/MDT_API_KEY")
        return False

    note = (
        f"Направление: {destination}\n"
        f"Даты: {dates}\n"
        f"Людей: {people}\n"
        f"Бюджет: {budget}\n"
        + (f"ChatId: {chat_id}\n" if chat_id else "")
    )

    params = {
        "name": f"Заявка из MAX: {destination}",
        "phone": phone,
        "email": "",
        "source": "MAX bot",
        "fields": [
            {"name": "Комментарий", "values": [note]},
            {"name": "Направление", "values": [destination]},
            {"name": "Даты", "values": [dates]},
            {"name": "Людей", "values": [people]},
            {"name": "Бюджет", "values": [budget]},
        ],
    }

    try:
        resp = mdt_post("add-lead", params)
        ok = resp.status_code == 200
        if ok:
            logger.info("MDT лид создан: %s", resp.text[:200])
        else:
            logger.error("MDT лид ошибка: %s %s", resp.status_code, resp.text[:400])
        return ok
    except Exception as e:
        logger.error("MDT ошибка: %s", e)
        return False


def validate_phone(phone: str) -> bool:
    """Проверка формата телефона: +7, 8, или 7 + 10 цифр."""
    cleaned = re.sub(r"[\s\-\(\)]+", "", phone)
    # Допустимые форматы: +79123456789, 89123456789, 79123456789
    if re.match(r"^(\+7|8|7)\d{10}$", cleaned):
        return True
    return False


def validate_people(people: str) -> bool:
    """Проверка количества людей: число от 1 до 50."""
    try:
        num = int(people.strip())
        return 1 <= num <= 50
    except ValueError:
        return False


def validate_budget(budget: str) -> bool:
    """Проверка бюджета: число больше 0."""
    try:
        cleaned = budget.strip().replace(" ", "").replace(",", "")
        num = float(cleaned)
        return num > 0
    except ValueError:
        return False


def validate_dates(dates: str) -> bool:
    """Простая проверка дат: не пустая строка, минимум 5 символов."""
    return len(dates.strip()) >= 5


@dp.bot_started()
async def on_bot_started(event: BotStarted):
    all_chats.add(int(event.chat_id))
    await event.bot.send_message(chat_id=event.chat_id, text="🌴 Добро пожаловать! Нажмите /start для подбора тура.")


@dp.message_created(Command("start"))
async def cmd_start(event: MessageCreated, context: MemoryContext):
    chat_id = get_chat_id(event)
    all_chats.add(chat_id)
    await context.set_state(TourForm.destination)
    await event.message.answer(
        "🌴 Здравствуйте! Я помогу подобрать тур.\n\n"
        "📍 Куда бы вы хотели отправиться? (Например: Турция, Египет, Таиланд)"
    )


@dp.message_created(F.message.body.text, TourForm.destination)
async def fsm_destination(event: MessageCreated, context: MemoryContext):
    destination = event.message.body.text.strip()
    if len(destination) < 2:
        await event.message.answer("❌ Пожалуйста, укажите направление (минимум 2 символа).")
        return

    await context.update_data(destination=destination)
    await context.set_state(TourForm.dates)
    await event.message.answer(
        "📅 На какие даты планируете поездку?\n"
        "(Например: 15-22 июня, с 1 по 10 августа)"
    )


@dp.message_created(F.message.body.text, TourForm.dates)
async def fsm_dates(event: MessageCreated, context: MemoryContext):
    dates = event.message.body.text.strip()
    if not validate_dates(dates):
        await event.message.answer("❌ Укажите даты поездки (минимум 5 символов).")
        return

    await context.update_data(dates=dates)
    await context.set_state(TourForm.people)
    await event.message.answer("👥 Сколько человек будет путешествовать? (от 1 до 50)")


@dp.message_created(F.message.body.text, TourForm.people)
async def fsm_people(event: MessageCreated, context: MemoryContext):
    people = event.message.body.text.strip()
    if not validate_people(people):
        await event.message.answer("❌ Укажите корректное количество человек (от 1 до 50).")
        return

    await context.update_data(people=people)
    await context.set_state(TourForm.budget)
    await event.message.answer("💰 Какой бюджет рассматриваете на человека? (в рублях, например: 50000)")


@dp.message_created(F.message.body.text, TourForm.budget)
async def fsm_budget(event: MessageCreated, context: MemoryContext):
    budget = event.message.body.text.strip()
    if not validate_budget(budget):
        await event.message.answer("❌ Укажите корректный бюджет (число больше 0).")
        return

    await context.update_data(budget=budget)
    await context.set_state(TourForm.phone)
    await event.message.answer(
        "📱 Укажите ваш номер телефона для связи:\n"
        "(Например: +79123456789, 89123456789)"
    )


@dp.message_created(F.message.body.text, TourForm.phone)
async def fsm_phone(event: MessageCreated, context: MemoryContext):
    chat_id = get_chat_id(event)
    all_chats.add(chat_id)

    phone = event.message.body.text.strip()
    if not validate_phone(phone):
        await event.message.answer(
            "❌ Неверный формат телефона. Укажите номер в формате:\n"
            "+79123456789 или 89123456789"
        )
        return

    data = await context.get_data()
    await context.clear()

    destination = data.get("destination", "—")
    dates = data.get("dates", "—")
    people = data.get("people", "—")
    budget = data.get("budget", "—")

    await event.message.answer(
        "✅ Ваша заявка принята! Менеджер свяжется с вами в ближайшее время.\n\n"
        f"📍 Направление: {destination}\n"
        f"📅 Даты: {dates}\n"
        f"👥 Человек: {people}\n"
        f"💰 Бюджет: {budget} руб.\n"
        f"📱 Телефон: {phone}\n\n"
        "Для нового запроса нажмите /start"
    )

    # Отправка лида в МоиДокументы-Туризм
    send_to_mdt_lead(destination, dates, people, budget, phone, chat_id=chat_id)


@dp.message_created(F.message.body.text)
async def fallback(event: MessageCreated):
    all_chats.add(get_chat_id(event))
    await event.message.answer("🌴 Нажмите /start, чтобы подобрать тур!")


# --- Flask health-check для Render Web Service ---
app = Flask(__name__)


@app.route("/")
def health_check():
    return "MAX bot running"


@app.route("/health")
def health():
    return {"status": "ok", "chats": len(all_chats)}


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
