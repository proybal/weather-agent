# 🌦️ KANW Weather Agent

An automated weather briefing generator for **KANW 89.1 FM New Mexico**.

The Weather Agent collects current forecast information from the National Weather Service, generates a professional radio-ready weather briefing for New Mexico, and emails both HTML and plain-text versions to the host before each scheduled broadcast.

---

## Features

- 🌤 Retrieves live weather data from the National Weather Service (weather.gov)
- 🗺 Generates:
  - Albuquerque Metro forecast
  - Statewide weather summary
  - City-by-city forecasts
- 🌅 Includes Albuquerque sunrise and sunset times
- 📊 Displays metro temperature table
- 📧 Sends both HTML and plain-text email versions
- 🎙 Formats output specifically for on-air radio delivery
- 🧪 Supports **Force Mode** for testing without a calendar event
- 📅 Can be triggered automatically from a calendar schedule
- 🖥 Runs on a Bluehost VPS under Python virtual environment
- 🚀 Automatically deploys from GitHub using GitHub Actions

---

## Technologies

- Python 3.9+
- National Weather Service API
- Requests
- BeautifulSoup
- Python Dotenv
- Yahoo SMTP
- GitHub Actions
- Linux (AlmaLinux)
- Virtual Environment (venv)

---

## Project Structure

```
weather-agent/
│
├── weather.py              # Main application
├── email_utils.py          # Email generation and delivery
├── nws.py                  # National Weather Service functions
├── calendar.py             # Calendar trigger
├── requirements.txt
├── .env
└── README.md
```

---

## Project Location

### Bluehost VPS

```text
/home/burquebr/weather-agent
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/burquebr/weather-agent.git
cd weather-agent
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file containing:

```env
SMTP_SERVER=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_TO=
```

Additional API keys or configuration values can also be stored in `.env`.

---

## Running

Normal operation:

```bash
python weather.py
```

Force Mode (ignores calendar trigger):

```bash
python weather.py --force
```

---

## Sample Output

The generated briefing includes:

- Metro Forecast
- Metro Temperatures
- Statewide Forecast
- City Forecasts
- Sunrise & Sunset
- Professional radio sign-off

Both HTML and plain-text versions are generated and emailed automatically.

---

## Deployment

Deployment is fully automated through **GitHub Actions**.

Each push to the **main** branch:

1. Connects to the Bluehost VPS
2. Updates the repository
3. Activates the virtual environment
4. Installs updated dependencies
5. Performs application checks
6. Restarts the service

---

## Future Enhancements

- Road and traffic conditions
- Air quality alerts
- Fire weather warnings
- NWS watches and warnings
- Weather graphics generation
- Audio briefing generation using text-to-speech
- AI-generated conversational weather summaries

---

## License

Personal project created for volunteer use with **KANW 89.1 FM New Mexico Music**.

Weather data provided by the **National Weather Service (NOAA)**.