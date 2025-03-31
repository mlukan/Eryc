from datetime import datetime, timedelta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
import os
from actions.calendar_utils import get_lookup_date, get_time_slots, format_timestamp, generate_ics
from actions.common_utils import detect_language, send_ics_email
from actions.constants import LOCATIONS
from actions.orm import SessionLocal, User, Booking, Slot, Base
import logging
logger = logging.getLogger(__name__)

class ActionAskSlotBookingTime(Action):

    def name(self) -> Text:
        return "action_ask_slot_booking_time"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        slot_lang = tracker.get_slot("slot_lang")
        lookup_date = tracker.get_slot("slot_lookup_date")
        location = tracker.get_slot("slot_location")
        if not location:
            location = tracker.get_slot("slot_location_choice")

        if not location or location not in LOCATIONS:
            if slot_lang=="en":
                dispatcher.utter_message(text=f"Please provide one of the following locations\n {', '.join(LOCATIONS)}.")
            else:
                dispatcher.utter_message(text=f"Prosím, zadajte jedno z nasledovných miest: \n {', '.join(LOCATIONS)}.")
            return []
        start_time, end_time = get_lookup_date(lookup_date)
        
        if not start_time or not end_time:
            if slot_lang=="en":
                dispatcher.utter_message(text="Please provide a valid date as e.g. 05-13.")
            else:    
                dispatcher.utter_message(text="Prosím, zadajte platný dátum, napr. 13.05.")
            return [SlotSet("slot_lookup_date", None)]

        free_slots = get_time_slots(location, start_time, end_time)
        if not free_slots:
            if slot_lang=="en":
                dispatcher.utter_message(text=f"No free booking slots available on {lookup_date}, please try another day or come without booking.")
            else:
                dispatcher.utter_message(text=f"V danom čase nie sú k dispozícii žiadne rezervačné termíny, skúste prosím iný termín, alebo príďte osobne.")
            return [SlotSet("slot_lookup_date", None)]

        buttons = [{"title": format_timestamp(slot), "payload": f"/SetSlots(slot_booking_time={slot})"} for slot in free_slots]
        dispatcher.utter_message(response="utter_lookup_slot_booking_time", buttons=buttons)
        return []


    
class ActionBookSlot(Action):
    def name(self) -> Text:
        return "action_book_slot"

    def book_time_slot(self,email, location, time_slot, donation_type, slot_lang, dispatcher):
        session = SessionLocal()
        try:
            # Check if slot exists and has remaining capacity
            slot = (
                session.query(Slot)
                .filter(Slot.timestamp == time_slot, Slot.location == location)
                .with_for_update()  # Lock the row for concurrent safety
                .first()
            )

            if not slot or slot.slots_remaining == 0:
                message = (
                    f"Sorry, the slot {format_timestamp(time_slot)} in {location} is already booked."
                    if slot_lang == "en"
                    else f"Ľutujem, termín {format_timestamp(time_slot)} v {location} je už obsadený, príďte osobne."
                )
                dispatcher.utter_message(text=message)
                return []

            # Book the slot
            booking = Booking(
                location=location,
                email=email,
                timestamp=time_slot,
                donation_type=donation_type,
                success=False,
                status="confirmed"
            )
            session.add(booking)

            # Update slot availability
            slot.slots_remaining -= 1

            session.commit()
            return []

        except Exception as e:
            session.rollback()
            logger.error(f"Error booking slot: {e}")
            dispatcher.utter_message(text="An error occurred while booking your slot. Please try again.")
            return []
        finally:
            session.close()


    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        email = tracker.get_slot("slot_user_email")
        time_slot = tracker.get_slot("slot_booking_time")
        location = tracker.get_slot("slot_location")
        email = email if email else "mlukan@gmail.com"
        slot_lang = tracker.get_slot("slot_lang")
        donation_type = "whole blood"
        self.book_time_slot(email, location, time_slot, donation_type, slot_lang, dispatcher)

        dt = datetime.fromtimestamp(time_slot*60)
        date = dt.strftime("%Y-%m-%d")  # '20250330'
        starttime = dt.strftime("%H:%M:%S")  # '1530'
        endtime = (dt + timedelta(minutes=30)).strftime("%H:%M:%S")  # '1600'

        try: 
            ics_content = generate_ics(date, starttime, endtime, slot_lang)
            send_ics_email(email, ics_content, language="en")
            logger.info(f"ICS file sent to {email} for booking at {location} on {time_slot}")
        except Exception as e:
            logger.error(f"Could not send ICS file: {e}")
 
        if slot_lang=="en":
            dispatcher.utter_message(text=f"Your booking for {format_timestamp(time_slot)} at {location} is confirmed.")
        else:        
            dispatcher.utter_message(text=f"Vaša rezervácia pre {format_timestamp(time_slot)} v odbernom mieste {location} je potvrdená.")
        return []
    
class ActionCancelBooking(Action):
    def name(self):
        return "action_cancel_booking"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        email = tracker.get_slot("slot_user_email") or "mlukan@gmail.com"
        future_booking = tracker.get_slot("slot_future_booking")
        slot_lang = tracker.get_slot("slot_lang")

        if not future_booking:
            message = (
                "No future booking found."
                if slot_lang == "en"
                else "Nenašla sa žiadna budúca rezervácia."
            )
            dispatcher.utter_message(text=message)
            return []

        time_slot = future_booking["timestamp"]
        location = future_booking["location"]

        session = SessionLocal()
        try:
            # Locate and delete the booking
            booking = (
                session.query(Booking)
                .filter(
                    Booking.timestamp == time_slot,
                    Booking.location == location,
                    Booking.email == email,
                )
                .first()
            )

            if booking:
                session.delete(booking)
                session.commit()

                message = (
                    f"Your booking for {format_timestamp(time_slot)} at {location} is canceled."
                    if slot_lang == "en"
                    else f"Vaša rezervácia pre {format_timestamp(time_slot)} v odbernom mieste {location} bola zrušená."
                )
                dispatcher.utter_message(text=message)
                logger.info(f"Booking canceled for {email} at {location} on {time_slot}")
                return [SlotSet("slot_location", location)]
            else:
                raise ValueError("Booking not found")

        except Exception as e:
            logger.error(f"Could not cancel booking: {e}")
            message = (
                f"Could not cancel booking for {format_timestamp(time_slot)} at {location}."
                if slot_lang == "en"
                else f"Nepodarilo sa zrušiť rezerváciu pre {format_timestamp(time_slot)} v odbernom mieste {location}."
            )
            dispatcher.utter_message(text=message)
            return []
        finally:
            session.close()


