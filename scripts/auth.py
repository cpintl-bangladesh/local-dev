#!/usr/bin/env python3
"""
CPI Bangladesh Mission — OAuth Authentication
Uses your personal Google account (ariful@cpintl.org)
No service account or GCP billing required.
Run once: python3 scripts/auth.py
Token is saved and reused automatically.
"""

import os, sys, json, webbrowser
from pathlib import Path

BASE_DIR  = Path(__file__).resolve().parent.parent
CREDS     = BASE_DIR / "config" / "credentials.json"
TOKEN     = BASE_DIR / "config" / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]

def get_credentials():
    """Return valid credentials, refreshing or re-authorising as needed."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None

    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())
        else:
            if not CREDS.exists():
                print(f"""
╔══════════════════════════════════════════════════════════════╗
║  credentials.json not found at: config/credentials.json     ║
║                                                              ║
║  Please follow the instructions in:                         ║
║  config/oauth_setup_instructions.txt                        ║
╚══════════════════════════════════════════════════════════════╝
""")
                sys.exit(1)

            print("🌐 Opening browser for Google sign-in (ariful@cpintl.org)...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS), SCOPES)
            creds = flow.run_local_server(
                port=0,
                success_message="✅ Authentication successful! You can close this tab.",
                open_browser=True
            )

        TOKEN.parent.mkdir(parents=True, exist_ok=True)
        TOKEN.write_text(creds.to_json())
        print(f"✅ Token saved to {TOKEN}")

    return creds


def build_services(creds=None):
    """Build and return Drive, Sheets, Docs API service objects."""
    from googleapiclient.discovery import build

    if creds is None:
        creds = get_credentials()

    drive  = build("drive",  "v3", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)
    docs   = build("docs",   "v1", credentials=creds)

    return drive, sheets, docs


if __name__ == "__main__":
    print("\n🔐 CPI Bangladesh Mission — Google Authentication\n")
    creds = get_credentials()
    drive, sheets, docs = build_services(creds)

    # Quick test
    about = drive.about().get(fields="user").execute()
    user  = about.get("user", {})
    print(f"\n✅ Authenticated as: {user.get('displayName')} ({user.get('emailAddress')})")
    print("✅ Drive API: ready")
    print("✅ Sheets API: ready")
    print("✅ Docs API: ready\n")
