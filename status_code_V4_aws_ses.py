import time
from datetime import datetime
import requests
import pandas as pd
from tqdm import tqdm
from collections import Counter
from bs4 import BeautifulSoup
from utils import send_email_ses, send_finished_email

# Configuration
limit = 200
recipient_email = "sayak@ezyschooling.com"
recipient_email_2 = "mayank@ezyschooling.com"
recipient_email_3 = "data@ezyschooling.com"
SENDER_EMAIL = "sayak.script@gmail.com"  # Replace with your verified email

# AWS SES Configuration
AWS_REGION = "eu-north-1"  # Set to your AWS region

# Send starting email
start_email_subject = "Routine Error Checking Script Running"
start_email_body = "Routine error checking script is running now. You will receive a summary after the task finishes."
send_email_ses(start_email_subject, start_email_body, recipient_email)
send_email_ses(start_email_subject, start_email_body, recipient_email_2)
send_email_ses(start_email_subject, start_email_body, recipient_email_3)

try:
    base_url = "https://api.main.ezyschooling.com/api/v1/schools/document/"
    params = {
        "limit": limit,
        "offset": 0,
        "is_active": "true",
        "is_verified": "true",
        # "collab": "true",
        # "school_city": "delhi"
    }

    all_status_code = []
    all_url = []

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        total_count = response.json()["count"]
        print(f"\nTotal schools count: {total_count}")
    else:
        print(f"Failed to fetch total count: {response.status_code}")
        total_count = 0

    iterations = (total_count // limit) + (1 if total_count % limit != 0 else 0)


    def fetch_data(offset):
        params["offset"] = offset
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            return response.json()["results"]
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return []
        
    def is_error_page(html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            error_text = soup.find('h4', string="Oops !! Couldn't find the page you are looking for.")
            return error_text is not None
        except Exception as e:
            print(f"Error while parsing HTML: {e}")
            return False


    for i in tqdm(range(iterations)):
        offset = i * limit
        results = fetch_data(offset)
        if not results:
            break
        all_url.extend([f"https://ezyschooling.com/school/{result['slug']}" for result in results])

    print("\nChecking URLs...")

    try:
        for url in tqdm(all_url):
            try:
                response = requests.get(url, allow_redirects=True, timeout=10)
                if is_error_page(response.text):
                    all_status_code.append('ErrorPage (200)')
                else:
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
    csv_filename = f"/home/ubuntu/scripts/status_code_{current_datetime}.csv"
    df.to_csv(csv_filename, index=False)

    status_counts = Counter(all_status_code)
    summary = ""
    
    for status, count in status_counts.items():
        summary += f"{status} - {count} URLs\n"
        print(f"{status} - {count} URLs")

    print("\n----- Process Complete -----")

    # Filter 404 and 500 URLs
    urls_404 = [url for url, code in zip(all_url, all_status_code) if code == 'ErrorPage (200)']
    urls_500 = [url for url, code in zip(all_url, all_status_code) if code == 500]
    
    send_finished_email(total_count, summary, urls_404, urls_500, recipient_email, csv_filename)
    send_finished_email(total_count, summary, urls_404, urls_500, recipient_email_2, csv_filename)
    send_finished_email(total_count, summary, urls_404, urls_500, recipient_email_3, csv_filename)

except Exception as e:
    # Send error email with AWS SES
    error_subject = "Error in Script Execution"
    error_body = f"Hello,\n\nAn error occurred during the execution of the script. Details are as follows:\n\n{str(e)}\n\nPlease check the script logs for more information.\n\nThanks,\nSayak Pan"
    send_email_ses(error_subject, error_body, recipient_email)
    send_email_ses(error_subject, error_body, recipient_email_2)
    send_email_ses(error_subject, error_body, recipient_email_3)
