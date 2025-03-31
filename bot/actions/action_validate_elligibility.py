import requests
import csv
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
from actions.calendar_utils import get_lookup_date, get_unix_minutes, format_timestamp
import sqlite3
import logging
import datetime
from sqlalchemy.orm import joinedload
from actions.orm import SessionLocal, User, Booking, Base
logger = logging.getLogger(__name__)

class ActionValidateElligibility(Action):
    def name(self) -> Text:
        return "action_validate_elligibility"

    def get_last_donation_and_sex(self, email):
        session = SessionLocal()
        try:
            # Query the user and eager-load their bookings
            user = (
                session.query(User)
                .options(joinedload(User.bookings))
                .filter(User.email == email)
                .first()
            )

            if not user:
                return None, None

            # Find the most recent successful booking
            last_successful_booking = (
                sorted(
                    (b for b in user.bookings if b.success),
                    key=lambda b: b.timestamp,
                    reverse=True
                )
            )
            last_donation_timestamp = last_successful_booking[0].timestamp if last_successful_booking else None
            return last_donation_timestamp, user.sex

        except Exception as e:
            logger.error(f"Error retrieving last donation and sex: {e}")
            return None, None
        finally:
            session.close()
            
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        lang = tracker.get_slot("slot_lang")
        email = tracker.get_slot("slot_user_email")
        slot_lookup_date = tracker.get_slot("slot_lookup_date")
        start_date, end_date = get_lookup_date(slot_lookup_date)
        logger.info(f"Start date: {start_date}, end date: {end_date}")
        
        if not start_date or not end_date:
            if lang=="en":
                dispatcher.utter_message(text="Please provide a valid date as e.g. 05-13.")
            else:    
                dispatcher.utter_message(text="Prosím, zadajte platný dátum, napr. 13.05.")
            return [SlotSet("slot_lookup_date", None)]
        logger.info(f"Start date: {start_date}, end date: {end_date}")
        
        last_donation_timestamp, sex = self.get_last_donation_and_sex(email)

        recovery_days = 90 if sex == "M" else 120
        logger.info(f"Last donation: {format_timestamp(last_donation_timestamp) if last_donation_timestamp else None}")
        
        elligible_timestamp = last_donation_timestamp + recovery_days * 24 * 60 if last_donation_timestamp else get_unix_minutes(datetime.datetime.now())
        
        logger.info(f"Elligible date for donation: {format_timestamp(elligible_timestamp)}")
        
        if elligible_timestamp < start_date:
            return [SlotSet("slot_elligible_for_donation", True)]
        else:
            if lang == "en":
                dispatcher.utter_message(f"You are not yet elligible for donation, you cannot donate again before {format_timestamp(elligible_timestamp)}.")
            else:
                dispatcher.utter_message(f"Kvôli povinnej rekonvalescencii vo vybranom termíne nemôžete darovať krv, najskôr {format_timestamp(elligible_timestamp)}.")
            return [SlotSet("slot_elligible_for_donation", False),SlotSet("slot_lookup_date", None)]
 
