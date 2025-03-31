from datetime import datetime, timedelta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
from ics import Calendar, Event
import os
from actions.constants import LOCATIONS

class ActionCheckLocation(Action):

    def name(self) -> Text:
        return "action_check_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        location = tracker.get_slot("slot_location")
        if location and location  in LOCATIONS:
            return [SlotSet("slot_location_status", "found")]
        else:
            return [SlotSet("slot_location_status", "not found")]
