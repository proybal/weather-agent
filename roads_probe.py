import re
import requests
from urllib.parse import urljoin

BASE = "https://www.nmroads.com/default.html"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

r = session.get(BASE, timeout=30)
r.raise_for_status()

html = r.text

js_files = sorted(set(re.findall(r'["\']([^"\']+\.js)["\']', html)))

print("JS files found:")
for js in js_files:
    print(" ", js)

print("\nSearching JavaScript files...\n")

patterns = [
    "ajax",
    "api",
    "events",
    "get",
    "post",
    "Event",
    "Traffic",
    "Road",
    "Travel",
    "Camera",
    "Message",
    "Route",
]

for js in js_files:
    url = urljoin(BASE, js)
    print(f"\n===== {url} =====")

    try:
        jr = session.get(url, timeout=30)
        print("Status:", jr.status_code)
        text = jr.text

        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(p.lower() in line.lower() for p in patterns):
                line = line.strip()
                if line:
                    print(f"{line_no}: {line[:300]}")

    except Exception as ex:
        print("ERROR:", ex)