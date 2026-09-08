import csv
import os
import requests
from datetime import datetime
from typing import Optional, Tuple

# Configuration
# National Weather Service requires a custom User-Agent with your contact info.
HEADERS = {
    'User-Agent': '(MyWeatherDashboard/1.0, contact@example.com)'
}

# Optional: Add your Weather Company API Key here if you have one
TWC_API_KEY = ""

CSV_FILE = "weather_dashboard.csv"

CITIES = [
    {"name": "New York City", "lat": 40.7128, "lon": -74.0060},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Austin", "lat": 30.2672, "lon": -97.7431},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918},
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
    {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Las Vegas", "lat": 36.1699, "lon": -115.1398},
    {"name": "New Orleans", "lat": 29.9511, "lon": -90.0715},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"name": "Washington DC", "lat": 38.9072, "lon": -77.0369},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
    {"name": "Boston", "lat": 42.3601, "lon": -71.0589},
    {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740},
    {"name": "Atlanta", "lat": 33.7490, "lon": -84.3880},
    {"name": "Minneapolis", "lat": 44.9778, "lon": -93.2650},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
    {"name": "San Antonio", "lat": 29.4241, "lon": -98.4936},
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
    {"name": "Oklahoma City", "lat": 35.4676, "lon": -97.5164},
    {"name": "Newark", "lat": 40.7357, "lon": -74.1724},
    {"name": "Trenton", "lat": 40.2171, "lon": -74.7429}
]

def fetch_nws_forecast(lat: float, lon: float) -> Tuple[Optional[float], Optional[float]]:
    """Fetch High Temp and Rain Chance from NWS/NOAA API."""
    try:
        points_url = f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}"
        res = requests.get(points_url, headers=HEADERS, timeout=5)
        if res.status_code != 200:
            return None, None
            
        forecast_url = res.json()['properties']['forecast']
        forecast_res = requests.get(forecast_url, headers=HEADERS, timeout=5)
        periods = forecast_res.json()['properties']['periods']
        
        daytime_period = next((p for p in periods if p['isDaytime']), periods[0])
        high_temp = float(daytime_period['temperature'])
        pop = daytime_period.get('probabilityOfPrecipitation', {}).get('value', 0)
        pop = float(pop) if pop is not None else 0.0
        
        return high_temp, pop
    except Exception:
        return None, None

def fetch_openmeteo_forecast(lat: float, lon: float) -> Tuple[Optional[float], Optional[float]]:
    """Fetch High Temp and Rain Chance from Open-Meteo API."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,precipitation_probability_max&temperature_unit=fahrenheit&timezone=auto"
        res = requests.get(url, timeout=5)
        data = res.json()['daily']
        high_temp = float(data['temperature_2m_max'][0])
        pop = float(data['precipitation_probability_max'][0])
        return high_temp, pop
    except Exception:
        return None, None

def fetch_twc_forecast(lat: float, lon: float, api_key: str) -> Tuple[Optional[float], Optional[float]]:
    """Fetch High Temp and Rain Chance from The Weather Company API (Requires Paid Key)."""
    if not api_key:
        return None, None
    try:
        url = f"https://api.weather.com/v3/wx/forecast/daily/5day?geocode={lat},{lon}&format=json&units=e&apiKey={api_key}"
        res = requests.get(url, timeout=5)
        data = res.json()
        high_temp = float(data['calendarDayTemperatureMax'][0])
        pop = float(data['daypart'][0]['precipChance'][0])
        return high_temp, pop
    except Exception:
        return None, None

def export_to_csv():
    file_exists = os.path.isfile(CSV_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:00:00")
    
    headers = [
        "Timestamp", "City", 
        "NWS High (°F)", "NWS Rain (%)", 
        "Meteo High (°F)", "Meteo Rain (%)", 
        "TWC High (°F)", "TWC Rain (%)", 
        "Average High (°F)", "Average Rain (%)"
    ]
    
    rows = []
    
    for city in CITIES:
        nws_high, nws_pop = fetch_nws_forecast(city['lat'], city['lon'])
        meteo_high, meteo_pop = fetch_openmeteo_forecast(city['lat'], city['lon'])
        twc_high, twc_pop = fetch_twc_forecast(city['lat'], city['lon'], TWC_API_KEY)
        
        # Calculate source-based averages
        highs = [h for h in [nws_high, meteo_high, twc_high] if h is not None]
        pops = [p for p in [nws_pop, meteo_pop, twc_pop] if p is not None]
        
        avg_high = round(sum(highs) / len(highs), 1) if highs else ""
        avg_pop = round(sum(pops) / len(pops), 1) if pops else ""
        
        rows.append([
            timestamp,
            city['name'],
            nws_high if nws_high is not None else "",
            nws_pop if nws_pop is not None else "",
            meteo_high if meteo_high is not None else "",
            meteo_pop if meteo_pop is not None else "",
            twc_high if twc_high is not None else "",
            twc_pop if twc_pop is not None else "",
            avg_high,
            avg_pop
        ])

    # Append to CSV
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerows(rows)

    print(f"[{timestamp}] Successfully exported {len(rows)} cities to {CSV_FILE}")

if __name__ == "__main__":
    export_to_csv()
