from colorama import Fore, Style
from collections import Counter
import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


recipient_email = "sayak@ezyschooling.com"
sender_email = "sayak.script@gmail.com"  

# Authenticate Gmail first
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    creds = None
    if os.path.exists('/home/ubuntu/scripts/token.json'):
        creds = Credentials.from_authorized_user_file('/home/ubuntu/scripts/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('/home/ubuntu/scripts/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('/home/ubuntu/scripts/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

creds = authenticate_gmail()

if creds:
    print(Fore.GREEN + "\nAuthorization Successful\n")
else:
    print(Fore.RED + "\nAuthorization Failed\n")


def send_email(creds, recipient_email, subject, body):
    service = build('gmail', 'v1', credentials=creds)

    message = MIMEMultipart()
    message['to'] = recipient_email
    message['from'] = sender_email
    message['subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    raw = {'raw': raw_message}

    service.users().messages().send(userId="me", body=raw).execute()
    print(f'Email sent successfully! - {recipient_email}')

email_subject = "Test Success"
email_body = f"Hello, \n\nEnvironment Test Successful.\nCrontab is going to execute the status test for all urls."

send_email(creds, recipient_email, email_subject, email_body)
