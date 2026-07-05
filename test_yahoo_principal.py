import os
from dotenv import load_dotenv
import caldav

load_dotenv()

client = caldav.DAVClient(
    url="https://caldav.calendar.yahoo.com/principals/users/proybal/",
    username=os.getenv("YAHOO_EMAIL"),
    password=(os.getenv("YAHOO_APP_PASSWORD") or "").replace(" ", ""),
)

principal = client.principal()
calendars = principal.calendars()

print("Calendars:", len(calendars))
for cal in calendars:
    print("-", getattr(cal, "name", cal.url))
