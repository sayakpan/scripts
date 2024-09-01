import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

AWS_REGION = "eu-north-1"  # Set to your AWS region
SENDER_EMAIL = "sayak.script@gmail.com"  # Must be a verified email in SES
RECIPIENT_EMAIL = "sayak@ezyschooling.com"  # Recipient email

def send_email_ses(subject, body, recipient_email):
    # Initialize AWS SES client using default credentials from 'aws configure'
    ses_client = boto3.client('ses', region_name=AWS_REGION)

    # Construct email
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = SENDER_EMAIL
    message['To'] = recipient_email
    message.attach(MIMEText(body, 'plain'))

    try:
        # Send the email via AWS SES
        response = ses_client.send_raw_email(
            Source=SENDER_EMAIL,
            Destinations=[recipient_email],
            RawMessage={
                'Data': message.as_string(),
            }
        )
        print(f"Email sent successfully! Message ID: {response['MessageId']}")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error sending email: {str(e)}")

# Test email
email_subject = "Test Success"
email_body = "Hello,\n\nEnvironment Test Successful."
send_email_ses(email_subject, email_body, RECIPIENT_EMAIL)