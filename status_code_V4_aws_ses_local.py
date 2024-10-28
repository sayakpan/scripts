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
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Configuration
collab = False
limit = 200
recipient_email = "sayak@ezyschooling.com"
recipient_email_2 = "mayank@ezyschooling.com"
sender_email = "sayak.script@gmail.com"  # Replace with your email
AWS_REGION = "eu-north-1"  # Set to your AWS region

# Initialize AWS SES client
def send_email_ses(subject, body, recipient_email, attachment_path=None):
    ses_client = boto3.client('ses', region_name=AWS_REGION)
    
    # Construct email
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipient_email
    message.attach(MIMEText(body, 'plain'))

    # Attach file if provided
    if attachment_path:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(attachment_path)}')
            message.attach(part)

    try:
        # Send the email via AWS SES
        response = ses_client.send_raw_email(
            Source=sender_email,
            Destinations=[recipient_email],
            RawMessage={
                'Data': message.as_string(),
            }
        )
        print(f"Email sent successfully! Message ID: {response['MessageId']}")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error sending email: {str(e)}")

# Send starting email
start_email_subject = "Started Executing Script 500"
start_email_body = "Routine error checking script is running now. You will receive a summary after the task finishes."
send_email_ses(start_email_subject, start_email_body, recipient_email)
# send_email_ses(start_email_subject, start_email_body, recipient_email_2)

try:
    # API endpoint
    base_url = "https://api.main.ezyschooling.com/api/v1/schools/document/"
    params = {
        "limit": limit,
        "offset": 0,
        "is_active": "false",
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
        raise RuntimeError(f"Error in retrieving status codes: {e}")

    # Create DataFrame and save to CSV
    df = pd.DataFrame({"url": all_url, "status_code": all_status_code})
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_filename = f"status_code_{current_datetime}.csv"
    df.to_csv(csv_filename, index=False)

    # Print status code counts
    status_counts = Counter(all_status_code)
    print(Fore.BLUE + "\nStatus Code Summary:")
    summary = ""
    for status, count in status_counts.items():
        summary += f"{status} - {count} URLs\n"
        print(f"{status} - {count} URLs")

    # Filter 404 and 500 URLs
    urls_404 = [url for url, code in zip(all_url, all_status_code) if code == 404]
    urls_500 = [url for url, code in zip(all_url, all_status_code) if code == 500]


    # Print "Process Complete" in green
    print(Fore.GREEN + f"\nExported as {csv_filename}")
    print(Fore.GREEN + "\n----- Process Complete -----")
    print(Style.RESET_ALL)  # Reset colorama styles

    # Send completion email with AWS SES
    email_subject = "Task Finished - Ezyschooling URL Status Code Summary"

    email_body = (
        f"Hello,\n\n"
        f"The URL status check for ezyschooling-main has been completed. Here is the summary:\n\n"
        f"Checked URLs - {total_count}.\n{summary}\n\n"
    )

    # Add URLs with 404 errors if there are any
    if urls_404:
        email_body += "URLs with 404 errors:\n" + "\n".join(urls_404) + "\n\n"

    # Add URLs with 500 errors if there are any
    if urls_500:
        email_body += "URLs with 500 errors:\n" + "\n".join(urls_500) + "\n\n"

    email_body += (
        f"Attached to this email, you will find the detailed report, which includes the comprehensive status breakdown for each URL tested.\n\n"
        f"Thanks,\nSayak Pan"
    )

    send_email_ses(email_subject, email_body, recipient_email, csv_filename)
    # send_email_ses(email_subject, email_body, recipient_email_2, csv_filename)

except Exception as e:
    # Send error email with AWS SES
    error_subject = "Error in Script Execution"
    error_body = f"Hello,\n\nAn error occurred during the execution of the script. Details are as follows:\n\n{str(e)}\n\nPlease check the script logs for more information.\n\nThanks,\nSayak Pan"
    send_email_ses(error_subject, error_body, recipient_email)
    # send_email_ses(error_subject, error_body, recipient_email_2)
