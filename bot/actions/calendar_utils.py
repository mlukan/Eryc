import time  # For current timestamp
import sqlite3
from datetime import datetime, timedelta
from ics import Calendar, Event
from actions.orm import SessionLocal, Slot, User, Session as UserSession, Base
import logging
logger = logging.getLogger(__name__)

def get_unix_minutes(date_obj):
    """Convert a datetime object to Unix timestamp in minutes."""
    return int(date_obj.timestamp() // 60)

def date_to_unix(date_str):
    """Convert date from DD.MM.YYYY to Unix timestamp (seconds since epoch)."""
    try:
        # Parse the string to a datetime object
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        
        # Convert to Unix timestamp
        unix_timestamp = int(date_obj.timestamp())
        return unix_timestamp

    except Exception as e:
        logger.error(f"Error converting date to Unix timestamp: {e}")
        return None

def format_timestamp(unix_minutes):
    """
    Converts a Unix timestamp in minutes to a formatted time string.
    
    - If the timestamp is today → returns "HH:MM"
    - If the timestamp is another day → returns "DD.MM. HH:MM"

    :param unix_minutes: Unix timestamp in minutes
    :return: Formatted time string
    """
    dt = datetime.fromtimestamp(unix_minutes * 60)  # Convert to datetime
    today = datetime.now().date()

    if dt.date() == today:
        return dt.strftime("%H:%M")  # Format as "HH:MM"
    else:
        return dt.strftime("%d.%m. %H:%M")  # Format as "DD.MM. HH:MM"


def get_lookup_date(query):
    """
    Converts a given query (e.g., 'today', 'tomorrow', 'this week', 'next week', 'MM-DD') 
    into start_time and end_time as Unix timestamps in minutes.

    :param query: One of ['today', 'tomorrow', 'this week', 'next week', 'MM-DD']
    :return: Tuple (start_time, end_time) in Unix minutes
    """
    now = datetime.now()
    today = now.date()

    if query == "today" or query == "dnes":
        start_time = get_unix_minutes(now)  # Start from now
        end_time = get_unix_minutes(datetime.combine(today, datetime.min.time().replace(hour=15)))

    elif query == "tomorrow" or query == "zajtra":
        tomorrow = today + timedelta(days=1)
        start_time = get_unix_minutes(datetime.combine(tomorrow, datetime.min.time().replace(hour=7)))
        end_time = get_unix_minutes(datetime.combine(tomorrow, datetime.min.time().replace(hour=15)))

    elif query == "this week" or query == "tento týždeň":
        # From tomorrow until this week's Friday
        friday = today + timedelta(days=(4 - today.weekday()))  # Next Friday
        start_time = get_unix_minutes(datetime.combine(today + timedelta(days=1), datetime.min.time().replace(hour=7)))
        end_time = get_unix_minutes(datetime.combine(friday, datetime.min.time().replace(hour=15)))

    elif query == "next week" or query == "budúci týždeň":
        # Monday to Friday of next week
        next_monday = today + timedelta(days=(7 - today.weekday()))  # Next Monday
        next_friday = next_monday + timedelta(days=4)  # Next Friday
        start_time = get_unix_minutes(datetime.combine(next_monday, datetime.min.time().replace(hour=7)))
        end_time = get_unix_minutes(datetime.combine(next_friday, datetime.min.time().replace(hour=15)))

    else:  
        if isinstance(query,str):
            try:
                if "." in query:
                    day, month = map(int, query.strip(".").split("."))
                elif "-" in query:
                    month, day = map(int, query.split("-"))
                year = today.year if today.month <= month else today.year + 1  # Handle year change
                lookup_date = datetime(year, month, day)

                start_time = get_unix_minutes(datetime.combine(lookup_date, datetime.min.time().replace(hour=7)))
                end_time = get_unix_minutes(datetime.combine(lookup_date, datetime.min.time().replace(hour=15)))
                return start_time, end_time
            except Exception as e:
                logger.error(f"Could not parse date value, error: {e}")
                return None, None
            
        return None, None

    return start_time, end_time

def get_time_slots(location, start_time, end_time):
    session = SessionLocal()
    try:
        logger.info(f"Fetching free slots between {start_time} and {end_time} at {location}")   

        results = (
            session.query(Slot.timestamp)
            .filter(
                Slot.slots_remaining > 0,
                Slot.location == location,
                Slot.timestamp.between(start_time, end_time)
            )
            .order_by(Slot.timestamp.asc())
            .all()
        )

        return [row[0] for row in results]  # extract timestamps

    except Exception as e:
        logger.error(f"Error fetching free slots: {e}")
        return []

    finally:
        session.close()


def generate_ics(date, starttime,endtime,lang):
    # Generate ICS file
    cal = Calendar()
    event = Event()
    event.name = "Blood donation appointment" if lang == "en" else "Darovanie krvi"
    event.begin = f"{date} {starttime}"
    event.end = f"{date} {endtime}"
    event.description = f"Blood donation appointment" if lang == "en" else "Darovanie krvi"
    cal.events.add(event)
    return str(cal)
