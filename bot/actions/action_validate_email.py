import requests
import csv
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
from actions.orm import SessionLocal, User,Base
import sqlite3
import logging
logger = logging.getLogger(__name__)

class ActionValidateEmail(Action):
    def name(self) -> Text:
        return "action_validate_email"

    def get_user_email_and_sex(self, email):
        session = SessionLocal()
        try:
            result = session.query(User.email, User.sex).filter(User.email == email).first()
            return result  # returns a tuple: (email, sex) or None
        except Exception as e:
            logger.error(f"Error retrieving user: {e}")
            return None
        finally:
            session.close()

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        email = tracker.get_slot("slot_user_email")
        res = self.get_user_email_and_sex(email)
        if res:
            sex = res[1]
            return [SlotSet("slot_email_valid", True),SlotSet("slot_user_gender",sex)]
        else:
            return [SlotSet("slot_email_valid", False)]
