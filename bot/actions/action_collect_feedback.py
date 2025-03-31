from datetime import datetime
import requests
import csv
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language
from actions.calendar_utils import get_unix_minutes
from actions.orm import Base, User, Booking, Slot,Feedback
import logging
import sqlite3
logger = logging.getLogger(__name__)

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
engine = create_engine("sqlite:///../data/faq_database.db")
Session = sessionmaker(bind=engine)
session = Session()
Base=declarative_base()
class ActionCollectFeedback(Action):
    def name(self) -> Text:
        return "action_collect_feedback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        feedback = tracker.get_slot("slot_feedback")
        lang = tracker.get_slot("slot_lang")
        sender = tracker.sender_id
        events = tracker.events
        questions = []
        responses = []
        if events:
            for event in events:
                if event.get("event") == "user":
                    question = event.get("text")
                    if not "SetSlot" in question:
                        questions.append(question)
                elif event.get("event") == "bot":
                    response = event.get("text")
                    responses.append(response)
        last_question = questions[-1] if questions else None
        last_response = responses[-2] if responses else None
        if last_question and last_response:
            logger.info(f"Last question: {last_question}")
            logger.info(f"Last response: {last_response}")
        timestamp = get_unix_minutes(datetime.now())
        try:
            new_feedback = Feedback(
                timestamp=timestamp,
                sender=sender,
                question=last_question,
                response=last_response,
                feedback=feedback
            )

            # Add and commit the new feedback
            session.add(new_feedback)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error while adding feedback: {e}")
        session.close()
        if lang == "en":
            dispatcher.utter_message("Thank you for your feedback!")
        else:
            dispatcher.utter_message("Ďakujeme za vašu spätnú väzbu!")
        return [SlotSet("slot_feedback", "pending")]
     
