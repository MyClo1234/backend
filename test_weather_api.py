import sys
import os
import asyncio
import aiohttp
import json
from datetime import datetime
from urllib.parse import unquote

# Add project root to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.regions import get_nearest_region

# Configuration matching backend/local.settings.json
API_KEY = "7971bf2e2fe86294900d2dbb67d5406dad1297a2962cef98a6577eed8d69e3ac"
BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"


async def test_weather_api():
    # 1. Setup Request
    today_str = datetime.now().strftime("%Y%m%d")
    now_hour_str = datetime.now().strftime("%H00")

    # Test Location: Seoul City Hall (Lat: 37.5665, Lon: 126.9780)
    test_lat = 37.5665
    test_lon = 126.9780

    region_name, region_data = get_nearest_region(test_lat, test_lon)
    nx = region_data["nx"]
    ny = region_data["ny"]

    print(f"Test Location: Lat={test_lat}, Lon={test_lon}")
    print(f"Nearest Region: {region_name} (NX={nx}, NY={ny})")

    # Decode key as requests/aiohttp often re-encode
    service_key = unquote(API_KEY)

    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "300",
        "dataType": "JSON",
        "base_date": today_str,
        "base_time": "0200",  # 02:00 AM forecast base
        "nx": nx,
        "ny": ny,
    }

    print(f"Requesting to: {BASE_URL}")
    print(f"Params: {params}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(BASE_URL, params=params, timeout=10) as response:
                print(f"Status: {response.status}")

                if response.status != 200:
                    text = await response.text()
                    print(f"Error Response: {text}")
                    return

                data = await response.json()

                # Verify structure
                if "response" not in data or "body" not in data["response"]:
                    print("Invalid Response Structure")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    return

                items = data["response"]["body"]["items"]["item"]
                print(f"Total Items Received: {len(items)}")

                # 2. Parse Logic (Mirroring Service Logic)
                min_val = None
                max_val = None
                max_rain_type = 0
                current_rain_type = None

                print(f"Target Time for Current Rain Type: {now_hour_str}")

                for item in items:
                    cat = item["category"]
                    val = item["fcstValue"]
                    fcst_time = item["fcstTime"]

                    if cat == "TMN":
                        min_val = float(val)
                    elif cat == "TMX":
                        max_val = float(val)
                    elif cat == "PTY":
                        rain_val = int(val)
                        if rain_val > max_rain_type:
                            max_rain_type = rain_val

                        if fcst_time == now_hour_str:
                            current_rain_type = rain_val
                            print(f"Found Current PTY at {fcst_time}: {rain_val}")

                print("\n" + "=" * 30)
                print(f"Parsed Result:")
                print(f"Min Temp: {min_val}")
                print(f"Max Temp: {max_val}")
                print(f"Current Rain Type (PTY): {current_rain_type}")
                print("=" * 30 + "\n")

        except Exception as e:
            print(f"Exception: {e}")


if __name__ == "__main__":
    asyncio.run(test_weather_api())
