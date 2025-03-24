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
logger = logging.getLogger(__name__)

class ActionValidateElligibility(Action):
    def name(self) -> Text:
        return "action_validate_elligibility"

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
        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()
        query = '''
        SELECT timestamp
        FROM booking
        WHERE email = ? AND success = 1 
        ORDER BY timestamp DESC
        LIMIT 1
        '''
        cursor.execute(query, (email,))
        last_donation_timestamp = cursor.fetchone()
        sex_query = '''
        SELECT
        sex
        FROM users
        WHERE email = ?
        '''
        cursor.execute(sex_query, (email,))
        sex = cursor.fetchone()
        conn.close()

        recovery_days = 90 if sex == "M" else 120
        logger.info(f"Last donation: {format_timestamp(last_donation_timestamp[0]) if last_donation_timestamp else None}")
        elligible_timestamp = last_donation_timestamp[0] + recovery_days * 24 * 60 if last_donation_timestamp else get_unix_minutes(datetime.datetime.now())
        logger.info(f"Elligible date for donation: {format_timestamp(elligible_timestamp)}")
        if elligible_timestamp < start_date:
            return [SlotSet("slot_elligible_for_donation", True)]
        else:
            if lang == "en":
                dispatcher.utter_message(f"You are not yet elligible for donation, you cannot donate again before {format_timestamp(elligible_timestamp)}.")
            else:
                dispatcher.utter_message(f"Kvôli povinnej rekonvalescencii vo vybranom termíne nemôžete darovať krv, najskôr {format_timestamp(elligible_timestamp)}.")
            return [SlotSet("slot_elligible_for_donation", False),SlotSet("slot_lookup_date", None)]
 
