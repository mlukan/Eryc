import requests
import csv
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
from actions.calendar_utils import date_to_unix
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
        try:
            conn = sqlite3.connect("../data/calendar.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO  users (email, name, phone, address, dob, sex) VALUES (?, ?, ?, ?, ?, ?)",
                            (slot_user_email,slot_user_name_and_surname, slot_user_phone, slot_user_address, slot_user_dob, slot_user_gender,))
            conn.commit()
            conn.close
            if lang == "en":
                dispatcher.utter_message(text=f"You are now registered with e-mail {slot_user_email}.")
            else:
                dispatcher.utter_message(text=f"Vaša registrácia bola úspešná s e-mailom {slot_user_email}.")
            return []
        except Exception as e:
            logger.error(f"Error registrating user {slot_user_email}: {e}")
            if lang == "en":
                dispatcher.utter_message(text=f"Error registering user {slot_user_email}.")
            else:
                dispatcher.utter_message(text=f"Reistrácia používateľa {slot_user_email} nebola možná.")
