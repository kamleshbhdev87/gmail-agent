import json
import uuid
import anthropic
from app.agent.state import AgentState, EmailItem
from app.agent.prompts import SCORE_EMAIL_PROMPT, DRAFT_REPLY_PROMPT
from app.tools.gmail_tool import fetch_recent_emails, send_email
from app.tools.whatsapp_tool import send_whatsapp_message, send_whatsapp_messages
from app.memory.chroma_store import save_thread

client = anthropic.Anthropic()


# ── NODE 1: Fetch Emails ──────────────────────────────────────────────────────
def fetch_emails(state: AgentState) -> AgentState:
    raw_emails = fetch_recent_emails(max_results=50)
    state["emails"] = raw_emails
    state["run_id"] = str(uuid.uuid4())[:8]
    print(f"[fetch_emails] Fetched {len(raw_emails)} emails")
    return state


# ── NODE 2: Score Emails ──────────────────────────────────────────────────────
def score_emails(state: AgentState) -> AgentState:
    scored = []
    for email in state["emails"]:
        prompt = SCORE_EMAIL_PROMPT.format(
            sender=email["sender"],
            subject=email["subject"],
            body=email["body"][:600]
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        try:
            result = json.loads(response.content[0].text)
            scored.append({
                **email,
                "priority_score": result.get("score", 1),
                "priority_reason": result.get("reason", ""),
                "needs_reply": result.get("needs_reply", False),
                "draft_reply": None
            })
        except json.JSONDecodeError:
            scored.append({
                **email,
                "priority_score": 1,
                "priority_reason": "parse error",
                "needs_reply": False,
                "draft_reply": None
            })

    state["emails"] = sorted(scored, key=lambda x: x["priority_score"], reverse=True)
    print(f"[score_emails] Scored {len(scored)} emails")
    return state


# ── NODE 3: Filter Important ──────────────────────────────────────────────────
def filter_important(state: AgentState) -> AgentState:
    important = [e for e in state["emails"] if e["priority_score"] >= 4]
    state["important_emails"] = important
    print(f"[filter_important] {len(important)} important emails (score >= 4)")
    return state


# ── NODE 4: Draft Replies ─────────────────────────────────────────────────────
def draft_replies(state: AgentState) -> AgentState:
    updated = []
    for email in state["important_emails"]:
        prompt = DRAFT_REPLY_PROMPT.format(
            sender=email["sender"],
            subject=email["subject"],
            body=email["body"][:800]
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        email["draft_reply"] = response.content[0].text.strip()
        updated.append(email)

    state["important_emails"] = updated
    print(f"[draft_replies] Drafted replies for {len(updated)} emails")
    return state


# ── NODE 5: Build Briefing ────────────────────────────────────────────────────
def build_briefing(state: AgentState) -> AgentState:
    """Build one WhatsApp message per email — stored as list in briefing_text."""
    if not state["important_emails"]:
        state["briefing_text"] = json.dumps([
            "✅ *Gmail Briefing* — Inbox is clear! No urgent emails right now."
        ])
        return state

    total = len(state["important_emails"])
    messages = []

    # Header message
    messages.append(f"📬 *Gmail Briefing — {total} email(s) need your attention*")

    for i, email in enumerate(state["important_emails"], 1):
        score = email["priority_score"]
        if score >= 9:
            priority_emoji = "🔴 URGENT"
        elif score >= 7:
            priority_emoji = "🟡 IMPORTANT"
        else:
            priority_emoji = "🟢 FYI"

        # Extract sender name cleanly
        sender_raw = email["sender"]
        sender_name = sender_raw.split("<")[0].strip().strip('"') or sender_raw

        draft = email.get("draft_reply", "").strip()
        draft_section = f'📝 *Drafted Reply:*\n"{draft}"' if draft else "📝 No reply needed"

        msg = (
            f"*EMAIL {i} of {total}*\n"
            f"{priority_emoji} ({score}/10)\n"
            f"👤 *From:* {sender_name}\n"
            f"📧 *Email:* {sender_raw}\n"
            f"📌 *Subject:* {email['subject']}\n"
            f"💬 *Why:* {email['priority_reason']}\n"
            f"\n"
            f"{draft_section}\n"
            f"\n"
            f"👉 Reply: *send {i}* | *skip {i}* | *edit {i} your-text*"
        )
        messages.append(msg)

    # Footer
    messages.append("✅ Reply *done* when finished.")

    # Store as JSON list so send_whatsapp can send individually
    state["briefing_text"] = json.dumps(messages)
    print(f"[build_briefing] Built {len(messages)} WhatsApp messages for {total} emails")
    return state


# ── NODE 6: Send WhatsApp ─────────────────────────────────────────────────────
def send_whatsapp(state: AgentState) -> AgentState:
    """Send one WhatsApp message per email."""
    try:
        messages = json.loads(state["briefing_text"])
    except (json.JSONDecodeError, TypeError):
        messages = [state["briefing_text"]]

    send_whatsapp_messages(messages)
    print(f"[send_whatsapp] Sent {len(messages)} WhatsApp messages")
    return state


# ── NODE 7: Execute Action ────────────────────────────────────────────────────
def execute_action(state: AgentState) -> AgentState:
    reply = (state.get("whatsapp_reply") or "").strip().lower()
    actions = []

    if not reply or reply == "done":
        send_whatsapp_message("👋 Session ended. No emails sent.")
        state["actions_taken"] = ["session_ended"]
        return state

    commands = reply.splitlines()

    for cmd in commands:
        cmd = cmd.strip()
        if cmd.startswith("send "):
            try:
                idx = int(cmd.split()[1]) - 1
                email = state["important_emails"][idx]
                draft = email.get("draft_reply", "")
                if draft:
                    send_email(
                        to=email["sender"],
                        subject=f"Re: {email['subject']}",
                        body=draft,
                        thread_id=email["thread_id"]
                    )
                    actions.append(f"sent: {email['subject']}")
                    send_whatsapp_message(f"✅ Sent reply to: *{email['subject']}*")
            except (IndexError, ValueError):
                send_whatsapp_message(f"⚠️ Could not process: '{cmd}'")

        elif cmd.startswith("skip "):
            try:
                idx = int(cmd.split()[1]) - 1
                email = state["important_emails"][idx]
                actions.append(f"skipped: {email['subject']}")
                send_whatsapp_message(f"⏭ Skipped: *{email['subject']}*")
            except (IndexError, ValueError):
                send_whatsapp_message(f"⚠️ Could not process: '{cmd}'")

        elif cmd.startswith("edit "):
            try:
                parts = cmd.split(maxsplit=2)
                idx = int(parts[1]) - 1
                custom_text = parts[2] if len(parts) > 2 else ""
                email = state["important_emails"][idx]
                if custom_text:
                    send_email(
                        to=email["sender"],
                        subject=f"Re: {email['subject']}",
                        body=custom_text,
                        thread_id=email["thread_id"]
                    )
                    actions.append(f"sent custom: {email['subject']}")
                    send_whatsapp_message(f"✅ Sent your reply to: *{email['subject']}*")
            except (IndexError, ValueError):
                send_whatsapp_message(f"⚠️ Could not process: '{cmd}'")

    state["actions_taken"] = actions
    return state


# ── NODE 8: Update Memory ─────────────────────────────────────────────────────
def update_memory(state: AgentState) -> AgentState:
    for email in state["important_emails"]:
        was_sent = any(email["subject"] in a for a in state["actions_taken"])
        save_thread(
            thread_id=email["thread_id"],
            subject=email["subject"],
            sender=email["sender"],
            status="replied" if was_sent else "pending_followup",
            run_id=state["run_id"]
        )
    print(f"[update_memory] Saved {len(state['important_emails'])} threads to memory")
    return state


def debug_scores(state: AgentState) -> AgentState:
    """Debug endpoint — print all email scores."""
    for e in state["emails"]:
        print(f"Score {e['priority_score']} | {e['subject']} | {e['sender']}")
    return state
