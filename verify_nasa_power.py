"""Quick connection check for NASA POWER monthly T2M at Lahore."""
import requests

url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
params = {
    "parameters": "T2M",
    "community": "AG",
    "longitude": "74.3587",
    "latitude": "31.5204",
    "start": "2024",
    "end": "2024",
    "format": "JSON",
}

response = requests.get(url, params=params, timeout=(15, 60))
print("HTTP status:", response.status_code)
response.raise_for_status()
payload = response.json()
values = payload["properties"]["parameter"]["T2M"]
print("Response title:", payload.get("header", {}).get("title", "not supplied"))
print("Number of monthly keys:", len([k for k in values if len(str(k)) == 6]))
print("First entries:", list(values.items())[:3])
