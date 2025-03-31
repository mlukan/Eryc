import requests
import csv
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
import logging
logger = logging.getLogger(__name__)
class ActionInitiate(Action):
    def name(self) -> Text:
        return "action_initiate"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        message = tracker.latest_message.get("text")
        logger.info(f"Detecting language for message: {message}")
        language = detect_language(message)
        logger.info(f"Detected language: {language}")
        return [SlotSet("slot_lang", language)]
     
