import requests
import csv
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
import sqlite3
import logging
logger = logging.getLogger(__name__)

class ActionValidateEmail(Action):
    def name(self) -> Text:
        return "action_validate_email"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        email = tracker.get_slot("slot_user_email")

        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()
        cursor.execute("SELECT email,sex FROM users WHERE email = ?", (email,))
        res = cursor.fetchone()
        conn.close
        if res:
            sex = res[1]
            return [SlotSet("slot_email_valid", True),SlotSet("slot_user_gender",sex)]
        else:
            return [SlotSet("slot_email_valid", False)]
