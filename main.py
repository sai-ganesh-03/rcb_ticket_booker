import json
import threading

from RCB_TICKET_BOOKER import RCBTicketBooker
from logger import logger
from telegram import send_telegram_messages

TOKEN_JSON_PATH = "/home/sai-ganesh-s/Projects/rcb_ticket_notifier_v3/token.json"

def main():
    try:
        logger.info(f"Started")
        ticket_booker = RCBTicketBooker()
        event_data=ticket_booker.fetch_event_data()

        if event_data and event_data.get("status") == "Success" and len(event_data.get("result")) == 5:
            send_telegram_messages("Ticket Found")
            logger.info(f"Ticket Found")

            with open(TOKEN_JSON_PATH, 'r') as token_file:
                token_dict = json.loads(token_file.read())
                
                threads = []
                for mobile, auth_token in token_dict.items():
                    logger.info(f"Starting thread for mobile: {mobile}")
                    thread = threading.Thread(target=ticket_booker.book_tickets, args=(event_data, mobile, auth_token))
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()
                    logger.info(f"Thread {thread.name} has completed")

    except Exception as e:
        error_message = f"Unexpected error: {e}"
        logger.critical(error_message, exc_info=True)
        send_telegram_messages(error_message)

if __name__ == "__main__":
    main()