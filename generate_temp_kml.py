#!/usr/bin/env python3
import requests
from datetime import datetime
from pathlib import Path

# 1. Configuration
MIN_LON, MAX_LON = -130.0, -60.0
MIN_LAT, MAX_LAT =   20.0,   55.0
IMG_WIDTH  = 1024
IMG_HEIGHT = 512  # Maintains 2:1 aspect ratio for 70°×35°
PNG_FILENAME = "forecast.png"
KML_FILENAME = "temperature-overlay.kml"

# Base WMS endpoint for NOAA NDFD temperature
WMS_BASE = (
    "https://mapservices.weather.noaa.gov/raster/rest/services/"
    "NDFD/NDFD_temp/MapServer/WmsServer"
)

# 2. Determine latest 3-hourly cycle timestamp (UTC)
def get_latest_cycle_iso():
    now = datetime.utcnow()
    cycle_hour = (now.hour // 3) * 3
    cycle = now.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)
    return cycle.strftime("%Y-%m-%dT%H:%M:%SZ")

# 3. Build WMS GetMap URL
def build_wms_url(time_iso):
    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "VERSION": "1.3.0",
        "LAYERS": "0",           # temperature grid only
        "STYLES": "",            # default styling
        "FORMAT": "image/png",
        "TRANSPARENT": "true",
        "CRS": "EPSG:4326",
        "BBOX": f"{MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON}",
        "WIDTH": str(IMG_WIDTH),
        "HEIGHT": str(IMG_HEIGHT),
        "TIME": time_iso
    }
    # Assemble URL with query string
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{WMS_BASE}?{qs}"

# 4. Download the PNG from WMS
def fetch_png(url: str, dest: Path):
    print(f"[→] Downloading PNG from WMS:\n    {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"[✓] Saved {dest.name}")

# 5. Generate KML pointing to the hosted PNG
def build_kml_text(hosted_png_url: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>NOAA CONUS Temperature (WMS)</name>
    <GroundOverlay>
      <name>CONUS Temperature</name>
      <Icon>
        <href>{hosted_png_url}</href>
      </Icon>
      <LatLonBox>
        <north>{MAX_LAT:.6f}</north>
        <south>{MIN_LAT:.6f}</south>
        <east>{MAX_LON:.6f}</east>
        <west>{MIN_LON:.6f}</west>
      </LatLonBox>
    </GroundOverlay>
  </Document>
</kml>
"""

# 6. Save KML to disk
def save_kml(kml_text: str, dest: Path):
    dest.write_text(kml_text, encoding="utf-8")
    print(f"[✓] Wrote {dest.name}")

# 7. Main workflow
def main():
    # a. Compute cycle time & WMS URL
    cycle_iso = get_latest_cycle_iso()
    print(f"⏱ Forecast cycle: {cycle_iso}")
    wms_url = build_wms_url(cycle_iso)

    # b. Download forecast.png
    png_path = Path(PNG_FILENAME)
    fetch_png(wms_url, png_path)

    # c. Generate & save KML
    #    Replace with your actual GitHub Pages URL location
    hosted_url = (
        "https://github.com/jeandeauxmail-cell/temperaturetest/gh-pages"
        "temperaturetest/"
        f"{PNG_FILENAME}"
    )
    kml_text = build_kml_text(hosted_url)
    save_kml(kml_text, Path(KML_FILENAME))

if __name__ == "__main__":
    main()
