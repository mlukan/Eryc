from datetime import datetime, timedelta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
from ics import Calendar, Event
import os
from actions.constants import LOCATIONS

class ActionAskSlotLocationChoice(Action):

    def name(self) -> Text:
        return "action_ask_slot_location_choice"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        slot_last_location = tracker.get_slot("slot_last_location")
        lang = tracker.get_slot("slot_lang")
        if lang == "en":
            dispatcher.utter_message(text="Please select one of the following locations.",
                                     buttons=[{"title": location, "payload":f"/SetSlots(slot_location={location})"} for location in LOCATIONS if location != slot_last_location]
                                     )       
        else:
            dispatcher.utter_message(text="Vyberte si z nasledovných odberných miest.",
                                     buttons=[{"title": location, "payload":f"/SetSlots(slot_location={location})"} for location in LOCATIONS if location != slot_last_location]
                                     )