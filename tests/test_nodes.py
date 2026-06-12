"""
Tests for agent nodes.
Run with: pytest tests/ -v
"""
import pytest
from unittest.mock import patch, MagicMock
from app.agent.nodes import score_emails, filter_important, build_briefing
from app.agent.state import AgentState


def make_state(emails=None) -> AgentState:
    return {
        "emails": emails or [],
        "important_emails": [],
        "briefing_text": "",
        "whatsapp_reply": None,
        "actions_taken": [],
        "run_id": "test-001"
    }


def make_email(subject="Test", score=0):
    return {
        "id": "abc123",
        "thread_id": "thread_abc",
        "sender": "boss@company.com",
        "subject": subject,
        "body": "Please review and respond urgently.",
        "priority_score": score,
        "priority_reason": "",
        "needs_reply": False,
        "draft_reply": None
    }


# ── filter_important ──────────────────────────────────────────────────────────
def test_filter_important_keeps_high_scores():
    state = make_state(emails=[
        make_email("Urgent contract", score=9),
        make_email("Newsletter", score=2),
        make_email("Meeting invite", score=7),
    ])
    result = filter_important(state)
    assert len(result["important_emails"]) == 2
    assert all(e["priority_score"] >= 6 for e in result["important_emails"])


def test_filter_important_empty_inbox():
    state = make_state(emails=[make_email("Promo", score=1)])
    result = filter_important(state)
    assert result["important_emails"] == []


# ── build_briefing ────────────────────────────────────────────────────────────
@patch("app.agent.nodes.client")
def test_build_briefing_no_important_emails(mock_client):
    state = make_state()
    state["important_emails"] = []
    result = build_briefing(state)
    assert "clear" in result["briefing_text"].lower() or "nothing" in result["briefing_text"].lower()
    mock_client.messages.create.assert_not_called()


@patch("app.agent.nodes.client")
def test_build_briefing_calls_claude(mock_client):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="🗂 Email Briefing\n1. Urgent email\nReply 'send 1'")]
    mock_client.messages.create.return_value = mock_response

    state = make_state()
    state["important_emails"] = [make_email("Urgent contract", score=9)]
    state["important_emails"][0]["needs_reply"] = True

    result = build_briefing(state)
    assert result["briefing_text"] != ""
    mock_client.messages.create.assert_called_once()
