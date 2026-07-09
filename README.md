# TurBot MAX — тот же турбот, другой мессенджер

![Python](https://img.shields.io/badge/Python-asyncio-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)

> Telegram-версию вы уже видели (или вот-вот увидите).  
> **MAX** — российский мессенджер. Клиенты там. Лиды должны быть там же.  
> Этот репозиторий — порт сценария «подбор тура → CRM», без «давайте перепишем всё с нуля, потому что скучно».

Бот для **МАКС**: пошаговый FSM (направление, даты, люди, бюджет, телефон),  
валидация, подтверждение, отправка lead в **МоиДокументы-Туризм (MDT)**.  
Flask рядом — `/` и `/health`, чтобы хостинг не думал, что процесс умер от одиночества.

---

## Зачем это существует

| Telegram (`turbot-arhangelsk`) | MAX (этот репо) |
|--------------------------------|-----------------|
| Webhook Bot API | long-polling + maxapi |
| Отдельный `shared/` с VK | Свой стек, та же **идея** lead-gen |
| Админка в Telegram | Фокус на клиентском диалоге + CRM |

Один бизнес-процесс — две (три) платформы. Не потому что «масштабируемся в мультивселенную»,  
а потому что клиенты разбежались по мессенджерам, а менеджеру нужен **один** lead в CRM.

---

## Фичи

- **FSM-диалог** — как анкета, только с эмодзи и без бумажки  
- **Валидация** — телефон, люди, бюджет, даты (человеческий ввод = энтропия)  
- **CRM** — `add-lead` в MDT; нет ключей — бот живёт, CRM просто «не сегодня» (warning в лог)  
- **Health** — Flask `/` и `/health`  
- **Деплой** — один процесс: polling MAX + HTTP в фоне  

---

## Стек

- Python · **asyncio**
- [maxapi](https://pypi.org/project/maxapi/) — Bot API, Dispatcher, FSM  
- Flask — health  
- requests — CRM  
- Render / VPS — как повезёт с free-tier  

---

## Быстрый старт

```bash
git clone https://github.com/r0meo-1/turbot-arhangelsk-max.git
cd turbot-arhangelsk-max
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # если есть; иначе — переменные окружения
```

Обычно нужны токен MAX-бота и (опционально) `MDT_*`.  
Без CRM бот всё равно пройдёт диалог — просто lead останется «в чате вселенной».

```bash
python bot.py   # или как указано в Procfile / README хостинга
```

---

## Связанный репозиторий

- [**turbot-arhangelsk**](https://github.com/r0meo-1/turbot-arhangelsk) — Telegram + VK, shared, 152-ФЗ, admin, Docker kit  

Смотрите оба, если хотите сравнить «одна идея — два адаптера».  
В pin профиля достаточно **одного** тур-бота. HR не обязан коллекционировать мессенджеры.

---

## Контакты

**[r0meo1.ru](https://r0meo1.ru)** · [@r0meo1](https://t.me/r0meo1) · r0meo1@ya.ru

## Лицензия

[MIT](LICENSE) — форкайте, деплойте, только не храните ПДн «где получилось».
