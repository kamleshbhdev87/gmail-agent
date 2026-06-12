import os
import json
from datetime import datetime
import chromadb
from chromadb.config import Settings


def _get_client():
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
    return chromadb.PersistentClient(path=persist_dir)


def _get_collection():
    client = _get_client()
    return client.get_or_create_collection(
        name="email_threads",
        metadata={"description": "Email thread history and follow-up tracking"}
    )


def save_thread(thread_id: str, subject: str, sender: str, status: str, run_id: str):
    """
    Save or update a thread in memory.

    status options:
        'pending_followup'  — important email, no reply sent yet
        'replied'           — reply was sent this run
        'resolved'          — no longer needs attention
    """
    collection = _get_collection()
    doc_id = f"thread_{thread_id}"

    metadata = {
        "thread_id": thread_id,
        "subject": subject,
        "sender": sender,
        "status": status,
        "run_id": run_id,
        "updated_at": datetime.utcnow().isoformat()
    }

    # Upsert — update if exists, insert if not
    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass

    collection.add(
        ids=[doc_id],
        documents=[f"{sender} | {subject}"],
        metadatas=[metadata]
    )


def get_thread_history(sender: str = None, status: str = None, limit: int = 20) -> list:
    """
    Query thread history. Filter by sender or status.

    Useful for: 'Have I already replied to this person this week?'
    """
    collection = _get_collection()

    where = {}
    if sender:
        where["sender"] = {"$contains": sender}
    if status:
        where["status"] = status

    try:
        if where:
            results = collection.get(where=where, limit=limit)
        else:
            results = collection.get(limit=limit)
        return results.get("metadatas", [])
    except Exception:
        return []


def get_pending_followups() -> list:
    """Return all threads still waiting for a reply."""
    return get_thread_history(status="pending_followup")
