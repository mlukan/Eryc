import requests
import csv
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
import faiss
import os
import logging
import numpy as np
import json
import faiss
import numpy as np
import sqlite3
import litellm
import ast
from actions.common_utils import detect_language
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from actions.orm import FAQ
engine = create_engine("sqlite:///../data/faq_database.db")
Session = sessionmaker(bind=engine)
session = Session()
Base=declarative_base()
litellm.api_key = os.getenv("AZURE_API_KEY")
litellm.api_base = os.getenv("AZURE_API_BASE")
logger = logging.getLogger(__name__)

# get embeddings from the SQlite

def get_embeddings_from_db():
    """Retrieve all embeddings from the FAQ table using SQLAlchemy."""
    try:
        results = session.query(FAQ.embeddings).all()
        return results  # Each item is a tuple: (embedding,)
    except Exception as e:
        logger.error(f"Error retrieving embeddings: {e}")
        return []
    finally:
        session.close()

def query_db_by_ids(ids: list):
    """Retrieve responses from the database for the given list of IDs using SQLAlchemy."""
    if not ids:
        return []
    try:
        faqs = session.query(FAQ.response).filter(FAQ.id.in_(ids)).all()
        results = [row[0] for row in faqs]  # each row is a tuple like (response,)
        return results
    except Exception as e:
        logger.error(f"Error querying FAQ responses by IDs: {e}")
        return []
    finally:
        session.close()

# Build FAISS index
def build_faiss_index(embeddings_from_db):
    embeddings = [np.frombuffer(row[0], dtype=np.float32) for row in embeddings_from_db]
    embeddings = np.vstack(embeddings)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

# Generate embeddings using litellm
def generate_embeddings(query):
    response = litellm.embedding(
        model="azure/text-embedding-3-large",
        deployment_id="text-embedding-3-large",
        api_version="2023-05-15",
        input=query)
         
    return np.array(response["data"][0]["embedding"], dtype='float32')


def search_faiss(query, index, top_k=3):
    """Search FAISS index and return the top-k responses from SQLite."""
    query_embedding = generate_embeddings(query).reshape(1, -1)
    distances, indices = index.search(query_embedding, top_k)
    
    # Ensure valid indices
    valid_indices = [int(idx)+1 for idx in indices[0] if idx >= 0]
    logger.debug(f"Valid indices: {valid_indices}")
    # Retrieve responses from the database
    responses = query_db_by_ids(valid_indices)
    logger.debug(f"Top-{top_k} responses: {responses}")
    return responses

data = get_embeddings_from_db()
index = build_faiss_index(data)

def rephrase(question,response):
    prompt = f"""
    Your task is to select the most appropriate response to the question from a selection of three responses. 
    If none of the responses is relevant to the question, you can also choose to provide a new response, but it must be relevant to the question.
    If you choose to provide a new response, please make sure that the response is in the language of the question.
    If you choose to provide a new response, state clearly the following as part of the response:
    "I could not find a relevant response to the question in the NTS database, but maybe the following answer will help you."
    \n
    Question: {question}
    Responses:
    {response[0]} \n
    {response[1]} \n
    {response[2]} \n
    """
    prompt_slovak = f"""
    Your task is to select the most appropriate response to the question from a selection of three responses. 
    If none of the responses is relevant to the question, you can also choose to provide a new response, but it must be relevant to the question.
    If you choose to provide a new response, please make sure that the response is in the language of the question.
    If you choose to provide a new response, state clearly the following as part of the response:
    "V databáze NTS otázok a odpovedí som bohužiaľ nenašiel žiadnu relevantnú odpoveď na Vašu otázku, ale možno Vám pomôže nasledujúca odpoveď."
    \n
    Question: {question}
    Responses:
    {response[0]} \n
    {response[1]} \n
    {response[2]} \n
    """
    language = detect_language(question)

    if language == "en":
        prompt = prompt
    else:
        prompt = prompt_slovak
   

    response = litellm.completion(
        model="azure/gpt-4",
        deployment_id="gpt-4-turbo",
        messages=[{ "content": prompt,"role": "user"}])
    result = response.choices[0].message.content
    
    return result

class ActionSearchFaiss(Action):
    def name(self) -> Text:
        return "action_search_faiss"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Retrieve session_id from tracker.sender_id
        message = tracker.latest_message.get("text")
        lang = tracker.get_slot("slot_lang")
        response = search_faiss(message, index)
        if response:
            message = rephrase(message,response)
            dispatcher.utter_message(text=message)
        else:
            if lang == "en":
                dispatcher.utter_message(text="Sorry, I couldn't find any relevant information.")
            else:
                dispatcher.utter_message(text="Ospravedlňujem sa, ale neviem nájsť žiadne relevantné informácie.")
        return  []






       