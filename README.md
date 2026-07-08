# KANW Weather Agent

Automated weather briefing generator for KANW New Mexico Music.

The script checks for the scheduled KANW show, builds a New Mexico weather briefing using National Weather Service data, creates both plain-text and HTML email versions, and sends the report by email.

## Features

- Pulls forecast data from weather.gov
- Generates statewide, metro, and city forecasts
- Includes Albuquerque sunrise and sunset
- Sends HTML and plain-text email
- Supports force mode for testing
- Runs on Bluehost VPS
- Deploys automatically from GitHub Actions

## Project Location

VPS path:

```bash
/home/burquebr/weather-agent