import time  # For current timestamp
import sqlite3
from datetime import datetime, timedelta
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

    if query == "today":
        start_time = get_unix_minutes(now)  # Start from now
        end_time = get_unix_minutes(datetime.combine(today, datetime.min.time().replace(hour=15)))

    elif query == "tomorrow":
        tomorrow = today + timedelta(days=1)
        start_time = get_unix_minutes(datetime.combine(tomorrow, datetime.min.time().replace(hour=7)))
        end_time = get_unix_minutes(datetime.combine(tomorrow, datetime.min.time().replace(hour=15)))

    elif query == "this week":
        # From tomorrow until this week's Friday
        friday = today + timedelta(days=(4 - today.weekday()))  # Next Friday
        start_time = get_unix_minutes(datetime.combine(today + timedelta(days=1), datetime.min.time().replace(hour=7)))
        end_time = get_unix_minutes(datetime.combine(friday, datetime.min.time().replace(hour=15)))

    elif query == "next week":
        # Monday to Friday of next week
        next_monday = today + timedelta(days=(7 - today.weekday()))  # Next Monday
        next_friday = next_monday + timedelta(days=4)  # Next Friday
        start_time = get_unix_minutes(datetime.combine(next_monday, datetime.min.time().replace(hour=7)))
        end_time = get_unix_minutes(datetime.combine(next_friday, datetime.min.time().replace(hour=15)))

    else:  # Assume "MM-DD" format
        
        try:
            if "." in query:
                day, month, _ = map(int, query.split("."))
            else:
                month, day = map(int, query.split("-"))
            year = today.year if today.month <= month else today.year + 1  # Handle year change
            lookup_date = datetime(year, month, day)

            start_time = get_unix_minutes(datetime.combine(lookup_date, datetime.min.time().replace(hour=7)))
            end_time = get_unix_minutes(datetime.combine(lookup_date, datetime.min.time().replace(hour=15)))

        except ValueError:
             # From tomorrow until this week's Friday
            friday = today + timedelta(days=(4 - today.weekday()))  # Next Friday
            start_time = get_unix_minutes(datetime.combine(today + timedelta(days=1), datetime.min.time().replace(hour=7)))
            end_time = get_unix_minutes(datetime.combine(friday, datetime.min.time().replace(hour=15)))


    return start_time, end_time

def get_time_slots(db_path, location, start_time, end_time):
    """
    Retrieves all available time slots between start_time and end_time.

    :param db_path: Path to the SQLite database
    :param start_time: Start time in Unix minutes
    :param end_time: End time in Unix minutes
    :return: List of available timestamps
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp FROM slots 
        WHERE slots_remaining > 0 AND  location = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """, (location, start_time, end_time))
    logger.info(f"Fetching free slots between {start_time} and {end_time} at {location}")   
    results = [row[0] for row in cursor.fetchall()]
    conn.close()

    return results


def book_slot(db_path, email, timestamp, donation_type, location, note=""):
    """
    Books a slot for a given timestamp and location if available.

    :param db_path: Path to the SQLite database
    :param email: User's email
    :param timestamp: Time slot in Unix time (minutes)
    :param donation_type: Type of donation (e.g., "blood", "plasma")
    :param location: Booking location
    :param note: Additional notes (optional)
    :return: Booking success message
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if there are available slots
    cursor.execute("""
        SELECT slots_remaining FROM slots 
        WHERE location = ? AND timestamp = ?
    """, (location, timestamp))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return f"No available slots found at {location} for the given time."

    slots_remaining = result[0]

    if slots_remaining <= 0:
        conn.close()
        return f"No available slots left at {location} for this time."

    # Insert booking record
    success = True
    cursor.execute("""
        INSERT INTO booking (email, timestamp, donation_type, location, success, status, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (email, timestamp, donation_type, location, success, "confirmed", note))

    # Decrease available slots
    cursor.execute("""
        UPDATE slots SET slots_remaining = slots_remaining - 1
        WHERE location = ? AND timestamp = ?
    """, (location, timestamp))

    # Commit changes and close connection
    conn.commit()
    conn.close()

    return f"Booking successful for {email} at {location} on timestamp {timestamp}."



def cancel_booking(db_path, email, timestamp, location):
    """
    Cancels a booking and restores the available slot.

    :param db_path: Path to the SQLite database
    :param email: User's email
    :param timestamp: Time slot in Unix time (minutes)
    :param location: Booking location
    :return: Cancellation success or failure message
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if booking exists
    cursor.execute("""
        SELECT id FROM booking 
        WHERE email = ? AND timestamp = ? AND location = ? AND success = 1
    """, (email, timestamp, location))
    
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        return f"No active booking found for {email} at {location} on the given timestamp."

    booking_id = booking[0]

    # Mark the booking as canceled
    cursor.execute("""
        UPDATE booking 
        SET success = 0, status = 'canceled', note = 'Canceled by user'
        WHERE id = ?
    """, (booking_id,))

    # Restore the available slot
    cursor.execute("""
        UPDATE slots 
        SET slots_remaining = slots_remaining + 1
        WHERE location = ? AND timestamp = ?
    """, (location, timestamp))

    # Commit changes and close connection
    conn.commit()
    conn.close()

    return f"Booking for {email} at {location} on timestamp {timestamp} has been canceled."



def get_last_past_successful_booking(db_path, email):
    """
    Retrieves the last successful booking (before NOW) for a given user.

    :param db_path: Path to the SQLite database
    :param email: User's email
    :return: Tuple (timestamp, donation_type) or None if no past successful booking exists.
    """
    current_timestamp = int(time.time() // 60)  # Get current time in Unix minutes

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, donation_type 
        FROM booking 
        WHERE email = ? AND success = 1 AND timestamp < ?
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (email, current_timestamp))

    result = cursor.fetchone()
    conn.close()

    return result  # Returns (timestamp, donation_type) or None if no past booking found

def get_next_booking_for_user(db_path, email):
    """
    Retrieves the next upcoming booking for a given user.

    :param db_path: Path to the SQLite database
    :param email: User's email
    :return: Tuple (timestamp, location) or None if no future booking exists.
    """
    current_timestamp = int(time.time() // 60)  # Get current time in Unix minutes

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, location 
        FROM booking 
        WHERE email = ? AND success = 1 AND timestamp > ?
        ORDER BY timestamp ASC 
        LIMIT 1
    """, (email, current_timestamp))

    result = cursor.fetchone()
    conn.close()

    return result  # Returns (timestamp, location) or None if no future booking found
