from datetime import datetime, timedelta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from actions.common_utils import detect_language, send_qr_code, generate_qr_code
from actions.calendar_utils import get_unix_minutes
from actions.orm import SessionLocal, Form, Base
import logging
import sqlite3
import uuid
import json
logger = logging.getLogger(__name__)
class ActionConfirmDeclaration(Action):
    def name(self) -> Text:
        return "action_confirm_declaration"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        email = tracker.get_slot("slot_user_email")
        questionnaire_data = {}
        for slot_name, value in tracker.slots.items():
            if slot_name.startswith("slot_q") and value is not None:
                q_key = slot_name.replace("slot_q", "q")
                questionnaire_data[q_key] = value
        timestamp = get_unix_minutes(datetime.now())
        expires_dt = datetime.now()+ timedelta(days=1)
        expires = get_unix_minutes(expires_dt)
        form_id = str(uuid.uuid4())
        session = SessionLocal()
        try:
            new_form = Form(
                timestamp=timestamp,
                email=email,
                data=json.dumps(questionnaire_data),
                form_id=form_id,
                expires=expires
            )

            session.add(new_form)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error inserting form: {e}")
        finally:
            session.close()
        lang = tracker.get_slot("slot_lang")
        # Generate and send the QR code to the user
        qr_code = generate_qr_code({"UID": form_id, "expires": expires_dt.strftime("%d.%m.%Y %H:%M")})
        send_qr_code(email, qr_code, lang)

        dispatcher.utter_message(response="utter_confirmed_declaration")
        return [SlotSet("slot_wants_to_register", False),SlotSet("slot_start_questionnaire", False)]
     
