#!/usr/bin/env python3
import requests
from datetime import datetime
import urllib.parse, json

# Geographic extents (CONUS)
MIN_LON, MAX_LON = -130.0, -60.0
MIN_LAT, MAX_LAT =  20.0,  55.0

# Desired image width in pixels
IMG_WIDTH = 1024

# Filenames & URLs
PNG_FILENAME = "forecast.png"
KML_FILENAME = "temperature-overlay.kml"
PNG_URL_BASE = "https://mapservices.weather.noaa.gov/raster/rest/services/NDFD/NDFD_temp/MapServer/export"

# Step 1: calculate height to match real-world aspect ratio
hor_span = abs(MAX_LON - MIN_LON)    # 70 degrees
ver_span =     MAX_LAT - MIN_LAT    # 35 degrees
IMG_HEIGHT = round(IMG_WIDTH * (ver_span / hor_span))  # 512 px

# Step 2: round down to the nearest valid 3-hr forecast cycle
def get_forecast_time():
    now = datetime.utcnow()
    h3  = (now.hour // 3) * 3
    ft  = now.replace(hour=h3, minute=0, second=0, microsecond=0)
    return ft.strftime("%Y-%m-%dT%H:%M:%SZ")

# Step 3: build the NOAA export URL
def build_noaa_url(forecast_time):
        dynamic = [{
        "id": 0,
        "source": {
            "type": "mapLayer",
            "mapLayerId": 0
        },
        "drawingInfo": {
            "renderer": {
                "type": "rasterStretch",
                "stretchType": "min-max"
            }
        }
    }]
    params = {
        "bbox":    f"{MIN_LON},{MIN_LAT},{MAX_LON},{MAX_LAT}",
        "size":    f"{IMG_WIDTH},{IMG_HEIGHT}",
        "format":  "png",
        "f":       "image",
        "layers":  "show:0",
        "imageSR": "4326",
        "bboxSR":  "4326",
        "transparent": "true",
        "disableLabels":  "true",
        "time":    forecast_time
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{PNG_URL_BASE}?{query}"

# Step 4: download the image
def download_image(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        with open(PNG_FILENAME, "wb") as f:
            f.write(resp.content)
        print(f"[✓] Saved {PNG_FILENAME} ({IMG_WIDTH}×{IMG_HEIGHT}px)")
    else:
        print(f"[✗] Image fetch failed: HTTP {resp.status_code}")

# Step 5: build the KML overlay
def build_kml():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>NOAA CONUS Temperature</name>
    <GroundOverlay>
      <name>Temperature Raster</name>
      <Icon>
        <href>https://jeandeauxmail-cell.github.io/temperaturetest/{PNG_FILENAME}</href>
      </Icon>
      <LatLonBox>
        <north>{MAX_LAT}</north>
        <south>{MIN_LAT}</south>
        <east>{MAX_LON}</east>
        <west>{MIN_LON}</west>
      </LatLonBox>
    </GroundOverlay>
  </Document>
</kml>
"""

# Step 6: save the KML
def save_kml(kml):
    with open(KML_FILENAME, "w", encoding="utf-8") as f:
        f.write(kml)
    print(f"[✓] Saved {KML_FILENAME}")

# Main
def main():
    ft = get_forecast_time()
    print(f"⏱ Forecast time: {ft}")
    url = build_noaa_url(ft)
    print(f"🔗 Fetch URL: {url}")
    download_image(url)
    save_kml(build_kml())

if __name__ == "__main__":
    main()
