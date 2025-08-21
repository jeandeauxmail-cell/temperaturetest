import requests
from datetime import datetime
import os

# Constants
PNG_FILENAME = "forecast.png"
KML_FILENAME = "temperature-overlay.kml"
PNG_URL = "https://jeandeauxmail-cell.github.io/temperaturetest/forecast.png"  # Update if repo or filename changes

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
def download_image(url, filename=PNG_FILENAME):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ Image saved as {filename}")
    else:
        print(f"❌ Failed to fetch image. Status code: {response.status_code}")
        print(f"URL attempted: {url}")

# Step 4: Build the KML content
def build_kml(png_url=PNG_URL):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>NOAA Temperature Raster</name>
    <GroundOverlay>
      <name>CONUS Temperature</name>
      <Icon>
        <href>{png_url}</href>
      </Icon>
      <LatLonBox>
        <north>55.0</north>
        <south>20.0</south>
        <east>-60.0</east>
        <west>-130.0</west>
      </LatLonBox>
    </GroundOverlay>
  </Document>
</kml>
"""

# Step 5: Save the KML file
def save_kml(content, filename=KML_FILENAME):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ KML saved as {filename}")

# Step 6: Main execution
def main():
    forecast_time = get_latest_forecast_time()
    print(f"🕒 Using forecast time: {forecast_time}")
    url = build_noaa_url(forecast_time)
    print(f"🔗 NOAA URL: {url}")
    download_image(url)
    kml_content = build_kml()
    save_kml(kml_content)

if __name__ == "__main__":
    main()
