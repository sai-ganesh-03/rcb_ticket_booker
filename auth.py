import json
import time

from config import config
from telegram import send_telegram_messages
from logger import logger
from custom_request import get_request, post_request
from mail import get_latest_otp

TOKEN_JSON_PATH = "/home/sai-ganesh-s/Projects/rcb_ticket_notifier_v3/token.json"
WAIT_FOR_OTP=20

class Auth:
    def __init__(self):
        self.profile_url = "https://rcbmpapi.ticketgenie.in/customer"
        self.login_url = "https://rcbmpapi.ticketgenie.in/customer/login"
        self.verify_otp_url = "https://rcbmpapi.ticketgenie.in/customer/verify"

    def get_invalid_tokens(self):
        invalid_token_numbers = []
        try:
            with open(TOKEN_JSON_PATH, 'r') as token_file:
                token_dict = json.loads(token_file.read())
            for phone, token in token_dict.items():
                response = get_request(self.profile_url, token, error_msg=f"Error while checking validity of token for {phone}")
                if not response:
                    logger.warning(f"Token for {phone} is invalid.")
                    invalid_token_numbers.append(phone)
        except FileNotFoundError:
            logger.error(f"Token file not found at path: {TOKEN_JSON_PATH}")
        except json.JSONDecodeError:
            logger.error("Error decoding token file. Ensure it is a valid JSON.")
        except Exception as e:
            logger.exception(f"Unexpected error while retrieving invalid tokens: {e}")
        return invalid_token_numbers

    def login(self, mobile):
        payload = {
            "email": "",
            "mobile": mobile,
            "utype": "Online"
        }
        try:
            response = post_request(self.login_url, payload)
            if response is None:
                logger.error(f"Login failed for {mobile}")
            return response
        except Exception as e:
            logger.exception(f"Error during login for {mobile}: {e}")
            return None

    def verify(self, mobile, otp):
        payload = {
            "email": "",
            "mobile": mobile,
            "otp": otp,
            "utype": "Online"
        }
        try:
            response = post_request(self.verify_otp_url, payload)
            if response and response.get("status") == "Success":
                token = response["result"]["token"]
                return token
            else:
                logger.error(f"Verification failed for {mobile}. Response: {response}")
                return None
        except Exception as e:
            logger.exception(f"Error during OTP verification for {mobile}: {e}")
            return None

    def get_email_for_number(self, number):
        try:
            for detail in config["RCB_PAYLOAD_DETAILS"]:
                if detail["mobile"] == number:
                    return detail["email"]
            logger.warning(f"No email found for mobile number: {number}")
            return None
        except Exception as e:
            logger.exception(f"Error fetching email for number {number}: {e}")
            return None

    def validate(self):
        logger.info(f"Starting validation for auth tokens")
        try:
            invalid_token_numbers = self.get_invalid_tokens()
            if invalid_token_numbers:
                logger.critical(f"Token invalid for : {invalid_token_numbers}")
                send_telegram_messages(f"Token invalid for : {invalid_token_numbers}")
            else:
                logger.info(f"No invalid token found")
                
        except Exception as e:
            logger.exception(f"Unexpected error during validation: {e}")
    
    def populate_valid_tokens(self,invalid_token_numbers):
        for number in invalid_token_numbers:
            response = self.login(number)
            if response:
                time.sleep(WAIT_FOR_OTP)
                email = self.get_email_for_number(number)
                
                if not email:
                    continue

                otp = get_latest_otp(email)
                if not otp:
                    logger.error(f"Failed to fetch OTP for {number} associated with email: {email}")
                    continue

                token = self.verify(number, otp)
                if not token:
                    continue

                try:
                    with open(TOKEN_JSON_PATH, "r") as token_file:
                        token_dict = json.loads(token_file.read())
                    token_dict[number] = token
                    with open(TOKEN_JSON_PATH, "w") as token_file:
                        json.dump(token_dict, token_file, indent=4)
                    logger.info(f"Token successfully updated for {number}")
                except Exception as e:
                    logger.exception(f"Error updating token file for {number}: {e}")


if __name__ == "__main__":
    auth = Auth()
    auth.validate()
    # invalid_numbers=auth.get_invalid_tokens()
    # auth.populate_valid_tokens(invalid_numbers)