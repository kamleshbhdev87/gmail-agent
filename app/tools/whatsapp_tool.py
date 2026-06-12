import os
from twilio.rest import Client


def _get_twilio_client():
    return Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"]
    )


def send_whatsapp_message(body: str) -> bool:
    """Send a single WhatsApp message."""
    client = _get_twilio_client()
    client.messages.create(
        from_=os.environ["TWILIO_WHATSAPP_FROM"],
        to=os.environ["YOUR_WHATSAPP_NUMBER"],
        body=body[:1500]
    )
    return True


def send_whatsapp_messages(messages: list) -> bool:
    """Send a list of WhatsApp messages - one per email."""
    client = _get_twilio_client()
    from_number = os.environ["TWILIO_WHATSAPP_FROM"]
    to_number = os.environ["YOUR_WHATSAPP_NUMBER"]
    for msg in messages:
        client.messages.create(
            from_=from_number,
            to=to_number,
            body=msg[:1500]
        )
    return True


def parse_whatsapp_reply(form_data: dict) -> str:
    """Extract reply text from Twilio webhook form data."""
    return form_data.get("Body", "").strip()
