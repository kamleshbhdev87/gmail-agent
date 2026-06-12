import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.agent.graph import agent_graph
from app.agent.state import AgentState
from app.scheduler import start_scheduler
from app.tools.whatsapp_tool import parse_whatsapp_reply

pending_sessions: dict[str, AgentState] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(
    title="Gmail Agent",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/run-now")
async def run_now():
    state: AgentState = {
        "emails": [],
        "important_emails": [],
        "briefing_text": "",
        "whatsapp_reply": None,
        "actions_taken": [],
        "run_id": ""
    }
    result = agent_graph.invoke(state)
    pending_sessions["current"] = result
    return JSONResponse({
        "status": "briefing_sent",
        "emails_found": len(result.get("important_emails", [])),
        "run_id": result.get("run_id", "")
    })

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    reply_text = parse_whatsapp_reply(dict(form_data))
    if not reply_text:
        return JSONResponse({"status": "empty_reply"})
    state = pending_sessions.get("current")
    if not state:
        return JSONResponse({"status": "no_active_session"}, status_code=404)
    state["whatsapp_reply"] = reply_text
    result = agent_graph.invoke(state, config={"recursion_limit": 10})
    pending_sessions.pop("current", None)
    return JSONResponse({
        "status": "processed",
        "actions_taken": result.get("actions_taken", [])
    })

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "gmail-agent"}

@app.get("/followups")
async def get_followups():
    from app.memory.chroma_store import get_pending_followups
    return {"pending": get_pending_followups()}


@app.get("/")
async def root():
    return {
        "name": "Gmail Agent",
        "description": "Autonomous Gmail agent — scores emails, drafts replies, sends WhatsApp briefing with human-in-the-loop approval",
        "status": "running",
        "stack": ["LangGraph", "Claude API", "FastAPI", "Gmail API", "Twilio WhatsApp", "ChromaDB", "Render"],
        "endpoints": {
            "POST /run-now": "Trigger agent manually",
            "POST /webhook/whatsapp": "Twilio WhatsApp webhook",
            "GET /health": "Health check",
            "GET /followups": "View pending follow-ups"
        },
        "github": "https://github.com/kamleshbhdev87/gmail-agent"
    }


@app.get("/")
async def root():
    return {
        "name": "Gmail Agent",
        "description": "Autonomous Gmail agent — scores emails, drafts replies, sends WhatsApp briefing with human-in-the-loop approval",
        "status": "running",
        "stack": ["LangGraph", "Claude API", "FastAPI", "Gmail API", "Twilio WhatsApp", "ChromaDB", "Render"],
        "endpoints": {
            "POST /run-now": "Trigger agent manually",
            "POST /webhook/whatsapp": "Twilio WhatsApp webhook",
            "GET /health": "Health check",
            "GET /followups": "View pending follow-ups"
        },
        "github": "https://github.com/kamleshbhdev87/gmail-agent"
    }
