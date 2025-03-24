from datetime import datetime, timedelta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
from ics import Calendar, Event
import os
from actions.calendar_utils import get_lookup_date, get_time_slots, format_timestamp, get_next_booking_for_user
from actions.constants import LOCATIONS
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
                dispatcher.utter_message(text="Please provide a valid date.")
            else:    
                dispatcher.utter_message(text="Prosím, zadajte platný dátum.")
            return []

        free_slots = get_time_slots("../data/calendar.db", location, start_time, end_time)
        if not free_slots:
            if slot_lang=="en":
                dispatcher.utter_message(text=f"No free booking slots available on {lookup_date}, please try another day or come without booking.")
            else:
                dispatcher.utter_message(text=f"V danom čase nie sú k dispozícii žiadne rezervačné termíny, skúste prosím iný termín, alebo príďte osobne.")
            return [SlotSet("slot_lookup_date", None)]

        buttons = [{"title": format_timestamp(slot), "payload": f"/SetSlots(slot_booking_time={slot})"} for slot in free_slots]
        if slot_lang=="en":
            dispatcher.utter_message(response="utter_lookup_slot_booking_time", buttons=buttons)
        else:
            dispatcher.utter_message(text="utter_lookup_slot_booking_time", buttons=buttons)
        return []


    
class ActionBookSlot(Action):
    def name(self) -> Text:
        return "action_book_slot"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        email = tracker.get_slot("slot_user_email")
        time_slot = tracker.get_slot("slot_booking_time")
        location = tracker.get_slot("slot_location")
        email = email if email else "mlukan@gmail.com"
        slot_lang = tracker.get_slot("slot_lang")
        donation_type = "whole blood"
        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()

        # Check if the slot is already booked
        cursor.execute("SELECT slots_remaining FROM slots WHERE timestamp = ? and location = ?", (time_slot, location))
        if cursor.fetchone()[0]== 0:
            if slot_lang=="en":
                dispatcher.utter_message(text=f"Sorry, the slot {format_timestamp(time_slot)}  in {location} is already booked.")
            else:
                dispatcher.utter_message(text=f"Ľutujem, termín {format_timestamp(time_slot)} v {location} je už obsadený, príďte osobne.")
            conn.close()
            return []

        # Book the slot
        cursor.execute("INSERT INTO booking (location, email, timestamp, donation_type, success, status) VALUES (?, ?, ?, ?, ?, ?)", (location, email, time_slot, donation_type, False, "confirmed"))
        cursor.execute("UPDATE slots SET slots_remaining = slots_remaining - 1 WHERE timestamp = ? and location = ?", (time_slot, location))
        conn.commit()
        conn.close()
        if slot_lang=="en":
            dispatcher.utter_message(text=f"Your booking for {format_timestamp(time_slot)} at {location} is confirmed.")
        else:        
            dispatcher.utter_message(text=f"Vaša rezervácia pre {format_timestamp(time_slot)} v odbernom mieste {location} je potvrdená.")
        return []
    
class ActionCancelBooking(Action):
    def name(self) -> Text:
        return "action_cancel_booking"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        email = tracker.get_slot("slot_user_email")
        future_booking = tracker.get_slot("slot_future_booking")
        email = email if email else "mlukan@gmail.com"
        slot_lang = tracker.get_slot("slot_lang")
        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()
        if future_booking:
            time_slot = future_booking["timestamp"]
            location = future_booking["location"]

            try:
                cursor.execute("DELETE from booking  WHERE timestamp = ? and location = ? and email = ?", (time_slot, location, email,))
                conn.commit()
                conn.close()
                if slot_lang=="en":
                    dispatcher.utter_message(text=f"Your booking for {format_timestamp(time_slot)} at {location} is canceled.")
                else:
                    dispatcher.utter_message(text=f"Vaša rezervácia pre {format_timestamp(time_slot)} v odbernom mieste {location} bola zrušená.")
                logger.info(f"Booking canceled for {email} at {location} on {time_slot}")
                return [SlotSet("slot_location",location)]
            except Exception as e:
                logger.error(f"Could not cancel booking: {e}")
                if slot_lang=="en":
                    dispatcher.utter_message(text=f"Could not cancel booking for {format_timestamp(time_slot)} at {location}.")
                else:
                    dispatcher.utter_message(text=f"Nepodarilo sa zrušiť rezerváciu pre {format_timestamp(time_slot)} v odbernom mieste {location}.")
                return []
        else:
            if slot_lang=="en":
                dispatcher.utter_message(text="No future booking found.")
            else:
                dispatcher.utter_message(text="Nenašla sa žiadna budúca rezervácia.")
            return []


class ActionGenerateICS(Action):
    def name(self) -> Text:
        return "action_generate_ics"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        slot_lang = tracker.get_slot("slot_lang")

        email = next(tracker.get_latest_entity_values("email"), None)
        date = next(tracker.get_latest_entity_values("date"), None)
        time = next(tracker.get_latest_entity_values("time"), None)

        if not email or not date or not time:
            dispatcher.utter_message(text="Please provide your email, date, and time slot.")
            return []

        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()

        # Check if booking exists
        cursor.execute("SELECT COUNT(*) FROM booking WHERE email = ? AND date = ? AND time = ?", (email, date, time))
        if cursor.fetchone()[0] == 0:
            dispatcher.utter_message(text="No such booking found.")
            conn.close()
            return []

        conn.close()

        # Generate ICS file
        cal = Calendar()
        event = Event()
        event.name = "Appointment Booking"
        event.begin = f"{date} {time}:00"
        event.description = f"Appointment booked by {email}"
        cal.events.add(event)

        ics_filename = f"booking_{email}_{date}_{time.replace(':', '')}.ics"
        ics_path = os.path.join(os.getcwd(), ics_filename)

        with open(ics_path, "w") as f:
            f.writelines(cal)

        dispatcher.utter_message(text=f"Here is your ICS file for the booking at {date} {time}.", attachment=ics_filename)

        return []
