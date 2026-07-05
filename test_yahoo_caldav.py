import os
from dotenv import load_dotenv
import caldav

load_dotenv()

for username in [
    os.getenv("YAHOO_EMAIL"),
    os.getenv("YAHOO_USERNAME"),
]:
    print("Trying:", username)

    try:
        client = caldav.DAVClient(
            url="https://caldav.calendar.yahoo.com",
            username=username,
            password=os.getenv("YAHOO_APP_PASSWORD"),
        )

        principal = client.principal()
        calendars = principal.calendars()

        print("SUCCESS")
        for cal in calendars:
            print("-", cal.name)
        break

    except Exception as e:
        print("FAILED:", repr(e))
