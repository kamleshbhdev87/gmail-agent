import os
import base64
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _get_gmail_service():
    """Build authenticated Gmail service using OAuth credentials from env."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send"
        ]
    )
    return build("gmail", "v1", credentials=creds)


def fetch_recent_emails(max_results: int = 20, hours_back: int = 12) -> list:
    """Fetch unread emails from the last N hours."""
    service = _get_gmail_service()

    # Build query: unread, within time window, not promotions/social
    since = (datetime.utcnow() - timedelta(hours=hours_back)).strftime("%Y/%m/%d")
    query = "is:unread"

    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        full = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
        body = _extract_body(full["payload"])

        emails.append({
            "id": msg["id"],
            "thread_id": full["threadId"],
            "sender": headers.get("From", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "body": body[:1500],        # cap at 1500 chars for LLM context
            "priority_score": 0,
            "priority_reason": "",
            "needs_reply": False,
            "draft_reply": None
        })

    return emails


def send_email(to: str, subject: str, body: str, thread_id: str = None) -> bool:
    """Send an email reply, optionally keeping it in the same thread."""
    service = _get_gmail_service()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    payload = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id

    service.users().messages().send(userId="me", body=payload).execute()
    return True


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail payload."""
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        # fallback: recurse into first part
        return _extract_body(payload["parts"][0])
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""
