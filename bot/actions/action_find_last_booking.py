# Description: Action to find the last booking of a user in the database
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
from actions.calendar_utils import get_lookup_date, get_unix_minutes, format_timestamp
import sqlite3
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
        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()
        query = '''
        SELECT timestamp, location, success, status
        FROM booking
        WHERE email = ?
        ORDER BY timestamp DESC
        '''

        try:
            cursor.execute(query, (email,))
            bookings = cursor.fetchall()
            conn.close()
            last_donation = next((row for row in bookings if row[2]== 1) ,None)
            future_booking = next((row for row in bookings if row[0] > get_unix_minutes(datetime.now())),None)
            logger.info(f"Bookings:{bookings}")
            logger.info(f"Future booking: {format_timestamp(future_booking[0]) if future_booking else None}")
            logger.info(f"Last booking: {format_timestamp(last_donation[0]) if last_donation else None}")
            last_donation_timestamp = last_donation[0] if last_donation else None
            last_location = last_donation[1] if last_donation else None
            last_success = last_donation[2] if last_donation else None
        except Exception as e:
            logger.error(f"Could not retrieve last booking: {e}")
        if future_booking:
            return [SlotSet("slot_future_booking", dict(timestamp=future_booking[0],location=future_booking[1]))]
        if last_location:
            return [SlotSet("slot_last_donation_timestamp", last_donation_timestamp), SlotSet("slot_last_location", last_location), SlotSet("slot_last_donation_success", last_success)]
        else:
            dispatcher.utter_message(response="utter_lookup_slot_location")
            logger.info(f"Last location not found")
            return [SlotSet("slot_last_donation_timestamp", None), SlotSet("slot_last_location", None), SlotSet("slot_last_donation_success", None)]

