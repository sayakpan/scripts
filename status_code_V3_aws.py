import time
from datetime import datetime
import requests
import pandas as pd
from colorama import Fore, Style
from tqdm import tqdm
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

# Configuration
collab = False
limit = 200
recipient_email = "sayak@ezyschooling.com"
recipient_email_2 = "mayank@ezyschooling.com"
sender_email = "sayak.script@gmail.com"  # Replace with your email

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

# API endpoint
base_url = "https://api.main.ezyschooling.com/api/v1/schools/document/"
params = {
    "limit": limit,
    "offset": 0,
    "is_active": "true",
    "is_verified": "true"
}
if collab:
    params["collab"] = "true"

# Initialize lists to store URLs and status codes
all_status_code = []
all_url = []

# Fetch total count
print(Fore.YELLOW + "Fetching total count from API...")
response = requests.get(base_url, params=params)
if response.status_code == 200:
    total_count = response.json()["count"]
    print(Fore.GREEN + "Success!")
    print(Fore.GREEN + f"\nTotal schools count: {total_count}")
else:
    print(Fore.RED + f"Failed to fetch total count: {response.status_code}")
    total_count = 0

# Calculate the number of iterations needed
iterations = (total_count // limit) + (1 if total_count % limit != 0 else 0)
print(Fore.GREEN + f"Total iterations needed: {iterations}")

# Function to get data from the API
def fetch_data(offset):
    params["offset"] = offset
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()["results"]
    else:
        print(Fore.RED + f"Failed to fetch data: {response.status_code}")
        return []

# Fetch data from the API using a for loop
print(Fore.BLUE + "\nLoading all URLs from API...")
for i in tqdm(range(iterations)):
    offset = i * limit
    results = fetch_data(offset)
    if not results:
        break
    all_url.extend([f"https://ezyschooling.com/school/{result['slug']}" for result in results])

print(Fore.GREEN + "\nURL Loading complete!")
print(Fore.YELLOW + "\nChecking URLs...")

# Check status codes for all URLs
try:
    for url in tqdm(all_url):
        try:
            response = requests.get(url, allow_redirects=True, timeout=10)
            all_status_code.append(response.status_code)
        except requests.TooManyRedirects:
            all_status_code.append('TooManyRedirects')
        except requests.RequestException as e:
            all_status_code.append(f'Error: {str(e)}')
        time.sleep(1) 
except Exception as e:
    print(Fore.RED + f"Error in retrieving status codes: {e}")

# Create DataFrame and save to CSV
df = pd.DataFrame({"url": all_url, "status_code": all_status_code})
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = f"/home/ubuntu/scripts/status_code_{current_datetime}.csv"
df.to_csv(csv_filename, index=False)

# Print status code counts
status_counts = Counter(all_status_code)
print(Fore.BLUE + "\nStatus Code Summary:")
summary = ""
for status, count in status_counts.items():
    summary += f"{status} - {count} URLs\n"
    print(f"{status} - {count} URLs")

# Print "Process Complete" in green
print(Fore.GREEN + f"\nExported as {csv_filename}")
print(Fore.GREEN + "\n----- Process Complete -----")
print(Style.RESET_ALL)  # Reset colorama styles

def send_email(creds, recipient_email, subject, body, attachment_path):
    service = build('gmail', 'v1', credentials=creds)

    message = MIMEMultipart()
    message['to'] = recipient_email
    message['from'] = sender_email
    message['subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(attachment_path)}')
        message.attach(part)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    raw = {'raw': raw_message}

    service.users().messages().send(userId="me", body=raw).execute()
    print(f'Email sent successfully! - {recipient_email}')

email_subject = "Task Finished - Ezyschooling URL Status Code Summary"
email_body = f"Hello,\n\nThe URL status check for ezyschooling-main has been completed. Here is the summary of the status of urls of Ezyschooling-Main:\n\nChecked URLs - {total_count}.\n{summary}\n\nAttached to this email, you will find the detailed report, which includes the comprehensive status breakdown for each URL tested.\n\nThanks,\nSayak Pan"

send_email(creds, recipient_email, email_subject, email_body, csv_filename)
send_email(creds, recipient_email_2, email_subject, email_body, csv_filename)
