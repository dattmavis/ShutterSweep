import os
import json
import google.auth
import google_auth_oauthlib.flow
import google.auth.transport.requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Set the path to the credentials file you downloaded from the Google Cloud Console
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "oauth.json")
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.appendonly"]

def get_credentials():
    creds = None
    token_path = "token.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds
