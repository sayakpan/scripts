import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def send_email_ses(subject, body, recipient_email, attachment_path=None):
    sender_email = "sayak.script@gmail.com"  # Replace with your email
    AWS_REGION = "eu-north-1"

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

def send_finished_email(total_count, summary, urls_404, urls_500, recipient_email, csv_filename):
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