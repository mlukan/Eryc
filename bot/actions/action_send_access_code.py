import sqlite3
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language, send_email_verification
from actions.calendar_utils import get_unix_minutes
from datetime import datetime, timedelta
import logging

import random
import time
logger = logging.getLogger(__name__)

class ActionSendAccessCode(Action):
    def name(self) -> Text:
        return "action_send_access_code"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        session_id = tracker.sender_id
        email = tracker.get_slot("slot_user_email")
        lang = tracker.get_slot("slot_lang")
        # Generate a random 6-digit code
        verification_code = random.randint(100000, 999999)
        expires = get_unix_minutes(datetime.now() + timedelta(minutes=30))
        logger.info(f"Verification code for {email}: {verification_code}")
        logger.info(f"Expires: {expires}")
        # Store the verification code in the database   

        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO sessions (email, session, code, expires)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(email) DO UPDATE SET
                       session = excluded.session,
                       code = excluded.code,
                       expires = excluded.expires
                       """, (email, session_id, verification_code, expires))

        conn.commit()
        conn.close()
        logger.info(f"Verification code for {email}: {verification_code}")
        # Send the verification code via email
        send_email_verification(email, verification_code)
        if lang == "en":
            dispatcher.utter_message(text=f"I have sent you a verification code to {email}.")
        else:
            dispatcher.utter_message(text=f"Poslal som vám overovací kód na {email}.")
        return []
     
