import requests
from logger import logger
from telegram import send_telegram_messages


headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "origin": "https://shop.royalchallengers.com",
            "referer": "https://shop.royalchallengers.com/",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }

def get_request(url,auth_token=None,error_msg=None,notify=False):
    try:
        if auth_token:
            headers["authorization"]=f"Bearer {auth_token}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if not error_msg:
            error_msg=f"URL: {url} | Error fetching data"
        logger.error(error_msg+f" | {e}",exc_info=True)
        if notify:
            send_telegram_messages(error_msg+f" | {e}")
        return None
    
def post_request(url,payload,auth_token=None,error_msg=None,notify=False):
    try:
        if auth_token:
            headers["authorization"]=f"Bearer {auth_token}"
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if not error_msg:
            error_msg=f"URL: {url} | Error fetching data"
        logger.error(error_msg+f" | {e}",exc_info=True)
        if notify:
            send_telegram_messages(error_msg+f" | {e}")
        return None