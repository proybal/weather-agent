import requests

url = "https://nmroads.com/"

r = requests.get(url, timeout=30)

print("Status:", r.status_code)
print()
print(r.text[:10000])