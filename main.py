from datetime import datetime
import json

from config import config
from logger import logger
from custom_request import get_request,post_request
from telegram import send_telegram_messages

TOKEN_JSON_PATH = "/home/sai-ganesh-s/Projects/rcb_ticket_notifier_v3/token.json"

class RCBTicketBooker:
    def __init__(self):
        pass

    def fetch_event_data(self):
        url = "https://rcbmpapi.ticketgenie.in/ticket/eventlist/O"
        return get_request(url,error_msg=f"Error while fetching event data")

    def select_event(self, events):
        # Sort events by date
        sorted_events = sorted(events, key=lambda x: datetime.strptime(x['event_Date'], "%Y-%m-%dT%H:%M:%S"))
        
        # Select the first upcoming event
        if sorted_events:
            selected_event = sorted_events[0]
            logger.info(f"Selected event: {selected_event['event_Name']} on {selected_event['event_Display_Date']}")
            return selected_event
        
        logger.info("No events found.")
        return None
    
    def get_stands_list(self, event_group_code,mobile,auth_token):
        url = f"https://rcbmpapi.ticketgenie.in/ticket/standslist/{event_group_code}"
        return get_request(url,auth_token,error_msg=f"{mobile} - Error while getting stands_list")
    
    def get_seat_list(self, event_group_code, event_code, stand_code,mobile,auth_token):
        url = f"https://rcbmpapi.ticketgenie.in/ticket/seatlist/{event_group_code}/{event_code}/{stand_code}"
        return get_request(url,auth_token,error_msg=f"{mobile} - Error getting seat list")
    
    def add_to_cart(self, event_group_id, event_id, stand_id, seat_nos, seat_ids,mobile,auth_token):
        url = "https://rcbmpapi.ticketgenie.in/checkout/ticketaddtocart"
        payload = {
            "eventGroupId": event_group_id,
            "eventId": event_id,
            "standId": stand_id,
            "qty": 2,
            "seatNos": seat_nos,
            "seatIds": seat_ids
        }
        
        return post_request(url,payload,auth_token,error_msg=f"{mobile} - Error adding tickets to cart")

    def get_payment_details(self,mobile):
        for detail in config["RCB_PAYLOAD_DETAILS"]:
                if detail["mobile"] == mobile:
                    return detail
                
    def pay_now(self,firstName,lastName,email,mobile,amount,auth_token):
        url="https://rcbmpapi.ticketgenie.in/checkout/proceed"
        payload={
                "addLine1":"",
                "addLine2":"",
                "city":"",
                "landmark":"",
                "pinCode":"",
                "state":"",
                "firstName":firstName,
                "lastName":lastName,
                "email":email,
                "mobile":mobile,
                "netAmount":amount
            }
        return post_request(url,payload,auth_token,error_msg="{mobile} - Error generating payment link")
      
    def book_tickets(self,mobile,auth_token):
        # Fetch event data
        event_data = self.fetch_event_data()
        
        if not event_data or event_data.get("status") != "Success":
            logger.info("No events found or error in fetching events.")
            send_telegram_messages("No events found or error in fetching events.")
            return

        # Select the first upcoming event
        selected_event = self.select_event(event_data['result'])
        if not selected_event:
            logger.info("No event selected.")
            send_telegram_messages("No event selected.")
            return

        # Extract event details
        event_group_code = selected_event.get('event_Group_Code')
        event_code = selected_event.get('event_Code')

        # Get stands list
        stands_data = self.get_stands_list(event_group_code,mobile,auth_token)
        if not stands_data or stands_data.get("status") != "Success":
            logger.info("No stands found or error in fetching stands.")
            return

        # Find stand with price 25000
        stands = stands_data['result'].get('stands', [])
        target_stand = next((stand for stand in stands if stand.get('price') == 30000), None)
        
        if not target_stand:
            logger.info("No stand found with price 25000.")
            return

        stand_code = target_stand['stand_Code']

        # Get seat list
        seat_list_data = self.get_seat_list(event_group_code, event_code, stand_code,mobile,auth_token)
        if not seat_list_data or seat_list_data.get("status") != "Success":
            logger.info("No seats found or error in fetching seats.")
            return

        # Filter available seats
        available_seats = [
            seat for seat in seat_list_data['result'] 
            if seat.get('status') == 'O' and seat.get('bucket') == 'O'
        ]

        # We need at least 2 seats
        if len(available_seats) < 2:
            logger.info("Not enough available seats.")
            return

        # Take first two available seats
        selected_seats = available_seats[:2]

        # Prepare seat details
        seat_nos = ",".join([f"{seat['row']}-{seat['seat_No']}" for seat in selected_seats])
        seat_ids = ",".join(str(seat['i_Id']) for seat in selected_seats)

        # Add to cart
        cart_result = self.add_to_cart(
            event_group_id=event_group_code, 
            event_id=event_code, 
            stand_id=stand_code, 
            seat_nos=seat_nos, 
            seat_ids=seat_ids,
            mobile=mobile,
            auth_token=auth_token,
        )


        if cart_result:
            message = f"{mobile} - Tickets added to cart for {selected_event['event_Name']}! Seats: {seat_nos}"
            logger.info(message)
            logger.info(cart_result)
        else:
            logger.info(f"{mobile} - Failed to add tickets to cart.")
        
        pay_details=self.get_payment_details(mobile)

        pay_now_result=self.pay_now(pay_details["firstName"],pay_details["lastName"],pay_details["email"],mobile,cart_result["result"]["tickets"][0]["subtotal"],auth_token)

        logger.info(pay_now_result)

        if pay_now_result and pay_now_result["status"]=="Success":
            pay_link=pay_now_result["result"]["payment_links"]['web']

            message = f"{mobile} - {pay_link}"
            logger.info(message)
            send_telegram_messages(message)
        else:
            logger.info(f"{mobile} - Failed to create payment link")
            send_telegram_messages(f"{mobile} - Failed to create payment link",)

    def check_timeout(self,mobile,auth_token):
        url="https://rcbmpapi.ticketgenie.in/checkout/ticketcarttimeout"
        return get_request(url,auth_token,error_msg=f"Error while checking timeout for {mobile}")




def main():
    try:
        ticket_booker = RCBTicketBooker()

        with open(TOKEN_JSON_PATH, 'r') as token_file:
            token_dict = json.loads(token_file.read())
            for mobile, auth_token in token_dict.items():
                ticket_booker.book_tickets(mobile,auth_token)

    except Exception as e:
        error_message = f"Unexpected error: {e}"
        logger.critical(error_message, exc_info=True)
        send_telegram_messages(error_message)


if __name__ == "__main__":
    main()

