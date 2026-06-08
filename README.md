# Morning Brief Bot

A Telegram bot that delivers a personalized daily brief every morning and lets you create reminders via plain-English messages.

```
┌─────────────────────────────────────────────────────────┐
│                     Architecture                        │
│                                                         │
│  GitHub Actions (cron)                                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │  brief.py                                       │    │
│  │   ├── weather.py    → Open-Meteo (no key)       │    │
│  │   ├── news.py       → GNews API                 │    │
│  │   ├── google_sources.py → Calendar + Gmail      │    │
│  │   ├── reminders.py  → Supabase Postgres         │    │
│  │   └── compose.py    → Claude claude-opus-4-8    │    │
│  │                ↓                                │    │
│  │           telegram.py → Telegram Bot API        │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Always-on host (Railway/Render/Fly)                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │  bot.py (Flask)                                 │    │
│  │   ├── POST /webhook  → parse + store reminder   │    │
│  │   └── GET  /         → health check             │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Setup

### 1. Telegram — create a bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot`
2. Copy the token → `TELEGRAM_BOT_TOKEN`
3. Send `/start` to your new bot, then fetch your chat ID:
   ```
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```
   The `chat.id` field → `TELEGRAM_CHAT_ID`

### 2. Supabase — create a database

1. Sign up at [supabase.com](https://supabase.com) and create a project.
2. In the SQL editor, run `schema.sql` to create the `reminders` table.
3. Project URL → `SUPABASE_URL`
4. Settings → API → `service_role` secret key → `SUPABASE_SERVICE_KEY`

### 3. Google OAuth — Calendar + Gmail

1. Go to [Google Cloud Console](https://console.cloud.google.com/), create a project.
2. Enable **Google Calendar API** and **Gmail API**.
3. Configure OAuth consent screen (External; add your Gmail as a test user).
4. Create credentials: **OAuth 2.0 Client ID** → Desktop app. Download as `client_secret.json` in the project root.
5. Run the helper once locally:
   ```
   python src/get_google_token.py
   ```
   Copy the printed values into your env:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`

### 4. GNews (optional)

Sign up at [gnews.io](https://gnews.io) for a free API key → `NEWS_API_KEY`.
If omitted, the news section says "(no news API key configured)".

### 5. Anthropic

Get an API key at [console.anthropic.com](https://console.anthropic.com) → `ANTHROPIC_API_KEY`.

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | yes | — | BotFather token |
| `TELEGRAM_CHAT_ID` | yes | — | Numeric chat ID of the owner |
| `ANTHROPIC_API_KEY` | yes | — | Claude API key |
| `SUPABASE_URL` | yes | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | yes | — | Supabase service_role key |
| `GOOGLE_CLIENT_ID` | yes | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | yes | — | Google OAuth client secret |
| `GOOGLE_REFRESH_TOKEN` | yes | — | Long-lived refresh token |
| `NEWS_API_KEY` | no | — | GNews key (brief degrades gracefully if absent) |
| `TIMEZONE` | no | `America/New_York` | IANA timezone string |
| `LATITUDE` | no | `40.6782` | Weather coordinates (Brooklyn, NY) |
| `LONGITUDE` | no | `-73.9442` | Weather coordinates |
| `NEWS_COUNTRY` | no | `us` | Two-letter GNews country code |
| `PORT` | no | `8080` | Injected by Railway/Render/Fly |

Copy `.env.example` to `.env` and fill in real values.

---

## Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# Export env vars
export $(cat .env | xargs)

# Send a brief immediately
python src/brief.py

# Run the webhook bot
flask --app src/bot run --port 8080
# or
gunicorn --chdir src bot:app --bind 0.0.0.0:8080
```

---

## GitHub Actions deployment (brief)

1. In your GitHub repo → **Settings → Secrets and variables → Actions**
2. Add all required env vars as **Repository secrets**:
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY`,
   `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GOOGLE_CLIENT_ID`,
   `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `NEWS_API_KEY`
3. Optionally add `TIMEZONE`, `LATITUDE`, `LONGITUDE`, `NEWS_COUNTRY` as
   **Repository variables** (not secrets).
4. The workflow fires at 11:00 UTC (7 AM EDT) and 12:00 UTC (7 AM EST)
   to bracket daylight saving time. Adjust the cron in
   `.github/workflows/morning-brief.yml` if you want a different time.
5. Test it immediately: **Actions → Morning Brief → Run workflow**.

---

## Bot deployment (webhook)

Deploy `bot.py` to any always-on host (Railway, Render, Fly.io).

### Railway (recommended)
1. Connect your GitHub repo.
2. Set all env vars in Railway's variable editor.
3. Railway auto-detects the `Procfile` and runs gunicorn.

### Register the webhook
Once deployed, run once:
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-host>/webhook"
```

### Bot commands
- `/start` — greet and display your chat ID
- `/list` — show today's due reminders
- Any plain-English text — parsed as a reminder, e.g.:
  - `remind me to take vitamins every day`
  - `call dentist on Friday`
  - `monthly team retro on the 15th`

---

## Running tests

```bash
# Set dummy values so config.py doesn't complain at import
export TELEGRAM_BOT_TOKEN=x TELEGRAM_CHAT_ID=0 ANTHROPIC_API_KEY=x \
       SUPABASE_URL=https://x.supabase.co SUPABASE_SERVICE_KEY=x \
       GOOGLE_CLIENT_ID=x GOOGLE_CLIENT_SECRET=x GOOGLE_REFRESH_TOKEN=x

pytest tests/ -v
```

Tests mock all network calls — no real credentials needed for CI.

---

## Cost estimate

| Component | Cost |
|-----------|------|
| Claude claude-opus-4-8 brief (1200 tokens out) | ~$0.06/day |
| Claude parse per reminder (300 tokens out) | ~$0.001 each |
| GNews free tier | 100 req/day — well within budget |
| Open-Meteo | Free |
| Supabase free tier | 500 MB database, plenty for reminders |
| GitHub Actions | Free for public repos / 2000 min/mo free for private |
| Railway/Render | ~$5/mo for always-on bot host |

Total: **≈ $3–7/month** depending on reminder volume and bot host choice.

---

## Manual verification checklist

- [ ] `python src/brief.py` delivers a message to Telegram
- [ ] Texting the deployed bot `remind me to do X tomorrow` stores a reminder
- [ ] The next morning's brief includes that reminder
- [ ] `/list` in the bot shows today's due reminders
- [ ] `workflow_dispatch` on `morning-brief.yml` succeeds end-to-end
