import imaplib
import email
import re
from email.header import decode_header
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from logger import logger
from config import config

OTP_TIME_LIMIT=5

def get_latest_otp(username: str):
    app_password=config["GMAIL_APP_PASSWORDS"][username]
    # Connect to Gmail's IMAP server
    imap_server = 'imap.gmail.com'
    imap = imaplib.IMAP4_SSL(imap_server)
    logger.info(f"Getting latest otp for {username}")

    try:
        # Login using your email and App Password
        imap.login(username, app_password)
        
        # Select the mailbox you want to use (inbox by default)
        imap.select("inbox")

        # Search for emails from the specific sender
        status, messages = imap.search(None, 'FROM "noreply@ticketgenie.in"')
        
        if status != 'OK':
            logger.info("No messages found.")

            return None
        
        # Convert messages to a list of email IDs
        email_ids = messages[0].split()
        
        if not email_ids:
            logger.info("No emails found from noreply@ticketgenie.in")
            return None
        
        # Fetch the latest email from the sender
        latest_email_id = email_ids[-1]
        
        status, msg_data = imap.fetch(latest_email_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse a bytes email into a message object
                msg = email.message_from_bytes(response_part[1])
                
                # Decode email subject
                subject, encoding = decode_header(msg.get("Subject"))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                
                # Get the email date and convert it to a datetime object
                date_str = msg.get("Date")
                email_datetime = parsedate_to_datetime(date_str).astimezone(timezone.utc)
                
                # Get current time (UTC)
                current_time = datetime.now(timezone.utc)
                
                # Calculate time difference in minutes
                time_diff = abs((current_time - email_datetime).total_seconds() / 60)
                
                # Check if the email is within the ±5-minute window
                if time_diff > OTP_TIME_LIMIT:
                    logger.info(f"No recent OTP email found within the last {OTP_TIME_LIMIT} minutes.")
                    return None
                
                # Extract email body
                body = ""
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            try:
                                body = part.get_payload(decode=True).decode()
                                break
                            except:
                                pass
                else:
                    body = msg.get_payload(decode=True).decode()
                
                # Find OTP in the email body (Assuming OTP is a 5-digit number)
                otp_match = re.search(r'\b\d{5}\b', body)
                otp = otp_match.group(0) if otp_match else None

                # Logout and close the connection
                imap.logout()

                # Return the extracted OTP if found
                if otp:
                    logger.info(f"Latest OTP from noreply@ticketgenie.in (Received {time_diff:.2f} minutes ago): {otp}")
                    return otp
                else:
                    logger.info("No OTP found in the latest email.")
                    return None

    except Exception as e:
        logger.info(f"Error: {e}")
        return None


if __name__=="__main__":
    get_latest_otp("sandursaiganesh@gmail.com", "agjo khxu xuhl tgwe")
