from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.agent.state import AgentState
from app.agent.graph import agent_graph

scheduler = AsyncIOScheduler(timezone="Asia/Singapore")


def _get_initial_state() -> AgentState:
    return {
        "emails": [],
        "important_emails": [],
        "briefing_text": "",
        "whatsapp_reply": None,
        "actions_taken": [],
        "run_id": ""
    }


async def run_agent():
    """Entry point for the scheduled daily run."""
    print("[scheduler] Running email intelligence agent...")
    try:
        state = _get_initial_state()
        agent_graph.invoke(state)
        print("[scheduler] Agent run complete — awaiting WhatsApp reply")
    except Exception as e:
        print(f"[scheduler] ERROR: {e}")


def start_scheduler():
    """Start APScheduler — runs agent daily at 8:00 AM Singapore time."""
    scheduler.add_job(
        run_agent,
        trigger="cron",
        hour=8,
        minute=0,
        id="daily_email_briefing",
        replace_existing=True
    )
    scheduler.start()
    print("[scheduler] Scheduler started — daily run at 08:00 SGT")
