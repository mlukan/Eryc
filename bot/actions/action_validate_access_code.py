import sqlite3
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language, validate_access_code
import logging
logger = logging.getLogger(__name__)

class ActionValidateAccessCode(Action):
    def name(self) -> Text:
        return "action_validate_access_code"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        session_id = tracker.sender_id
        logger.info(f"Session ID: {session_id}")
        acess_code_from_user = int(tracker.get_slot("slot_access_code")) if tracker.get_slot("slot_access_code") else None
        logger.info(f"Access code from user: {acess_code_from_user}")
        email = tracker.get_slot("slot_user_email")
        code_valid = validate_access_code(email,acess_code_from_user,session_id)
        logger.info(f"Access code valid: {code_valid}")
        
        if code_valid:
            return [SlotSet("slot_access_code_valid", code_valid),SlotSet("slot_email_valid", True), 
                    SlotSet("slot_user_email", email)]
        else:
            return [SlotSet("slot_access_code_valid", code_valid),SlotSet("slot_email_valid", None), 
                    SlotSet("slot_user_email", email), SlotSet("slot_access_code", None)]
     
