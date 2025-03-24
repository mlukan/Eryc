from datetime import datetime, timedelta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
from ics import Calendar, Event
import os
from actions.constants import LOCATIONS
import logging
logger = logging.getLogger(__name__)
class ActionAskSlotLocation(Action):

    def name(self) -> Text:
        return "action_ask_slot_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        slot_last_location = tracker.get_slot("slot_last_location")
        lang = tracker.get_slot("slot_lang")
        logger.info(f"Last location from ask_slot_location: {slot_last_location}")
        if not slot_last_location:
            if lang == "en":
                dispatcher.utter_message(text="Please select one of the following locations.",
                                        buttons=[{"title": location, "payload":f"/SetSlots(slot_location={location})"} for location in LOCATIONS]
                                        )       
            else:
                dispatcher.utter_message(text="Vyberte si z nasledovných odberných miest.",
                                        buttons=[{"title": location, "payload":f"/SetSlots(slot_location={location})"} for location in LOCATIONS]
                                        )
        else:
            if lang == "en":
                dispatcher.utter_message(text=f"Your last location was {slot_last_location}. Do you want to book at the same location?",
                                        buttons=[{"title": f"{slot_last_location}", "payload":f"/SetSlots(slot_location={slot_last_location})"}, {"title": "Other", "payload":f"/SetSlots(slot_location=other)"}]
                                        )
            else:
                dispatcher.utter_message(text=f"Vaše posledné odberové miesto bolo {slot_last_location}. Chcete si rezervovať na tomto mieste?",
                                        buttons=[{"title": f"{slot_last_location}", "payload":f"/SetSlots(slot_location={slot_last_location})"}, {"title": "Iné", "payload":f"/SetSlots(slot_location=other)"}]
                                        )
        return []