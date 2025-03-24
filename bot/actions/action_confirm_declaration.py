from datetime import datetime
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
from actions.calendar_utils import get_unix_minutes
import logging
import sqlite3
import uuid
import json
logger = logging.getLogger(__name__)
class ActionConfirmDeclaration(Action):
    def name(self) -> Text:
        return "action_confirm_declaration"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        email = tracker.get_slot("slot_user_email")
        questionnaire_data = {}
        for slot_name, value in tracker.slots.items():
            if slot_name.startswith("slot_q") and value is not None:
                q_key = slot_name.replace("slot_q", "q")
                questionnaire_data[q_key] = value

        timestamp = get_unix_minutes(datetime.now())
        expires = timestamp + 60 * 24 
        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO forms (timestamp, email, data, form_id,expires)
                       VALUES (?, ?, ?, ?, ?)
                       """, (timestamp, email, json.dumps(questionnaire_data), str(uuid.uuid4()), expires))
        conn.commit()
        conn.close()
        dispatcher.utter_message(response="utter_confirmed_declaration")
        return []
     
