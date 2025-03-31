import requests
import csv
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
from actions.calendar_utils import date_to_unix
from actions.orm import SessionLocal, User, Base
import sqlite3
import logging
logger = logging.getLogger(__name__)

class ActionRegisterUser(Action):
    def name(self) -> Text:
        return "action_register_user"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        lang = tracker.get_slot("slot_lang")
        slot_user_email = tracker.get_slot("slot_user_email")
        slot_user_name_and_surname = tracker.get_slot("slot_user_name_and_surname")
        slot_user_phone = tracker.get_slot("slot_user_phone")
        slot_user_address = tracker.get_slot("slot_user_address")
        slot_user_dob = date_to_unix(tracker.get_slot("slot_user_dob"))
        slot_user_gender = tracker.get_slot("slot_user_gender") 
        session = SessionLocal()

        try:
            new_user = User(
                email=slot_user_email,
                name=slot_user_name_and_surname,
                phone=slot_user_phone,
                address=slot_user_address,
                dob=slot_user_dob,
                sex=slot_user_gender
            )

            session.add(new_user)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error registering user {slot_user_email}: {e}")

            if lang == "en":
                dispatcher.utter_message(text=f"Error registering user {slot_user_email}.")
            else:
                dispatcher.utter_message(text=f"Registrácia používateľa {slot_user_email} nebola možná.")
        finally:
            session.close()