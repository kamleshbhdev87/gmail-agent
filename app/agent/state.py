from typing import TypedDict, List, Optional


class EmailItem(TypedDict):
    id: str
    sender: str
    subject: str
    body: str
    thread_id: str
    priority_score: int
    priority_reason: str
    needs_reply: bool
    draft_reply: Optional[str]


class AgentState(TypedDict):
    emails: List[EmailItem]
    important_emails: List[EmailItem]
    briefing_text: str
    whatsapp_reply: Optional[str]
    actions_taken: List[str]
    run_id: str
