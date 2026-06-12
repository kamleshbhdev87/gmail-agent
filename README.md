# 📧 Email Intelligence Agent

A single autonomous agent that monitors your Gmail, scores emails by priority,
drafts replies, and sends you an actionable WhatsApp briefing every morning.
You approve what gets sent — nothing goes out without your say-so.

**Stack:** LangGraph · Claude API · FastAPI · Gmail API · Twilio WhatsApp · ChromaDB · Render

---

## How It Works

```
Gmail (fetch) → Score emails (Claude) → Draft replies (Claude)
     → WhatsApp briefing → You reply 'send 1' → Email sent → Memory updated
```

---

## Setup

### 1. Clone and install
```bash
git clone https://github.com/yourname/email-intelligence-agent
cd email-intelligence-agent
pip install -r requirements.txt
cp .env.example .env
```

### 2. Gmail OAuth (one-time setup)
```bash
# Fill in GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env first, then:
python scripts/get_gmail_token.py
# Copy the printed GMAIL_REFRESH_TOKEN into your .env
```

### 3. Twilio WhatsApp
- Sign up at twilio.com
- Go to Messaging → Try it out → Send a WhatsApp message
- Join the sandbox by sending the join code to +14155238886
- Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, YOUR_WHATSAPP_NUMBER to .env

### 4. Run locally
```bash
uvicorn app.main:app --reload
```

### 5. Trigger manually (test)
```bash
curl -X POST http://localhost:8000/run-now
```

### 6. Test WhatsApp reply (simulate webhook)
```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -d "Body=send 1"
```

---

## Deploy to Render

1. Push to GitHub
2. Connect repo in Render → New Web Service
3. Add all environment variables from `.env.example` in Render's Environment tab
4. Set Twilio webhook URL to: `https://your-app.onrender.com/webhook/whatsapp`
5. Deploy — auto-deploys on every push

---

## WhatsApp Commands

| Command | Action |
|---------|--------|
| `send 1` | Send drafted reply for email #1 |
| `skip 2` | Skip email #2, no action |
| `edit 1 Sure, will check tomorrow` | Send your own text for email #1 |
| `send 1\nskip 2` | Multiple commands in one message |

---

## Project Structure

```
email-intelligence-agent/
├── app/
│   ├── main.py                  # FastAPI app + Twilio webhook
│   ├── scheduler.py             # APScheduler — runs daily at 8am SGT
│   ├── agent/
│   │   ├── graph.py             # LangGraph state graph
│   │   ├── nodes.py             # All 8 agent node functions
│   │   ├── state.py             # AgentState TypedDict
│   │   └── prompts.py           # LLM prompt templates
│   ├── tools/
│   │   ├── gmail_tool.py        # Gmail read + send
│   │   └── whatsapp_tool.py     # Twilio send + parse
│   └── memory/
│       └── chroma_store.py      # ChromaDB thread persistence
├── tests/
│   └── test_nodes.py
├── scripts/
│   └── get_gmail_token.py       # One-time Gmail OAuth setup
├── .env.example
├── requirements.txt
├── render.yaml
└── README.md
```

---

## Run Tests

```bash
pytest tests/ -v
```

---

## Resume Talking Points

- **LangGraph state graph** — each reasoning step is a discrete node with typed state
- **Human-in-the-loop** — WhatsApp approval before any email is sent
- **Persistent memory** — ChromaDB tracks thread status across days
- **Async FastAPI** — handles Twilio webhooks reliably
- **Production-grade** — deployed on Render with persistent disk, scheduled cron
