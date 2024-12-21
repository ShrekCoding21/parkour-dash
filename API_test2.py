import pyodide.http
import json

# Load weather codes from JSON file (you can save this in Pyodide FS if needed)
async def load_weather_codes():
    weather_codes = {
        "weather-codes": {
            "Clear": [0, 1],
            "Cloudy": [2, 3],
            "Rainy": [45, 48],
        }
    }
    return weather_codes

# Fetch coordinates for a city
async def get_coordinates(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    headers = {"User-Agent": "YourAppName/1.0 (your_email@example.com)"}

    try:
        response = await pyodide.http.pyfetch(url, method="GET", params=params, headers=headers)
        data = await response.json()

        if not data:
            raise ValueError("City not found. Please check the input.")
        
        location = data[0]
        return float(location['lat']), float(location['lon'])
    except Exception as e:
        raise ValueError(f"Request Error: {e}")

# Fetch weather data for given coordinates
async def fetch_weather_data(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "is_day",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "America/New_York",
    }
    try:
        response = await pyodide.http.pyfetch(url, method="GET", params=params)
        data = await response.json()
        return data
    except Exception as e:
        raise ValueError(f"Request Error: {e}")

# Process weather data
async def process_weather(data, weather_conditions):
    current = data["current_weather"]
    weather_code = current.get("weathercode")
    temperature = current.get("temperature")
    windspeed = current.get("windspeed")
    condition = "Unknown"

    for cond, codes in weather_conditions["weather-codes"].items():
        if weather_code in codes:
            condition = cond
            break

    return {
        "weather_code": weather_code,
        "temperature": temperature,
        "windspeed": windspeed,
        "weather_condition": condition
    }

# Main function to fetch and process weather data
async def main():
    city = "Atlanta"  # Replace with desired city
    try:
        # Load weather codes
        weather_conditions = await load_weather_codes()

        # Get coordinates
        latitude, longitude = await get_coordinates(city)
        print(f"Coordinates for {city}: Latitude {latitude}, Longitude {longitude}")

        # Get weather data
        weather_data = await fetch_weather_data(latitude, longitude)
        
        # Process weather data
        current_weather = await process_weather(weather_data, weather_conditions)
        
        print(f"Weather Code: {current_weather['weather_code']}")
        print(f"Temperature: {current_weather['temperature']} °F")
        print(f"Wind Speed: {current_weather['windspeed']} mph")
        print(f"Weather Condition: {current_weather['weather_condition']}")

        return current_weather
    except ValueError as e:
        print(e)
        return None

# Example of calling the main function
import asyncio
asyncio.run(main())
