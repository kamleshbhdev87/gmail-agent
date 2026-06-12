import os
import chromadb
from datetime import datetime

# Use in-memory client for free Render deployment
_client = chromadb.EphemeralClient()


def _get_collection():
    return _client.get_or_create_collection(
        name="email_threads",
        metadata={"description": "Email thread history and follow-up tracking"}
    )


def save_thread(thread_id: str, subject: str, sender: str, status: str, run_id: str):
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
    return get_thread_history(status="pending_followup")
