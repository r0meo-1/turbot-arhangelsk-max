# Turbot — Tour Selection Bot for MAX Messenger

A conversational bot for Russia's **МАКС (MAX)** messenger that helps travelers
pick a tour through a guided, step-by-step form and automatically forwards each
completed request as a lead into the **МоиДокументы-Туризм (MoiDokumenti-Tourism)**
CRM.

The bot walks a user through a short FSM-driven dialog — destination, dates,
party size, budget, phone — validates every answer, confirms the request, and
pushes a structured lead to the travel agency's CRM via its REST API. A small
Flask server runs alongside the bot to expose health-check endpoints, so the
service can be hosted on platforms like Render as a Web Service.

> 🇷🇺 Бот для мессенджера МАКС: пошаговый подбор тура и автоматическая отправка
> заявок в CRM «МоиДокументы-Туризм». Документация ниже — на английском.

## Features

- **Guided tour-request form** — finite-state-machine dialog collecting
  destination, dates, number of travelers, budget, and contact phone.
- **Input validation** — each field is validated before the conversation
  advances (phone format, party size 1–50, positive budget, dates, destination).
- **CRM lead delivery** — completed requests are sent to MoiDokumenti-Tourism
  via the `api/add-lead` endpoint, including a formatted comment and structured
  fields.
- **Graceful degradation** — if CRM credentials are not configured, the bot
  still works end-to-end and simply skips lead delivery (logged as a warning).
- **Health-check endpoints** — Flask `/` and `/health` routes for uptime
  monitoring and Web Service hosting.
- **Stateless-friendly deployment** — single process, long-polling the MAX API
  with the Flask server on a background thread.

## Tech Stack

- **Python** (asyncio)
- **[maxapi](https://pypi.org/project/maxapi/)** — MAX messenger Bot API client,
  Dispatcher, and FSM context
- **Flask** — health-check HTTP endpoints
- **requests** — CRM REST integration
- Designed for deployment on **Render** (Web Service)

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` and fill in your values:

```bash
cp .env.example .env
```

| Variable      | Required | Description                                                              |
|---------------|----------|--------------------------------------------------------------------------|
| `BOT_TOKEN`   | Yes      | MAX messenger bot token. The bot refuses to start without it.            |
| `ADMIN_ID`    | No       | Administrator chat ID (defaults to `0`).                                 |
| `MDT_DOMAIN`  | No\*     | MoiDokumenti-Tourism account domain, e.g. `your-account.moidokumenti.ru`.|
| `MDT_API_KEY` | No\*     | MoiDokumenti-Tourism API key.                                            |
| `PORT`        | No       | Port for the Flask health server (defaults to `5000`).                   |

\* `MDT_DOMAIN` and `MDT_API_KEY` are optional: without them the bot runs
normally but skips sending leads to the CRM.

### 3. Run

```bash
python bot.py
```

The bot starts long-polling the MAX API, and the Flask health server starts on
`PORT` in a background thread.

## How It Works

1. **Start** — the user sends `/start`; the bot initializes the `TourForm` FSM
   and asks for a destination.
2. **Collect & validate** — the bot advances through states
   (`destination → dates → people → budget → phone`), validating each input and
   re-prompting on invalid answers.
3. **Confirm** — once the phone number is valid, the bot summarizes the request
   back to the user and clears the conversation state.
4. **Deliver lead** — the request is sent to MoiDokumenti-Tourism via
   `POST https://<MDT_DOMAIN>/api/add-lead` with the lead name, phone, source
   (`MAX bot`), and structured fields (destination, dates, people, budget,
   comment).
5. **Fallback** — any message outside the form prompts the user to press
   `/start`.

A Flask server runs concurrently:

- `GET /` → `MAX bot running`
- `GET /health` → `{"status": "ok", "chats": <active chat count>}`

## Deploy on Render

1. Create a **Web Service** (not a Background Worker).
2. Connect this GitHub repository.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. Add environment variables: `BOT_TOKEN`, and optionally `MDT_DOMAIN` /
   `MDT_API_KEY`.

Render injects `PORT` automatically; Flask binds to it for health checks.

## Project Structure

```
turbot-arhangelsk-max/
├── bot.py            # Bot logic, FSM, CRM integration, Flask health server
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment variables
├── LICENSE           # MIT license
└── README.md         # This file
```

## License

[MIT](LICENSE) © 2026 r0meo-1
