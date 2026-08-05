# flight_tool.py
# Duffel Flight Search API (test mode)
# https://duffel.com/docs/api
# pip install requests python-dotenv

import os
import requests
from dotenv import load_dotenv

load_dotenv()

DUFFEL_API_KEY = os.getenv("DUFFEL_API_KEY")
DUFFEL_BASE_URL = "https://api.duffel.com"

HEADERS = {
    "Authorization": f"Bearer {DUFFEL_API_KEY}",
    "Duffel-Version": "v2",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def search_flights(dep_iata, arr_iata, travel_date=None):
    """
    Search real flight offers between dep_iata and arr_iata on travel_date
    (format: YYYY-MM-DD) using the Duffel API (test mode).

    Returns a formatted string with the top flight options, including price.
    """
    print(f"[DEBUG] search_flights called with dep={dep_iata}, arr={arr_iata}, date={travel_date}")
    print(f"[DEBUG] API key loaded: {'YES' if DUFFEL_API_KEY else 'NO - key is missing!'}")

    if not DUFFEL_API_KEY:
        return "Duffel API key not configured. Please set DUFFEL_API_KEY in .env"

    if not travel_date:
        from datetime import datetime, timedelta
        travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    payload = {
        "data": {
            "slices": [
                {
                    "origin": dep_iata,
                    "destination": arr_iata,
                    "departure_date": travel_date,
                }
            ],
            "passengers": [{"type": "adult"}],
            "cabin_class": "economy",
        }
    }

    try:
        response = requests.post(
            f"{DUFFEL_BASE_URL}/air/offer_requests?return_offers=true",
            json=payload,
            headers=HEADERS,
            timeout=20,
        )
        print(f"[DEBUG] Duffel HTTP status: {response.status_code}")
        print(f"[DEBUG] Duffel raw response (first 500 chars): {response.text[:500]}")
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get("errors", [{}])[0].get("message", str(e))
        except Exception:
            error_detail = str(e)
        print(f"[DEBUG] HTTPError: {error_detail}")
        return f"Flight search failed: {error_detail}"
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        return f"Flight search failed: {e}"

    offers = data.get("data", {}).get("offers", [])
    print(f"[DEBUG] Offers found: {len(offers)}")

    if not offers:
        return f"No flights found from {dep_iata} to {arr_iata} on {travel_date}."

    offers = sorted(offers, key=lambda o: float(o.get("total_amount", "999999")))[:5]

    flights = []
    for offer in offers:
        try:
            slice_ = offer["slices"][0]
            segment = slice_["segments"][0]
            airline = segment["operating_carrier"]["name"]
            flight_number = f"{segment['operating_carrier']['iata_code']}{segment['operating_carrier_flight_number']}"

            dep_time = segment["departing_at"][11:16]
            arr_time = segment["arriving_at"][11:16]

            stops = len(slice_["segments"]) - 1
            stops_label = "Nonstop" if stops == 0 else f"{stops} stop(s)"

            price = offer.get("total_amount", "N/A")
            currency = offer.get("total_currency", "")

            flights.append(
                f"""
Airline: {airline} ({flight_number})
Departure: {dep_iata} at {dep_time}
Arrival: {arr_iata} at {arr_time}
Stops: {stops_label}
Price: {currency} {price}
"""
            )
        except (KeyError, IndexError):
            continue

    if not flights:
        return f"No usable flight data found from {dep_iata} to {arr_iata} on {travel_date}."

    return "\n".join(flights)


if __name__ == "__main__":
    result = search_flights("DEL", "BOM", "2026-08-15")
    print(result)