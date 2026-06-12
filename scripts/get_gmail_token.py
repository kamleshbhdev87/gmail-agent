import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

CLIENT_CONFIG = {
    "installed": {
        "client_id": os.environ["GMAIL_CLIENT_ID"],
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
        "redirect_uris": ["http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

if __name__ == "__main__":
    flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n✅ Authentication successful!\n")
    print("Add this to your .env file:")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
