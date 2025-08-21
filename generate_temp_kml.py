import requests
from datetime import datetime
import os

# Step 1: Get the latest valid 3-hour UTC forecast time
def get_latest_forecast_time():
    now_utc = datetime.utcnow()
    rounded_hour = (now_utc.hour // 3) * 3
    forecast_time = now_utc.replace(hour=rounded_hour, minute=0, second=0, microsecond=0)
    return forecast_time.strftime('%Y-%m-%dT%H:%M:%SZ')

# Step 2: Build the NOAA export URL using the forecast time
def build_noaa_url(forecast_time):
    base_url = "https://mapservices.weather.noaa.gov/raster/rest/services/NDFD/NDFD_temp/MapServer/export"
    params = {
        "bbox": "-130,20,-60,55",
        "size": "1024,768",
        "format": "png",
        "f": "image",
        "layers": "show:0",
        "imageSR": "4326",
        "bboxSR": "4326",
        "transparent": "true",
        "showLabels": "false",
        "time": forecast_time
    }
    return f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

# Step 3: Download the image and save it
def download_image(url, filename="forecast.png"):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ Image saved as {filename}")
    else:
        print(f"❌ Failed to fetch image. Status code: {response.status_code}")
        print(f"URL attempted: {url}")

# Step 4: Main execution
def main():
    forecast_time = get_latest_forecast_time()
    print(f"🕒 Using forecast time: {forecast_time}")
    url = build_noaa_url(forecast_time)
    print(f"🔗 NOAA URL: {url}")
    download_image(url)

if __name__ == "__main__":
    main()
