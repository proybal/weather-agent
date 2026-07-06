import os
import re
import html
import smtplib
import requests
import argparse
import random
from email.message import EmailMessage
from datetime import datetime
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import sun
from dateutil.parser import parse as parse_date
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def make_session():
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "REPORT"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

CLOSINGS = [
    "Enjoy the music on KANW, and have a wonderful day.",
    "Stay safe, stay informed, and enjoy New Mexico Music on KANW.",
    "Wherever your travels take you across New Mexico, have a great day with KANW.",
    "Thanks for listening to KANW—your home for New Mexico Music.",
    "Have a safe day, and thank you for making KANW part of it.",
    "From all of us at KANW, enjoy today's forecast and the music ahead.",
    "Here's wishing you clear skies and great New Mexico Music on KANW.",
    "Until next time, enjoy the weather and keep it tuned to KANW.",
]

SESSION = make_session()
load_dotenv()

TZ = ZoneInfo("America/Denver")
STATE_FILE = "state.txt"
CACHE = {}

LOCATIONS = {
    "Albuquerque": (35.0844, -106.6504),
    "Santa Fe": (35.6870, -105.9378),
    "Grants": (35.1473, -107.8514),
    "Gallup": (35.5281, -108.7426),
    "Las Vegas": (35.5942, -105.2228),
    "Santa Rosa": (34.9387, -104.6825),
}

METRO_AREAS = {
    "Valley": (35.1030, -106.6700),
    "Heights": (35.1100, -106.5300),
}

HEADERS = {
    "User-Agent": "burquebro-weather-agent, proybal@yahoo.com",
    "Accept": "application/geo+json",
}


def get_json(url):
    if url in CACHE:
        return CACHE[url]

    r = SESSION.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    CACHE[url] = data
    return data


def get_forecast_urls(lat, lon):
    key = f"points:{lat},{lon}"

    if key in CACHE:
        return CACHE[key]

    point = get_json(f"https://api.weather.gov/points/{lat},{lon}")
    props = point["properties"]
    result = props["forecast"], props["forecastHourly"]
    CACHE[key] = result
    return result


def get_forecast_periods(lat, lon):
    forecast_url, _ = get_forecast_urls(lat, lon)
    forecast = get_json(forecast_url)
    return forecast["properties"]["periods"]


def get_current_temp(lat, lon):
    _, hourly_url = get_forecast_urls(lat, lon)
    hourly = get_json(hourly_url)
    period = hourly["properties"]["periods"][0]
    return period.get("temperature")


def pick_city_period(periods):
    now = datetime.now(TZ)
    want_daytime = now.hour < 15

    for p in periods:
        if p.get("isDaytime") == want_daytime:
            return p

    return periods[0]


def get_nm_alerts():
    try:
        alerts = get_json("https://api.weather.gov/alerts/active?area=NM")
        features = alerts.get("features", [])

        if not features:
            return []

        return [f["properties"]["headline"] for f in features]

    except Exception:
        return []


def clean_afd_text(text):
    text = text or ""

    text = re.sub(r"\$\$", "", text)
    text = re.sub(r"&&", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def get_latest_afd_text():
    products = get_json("https://api.weather.gov/products/types/AFD/locations/ABQ")

    graph = products.get("@graph", [])
    if not graph:
        raise RuntimeError("No AFD products found")

    latest_id = graph[0]["id"]
    product = get_json(f"https://api.weather.gov/products/{latest_id}")
    text = product.get("productText", "")

    match = re.search(
        r"\.SYNOPSIS\.\.\.\s*(.*?)(?=\n\.[A-Z]|\n&&|\Z)",
        text,
        re.DOTALL,
    )

    if not match:
        match = re.search(
            r"\.DISCUSSION\.\.\.\s*(.*?)(?=\n\.[A-Z]|\n&&|\Z)",
            text,
            re.DOTALL,
        )

    if match:
        summary = match.group(1).strip()
    else:
        summary = text[:1800].strip()

    summary = clean_afd_text(summary)

    sentences = re.split(r"(?<=[.!?])\s+", summary)

    skip_words = [
        "aviation",
        "taf",
        "zulu",
        "hrrr",
        "nam",
        "gfs",
        "ecmwf",
        "pwat",
        "h5",
        "h7",
        "700mb",
        "500mb",
        "model",
        "guidance",
        "forecast package",
    ]

    good = []

    for sentence in sentences:
        s = sentence.strip()
        low = s.lower()

        if len(s) < 30:
            continue

        if any(word in low for word in skip_words):
            continue

        good.append(s)

        if len(good) >= 4:
            break

    if not good:
        raise RuntimeError("No usable AFD sentences found")

    return " ".join(good)


def get_statewide_forecast():
    try:
        products = get_json(
            "https://api.weather.gov/products/types/AFD/locations/ABQ"
        )

        latest_id = products["@graph"][0]["id"]
        product = get_json(f"https://api.weather.gov/products/{latest_id}")
        text = product["productText"]

        # Remove the NWS header
        updated = re.search(r"Updated at.*?\n", text, re.DOTALL)
        if updated:
            text = text[updated.end():]

        # Capture wrapped key-message bullet blocks
        bullet_blocks = re.findall(
            r"^\s*-\s+(.*?)(?=\n\s*-\s+|\n&&|\n\.[A-Z]|\Z)",
            text,
            re.MULTILINE | re.DOTALL
        )

        messages = []

        for b in bullet_blocks[:4]:
            b = re.sub(r"\s+", " ", b).strip()
            b = b.replace(" NM", " New Mexico")
            b = b.replace("NM.", "New Mexico.")
            b = b.replace("east central", "east-central")
            messages.append(b)

        if messages:
            forecast = " ".join(messages)
        else:
            forecast = (
                "Weather conditions will vary across New Mexico today. "
                "See the local forecasts below for additional details."
            )

        alerts = get_nm_alerts()

        if alerts:
            forecast += " Weather Alert: " + alerts[0]

        return "STATEWIDE FORECAST\n\n" + forecast

    except Exception as ex:
        print(f"Statewide forecast error: {ex}")
        return (
            "STATEWIDE FORECAST\n\n"
            "Weather conditions will vary across New Mexico today."
        )


def get_metro_forecast():
    periods = get_forecast_periods(35.0844, -106.6504)

    lines = ["METRO FORECAST", ""]

    for period in periods[:3]:
        name = period["name"]
        temp_label = "High" if period["isDaytime"] else "Low"
        temp = period["temperature"]
        wind = f"{period['windDirection']} {period['windSpeed']}"
        rain = period.get("probabilityOfPrecipitation", {}).get("value")

        rain_text = ""
        if rain is not None and rain > 0:
            rain_text = f" Chance of precipitation {rain}%."

        lines.append(
            f"{name}: {period['shortForecast']}. "
            f"{temp_label} {temp}°. "
            f"Wind {wind}.{rain_text}"
        )

    lines.append("")
    lines.append("METRO TEMPERATURES")
    lines.append("")
    lines.append(f"{'Area':<10} {'High/Low':>10} {'Current':>10}  Forecast")
    lines.append("-" * 55)

    for area, (lat, lon) in METRO_AREAS.items():
        selected = pick_city_period(get_forecast_periods(lat, lon))
        current = get_current_temp(lat, lon)

        lines.append(
            f"{area:<10}"
            f"{str(selected['temperature']) + '°':>10}"
            f"{str(current) + '°':>10}  "
            f"{selected['shortForecast']}"
        )

    return "\n".join(lines)

def get_sunrise_sunset():
    city = LocationInfo(
        "Albuquerque",
        "New Mexico",
        "America/Denver",
        35.0844,
        -106.6504,
    )

    s = sun(city.observer, date=datetime.now(TZ).date(), tzinfo=TZ)
    sunrise = s["sunrise"].strftime("%-I:%M %p")
    sunset = s["sunset"].strftime("%-I:%M %p")

    return f"Sunrise in Albuquerque is {sunrise}. Sunset is {sunset}."

def get_city_table():
    now = datetime.now(TZ)
    label = "High" if now.hour < 15 else "Low"

    lines = [
        "CITY FORECAST",
        "",
        f"{'City':<14} {'Current':>8} {label:>8}  Forecast",
        "-" * 52,
    ]

    for city, (lat, lon) in LOCATIONS.items():
        p = pick_city_period(get_forecast_periods(lat, lon))
        current = get_current_temp(lat, lon)

        lines.append(
            f"{city:<14} "
            f"{str(current) + '°':>8} "
            f"{str(p.get('temperature')) + '°':>8}  "
            f"{p.get('shortForecast', '')}"
        )

    return "\n".join(lines)

def get_closing():
    return random.choice(CLOSINGS)

def build_weather_email(statewide, metro, city_table, sun, closing):

    return f"""{statewide}

{metro}

{city_table}

SUNRISE / SUNSET

{sun}

{closing}
"""


def build_metro_rows_html():
    rows = ""

    for area, (lat, lon) in METRO_AREAS.items():
        current = get_current_temp(lat, lon)
        p = pick_city_period(get_forecast_periods(lat, lon))

        rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #ddd;">{area}</td>
            <td style="padding:8px;text-align:center;border-bottom:1px solid #ddd;font-weight:bold;">{p.get('temperature')}°</td>
            <td style="padding:8px;text-align:center;border-bottom:1px solid #ddd;font-weight:bold;">{current}°</td>
            <td style="padding:8px;border-bottom:1px solid #ddd;">{p.get('shortForecast', '')}</td>
        </tr>
        """

    return rows


def build_city_rows_html():
    rows = ""

    for city, (lat, lon) in LOCATIONS.items():
        current = get_current_temp(lat, lon)
        p = pick_city_period(get_forecast_periods(lat, lon))

        rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #ddd;">{city}</td>
            <td style="padding:8px;text-align:center;border-bottom:1px solid #ddd;font-weight:bold;">{current}°</td>
            <td style="padding:8px;text-align:center;border-bottom:1px solid #ddd;font-weight:bold;">{p.get('temperature')}°</td>
            <td style="padding:8px;border-bottom:1px solid #ddd;">{p.get('shortForecast', '')}</td>
        </tr>
        """

    return rows


def build_weather_email_html(statewide, metro, sun, closing):

    statewide_html = statewide.replace("STATEWIDE FORECAST", "").strip()
    closing_html = closing.replace("\n", "<br>")

    metro_html = ""
    current_period = None

    for line in metro.splitlines():
        line = line.strip()

        if not line:
            continue

        if line in ["Today", "Tonight", "Tomorrow", "Tomorrow Night"]:
            current_period = line
            metro_html += f"<h3 style='color:#333;margin-top:16px;'>{line}</h3>"
            continue

        if line.startswith("METRO"):
            continue

        if line.startswith("High:") or line.startswith("Low:"):
            metro_html += f"<p><strong>{line}</strong></p>"
        elif line.startswith("Wind:") or line.startswith("Humidity:") or line.startswith("Chance of precipitation:"):
            label, text = line.split(":", 1)
            metro_html += f"<p><strong>{label}:</strong> {text.strip()}</p>"
        elif not line.startswith("Area") and not line.startswith("-") and not line.startswith("Valley") and not line.startswith("Heights"):
            metro_html += f"<p>{line}</p>"

    return f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif;color:#222;">
<div style="max-width:760px;margin:0 auto;background:#fff;padding:24px;">

<div style="border-bottom:4px solid #1f5f99;padding-bottom:12px;margin-bottom:22px;">
<h1 style="margin:0;color:#1f5f99;">KANW New Mexico Weather</h1>
<p style="margin-top:6px;color:#666;">
Automated weather briefing for New Mexico Music
</p>
</div>

<h2 style="color:#1f5f99;">Statewide Forecast</h2>

<p>{statewide_html}</p>

<h2 style="color:#1f5f99;">Metro Forecast</h2>

{metro_html}

<h3>Metro Temperatures</h3>

<table style="width:100%;border-collapse:collapse;">
<thead>
<tr style="background:#1f5f99;color:white;">
<th>Area</th>
<th>High/Low</th>
<th>Current</th>
<th>Forecast</th>
</tr>
</thead>

<tbody>

{build_metro_rows_html()}

</tbody>

</table>

<h2 style="color:#1f5f99;">City Forecast</h2>

<table style="width:100%;border-collapse:collapse;">
<thead>
<tr style="background:#1f5f99;color:white;">
<th>City</th>
<th>Current</th>
<th>High/Low</th>
<th>Forecast</th>
</tr>
</thead>

<tbody>

{build_city_rows_html()}

</tbody>

</table>

<h2 style="color:#1f5f99;">Sunrise / Sunset</h2>

<p>{sun}</p>

<p style="margin-top:25px;border-top:1px solid #ccc;padding-top:15px;">
{closing_html}
</p>

</div>
</body>
</html>
"""


def send_email(subject, text_body, html_body=None):
    msg = EmailMessage()
    msg["From"] = os.getenv("FROM_EMAIL", "").strip()
    msg["To"] = os.getenv("TO_EMAIL", "").strip()
    msg["Subject"] = subject

    msg.set_content(text_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    user = os.getenv("FROM_EMAIL", "").strip()
    password = os.getenv("APP_PASSWORD", "").replace(" ", "").strip()

    with smtplib.SMTP(
        os.getenv("SMTP_SERVER"),
        int(os.getenv("SMTP_PORT", "587")),
    ) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)


def already_triggered(uid):
    if not os.path.exists(STATE_FILE):
        return False

    with open(STATE_FILE, "r") as f:
        return uid in f.read()


def mark_triggered(uid):
    with open(STATE_FILE, "a") as f:
        f.write(uid + "\n")


def should_trigger():
    yahoo_email = os.getenv("YAHOO_EMAIL")
    yahoo_password = os.getenv("YAHOO_APP_PASSWORD", "").replace(" ", "")

    now = datetime.now(TZ)

    url = "https://caldav.calendar.yahoo.com/dav/proybal/Calendar/131/"

    body = """<?xml version="1.0" encoding="utf-8" ?>
<C:calendar-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <C:calendar-data/>
  </D:prop>
  <C:filter>
    <C:comp-filter name="VCALENDAR">
      <C:comp-filter name="VEVENT"/>
    </C:comp-filter>
  </C:filter>
</C:calendar-query>"""

    r = SESSION.request(
        "REPORT",
        url,
        auth=(yahoo_email, yahoo_password),
        headers={
            "Depth": "1",
            "Content-Type": "application/xml",
        },
        data=body,
        timeout=15,
    )

    r.raise_for_status()

    text = html.unescape(r.text)

    events = re.findall(
        r"BEGIN:VEVENT(.*?)END:VEVENT",
        text,
        re.DOTALL,
    )

    for event in events:
        summary_match = re.search(r"^SUMMARY:(.*)$", event, re.MULTILINE)
        dtstart_match = re.search(r"^DTSTART(?:;[^:]+)?:(.*)$", event, re.MULTILINE)
        dtend_match = re.search(r"^DTEND(?:;[^:]+)?:(.*)$", event, re.MULTILINE)
        uid_match = re.search(r"^UID:(.*)$", event, re.MULTILINE)

        if not summary_match or not dtstart_match or not dtend_match:
            continue

        title = summary_match.group(1).strip().lower()

        if title not in [
            "kanw nm music",
            "kanw nm msic",
        ]:
            continue

        dtstart_raw = dtstart_match.group(1).strip()
        dtend_raw = dtend_match.group(1).strip()

        start = parse_date(dtstart_raw)
        end = parse_date(dtend_raw)

        if start.tzinfo is None:
            start = start.replace(tzinfo=TZ)
        else:
            start = start.astimezone(TZ)

        if end.tzinfo is None:
            end = end.replace(tzinfo=TZ)
        else:
            end = end.astimezone(TZ)

        if not (start <= now < end):
            continue

        if now.minute > 5:
            continue

        uid = (
            uid_match.group(1).strip()
            if uid_match
            else f"{title}-{dtstart_raw}"
        )

        hour_key = now.strftime("%Y-%m-%d-%H")
        state_key = f"{uid}|{hour_key}"

        if already_triggered(state_key):
            continue

        mark_triggered(state_key)

        print(f"Matched active event: {title} ({start} - {end})")

        return True

    return False


def main():
    parser = argparse.ArgumentParser(description="KANW weather email agent")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run immediately without checking Yahoo Calendar.",
    )
    args = parser.parse_args()

    if not args.force:
        if not should_trigger():
            return
    else:
        print("Force mode: skipping Yahoo Calendar trigger.\n")

    statewide = get_statewide_forecast()
    metro = get_metro_forecast()
    city_table = get_city_table()
    sun = get_sunrise_sunset()
    closing = get_closing()

    text_message = build_weather_email(
        statewide,
        metro,
        city_table,
        sun,
        closing,
    )

    html_message = build_weather_email_html(
        statewide,
        metro,
        sun,
        closing,
    )
    if args.force:
        print("==== WEATHER EMAIL (TEXT) ====\n")
        print(text_message)
        print("\n==============================\n")

        with open("/tmp/weather_preview.html", "w", encoding="utf-8") as f:
            f.write(html_message)

        print("HTML preview written to /tmp/weather_preview.html\n")

    send_email(
        "KANW NM Music Weather",
        text_message,
        html_message,
    )

    if args.force:
        print("Weather email sent.")


if __name__ == "__main__":
    main()