from datetime import datetime, timedelta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from ics import Calendar, Event
import os
from actions.constants import LOCATIONS
import logging
from actions.calendar_utils import  format_timestamp
logger = logging.getLogger(__name__)
class ActionAskSlotLocation(Action):

    def name(self) -> Text:
        return "action_ask_slot_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        slot_last_location = tracker.get_slot("slot_last_location")
        lang = tracker.get_slot("slot_lang")
        logger.info(f"Last location from ask_slot_location: {slot_last_location}")
        last_donation_timestamp = tracker.get_slot("slot_last_donation_timestamp")
        if last_donation_timestamp:
            last_donation_time = format_timestamp(last_donation_timestamp)


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
                dispatcher.utter_message(text=f"Your last donation was in {slot_last_location} at {last_donation_time}. Do you want to book at the same location?",
                                        buttons=[{"title": f"{slot_last_location}", "payload":f"/SetSlots(slot_location={slot_last_location})"}, {"title": "Other", "payload":f"/SetSlots(slot_location=other)"}]
                                        )
            else:
                dispatcher.utter_message(text=f"Naposledy ste boli darovať krv {last_donation_time} na odberovom mieste {slot_last_location}. Chcete si rezervovať na tomto mieste?",
                                        buttons=[{"title": f"{slot_last_location}", "payload":f"/SetSlots(slot_location={slot_last_location})"}, {"title": "Iné", "payload":f"/SetSlots(slot_location=other)"}]
                                        )
        return []