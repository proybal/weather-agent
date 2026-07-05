import os
from dotenv import load_dotenv
import caldav

load_dotenv()

email = os.getenv("YAHOO_EMAIL")
username = os.getenv("YAHOO_USERNAME")
password = (os.getenv("YAHOO_APP_PASSWORD") or "").replace(" ", "")

urls = [
    "https://caldav.calendar.yahoo.com",
    f"https://caldav.calendar.yahoo.com/dav/{username}/",
    f"https://caldav.calendar.yahoo.com/dav/{username}/Calendar/",
]

users = [
    email,
    username,
]

for url in urls:
    for user in users:
        print("=" * 70)
        print("URL:", url)
        print("USER:", user)

        try:
            client = caldav.DAVClient(
                url=url,
                username=user,
                password=password,
            )

            principal = client.principal()
            calendars = principal.calendars()

            print("SUCCESS")
            print("Calendars found:", len(calendars))

            for cal in calendars:
                try:
                    print("-", cal.name)
                except Exception:
                    print("-", cal.url)

            raise SystemExit

        except Exception as e:
            print("FAILED:", type(e).__name__, repr(e))
