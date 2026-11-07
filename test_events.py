import sqlite3
from database import (
    initialize_database,
    save_event,
    get_recent_events
)


try:
    initialize_database()

    save_event(
        event_type="TEST",
        message="Sample event: EcoPC event logging works."
    )

    latest_event = get_recent_events(limit=1)[0]

    print(f"Time: {latest_event['timestamp']}")
    print(f"Type: {latest_event['event_type']}")
    print(f"Message: {latest_event['message']}")

except sqlite3.Error as error:
    print(f"Event logging test failed: {error}")
    raise SystemExit(1)