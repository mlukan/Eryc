import sqlite3
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language, send_email_verification
from actions.calendar_utils import get_unix_minutes
from datetime import datetime, timedelta
from actions.orm import SessionLocal, User, Session as UserSession, Base
import logging

import random
import time
logger = logging.getLogger(__name__)

class ActionSendAccessCode(Action):
    def name(self) -> Text:
        return "action_send_access_code"

    def upsert_user_session(self, email, session_id, verification_code, expires):
        session = SessionLocal()
        try:
            existing_session = session.query(UserSession).filter_by(email=email).first()

            if existing_session:
                # Update existing session
                existing_session.session = session_id
                existing_session.code = verification_code
                existing_session.expires = expires
            else:
                # Insert new session
                new_session = UserSession(
                    email=email,
                    session=session_id,
                    code=verification_code,
                    expires=expires
                )
                session.add(new_session)

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting/updating session: {e}")
        finally:
            session.close()

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        session_id = tracker.sender_id
        email = tracker.get_slot("slot_user_email")
        lang = tracker.get_slot("slot_lang")
        # Generate a random 6-digit code
        verification_code = random.randint(100000, 999999)
        expires = get_unix_minutes(datetime.now() + timedelta(minutes=30))
        logger.info(f"Verification code for {email}: {verification_code}")
        logger.info(f"Expires: {expires}")
        # Store the verification code in the database   
        self.upsert_user_session(email, session_id, verification_code, expires)
        logger.info(f"Verification code for {email}: {verification_code}")
        # Send the verification code via email
        send_email_verification(email, verification_code)
        if lang == "en":
            dispatcher.utter_message(text=f"I have sent you a verification code to {email}.")
        else:
            dispatcher.utter_message(text=f"Poslal som vám overovací kód na {email}.")
        return []
     
