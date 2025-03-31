# Description: Action to find the last booking of a user in the database
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
from actions.calendar_utils import get_lookup_date, get_unix_minutes, format_timestamp
import sqlite3
from actions.orm import SessionLocal, Booking, Base
import logging
from datetime import datetime
logger = logging.getLogger(__name__)

class ActionFindLastBooking(Action):
    def name(self) -> Text:
        return "action_find_last_booking"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id

        email = tracker.get_slot("slot_user_email")
        lang = tracker.get_slot("slot_lang")
        session = SessionLocal()
        try:
            # Get all bookings for the email, ordered by most recent
            bookings = (
                session.query(Booking)
                .filter(Booking.email == email)
                .order_by(Booking.timestamp.desc())
                .all()
            )

            # Extract last successful donation
            last_donation = next((b for b in bookings if b.success is True), None)

            # Extract next upcoming booking (timestamp > now)
            future_booking = next(
                (b for b in bookings if b.timestamp > get_unix_minutes(datetime.now())), 
                None
            )

            logger.info(f"Bookings: {bookings}")
            logger.info(
                f"Future booking: {format_timestamp(future_booking.timestamp) if future_booking else None}"
            )
            logger.info(
                f"Last booking: {format_timestamp(last_donation.timestamp) if last_donation else None}"
            )

            last_donation_timestamp = last_donation.timestamp if last_donation else None
            last_location = last_donation.location if last_donation else None
            last_success = last_donation.success if last_donation else None

        except Exception as e:
            logger.error(f"Could not retrieve last booking: {e}")

        finally:
            session.close()
        if future_booking:
            return [SlotSet("slot_future_booking", dict(timestamp=future_booking.timestamp,location=future_booking.location))]
        if last_location:
            return [SlotSet("slot_last_donation_timestamp", last_donation_timestamp), SlotSet("slot_last_location", last_location), SlotSet("slot_last_donation_success", last_success)]
        else:
            dispatcher.utter_message(response="utter_lookup_slot_location")
            logger.info(f"Last location not found")
            return [SlotSet("slot_last_donation_timestamp", None), SlotSet("slot_last_location", None), SlotSet("slot_last_donation_success", None)]

