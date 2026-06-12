SCORE_EMAIL_PROMPT = """
You are an email priority scorer. Score this email from 1-10 for urgency and importance.
Return JSON only - no preamble, no markdown:
{{"score": int, "reason": str, "needs_reply": bool}}

Scoring rules:
- 9-10: Words like URGENT, ASAP, "call me", "as soon as possible", "immediately", deadlines today, money, legal
- 7-8:  Action needed, questions directed at me, meeting requests, follow-ups
- 5-6:  FYI but relevant, team updates, informational
- 3-4:  Low urgency, no action needed
- 1-2:  Newsletter, promo, automated notification

IMPORTANT: If subject or body contains "urgent", "URGENT", "call me",
"as soon as possible", "ASAP", "immediately" - score MUST be 9 or 10.

From: {sender}
Subject: {subject}
Body (first 600 chars): {body}
"""

DRAFT_REPLY_PROMPT = """
Draft a concise, professional reply to this email.
- Keep it under 100 words
- Match the tone of the original
- Leave [PLACEHOLDER] for any specific details I need to fill in
- Do NOT add subject line, just the reply body
- Write the actual reply text, not a template

From: {sender}
Subject: {subject}
Original email: {body}
"""
