#!/usr/bin/env python3
import requests
from datetime import datetime
from pathlib import Path

# 1. Geographic extents & image size
MIN_LON, MAX_LON = -130.0, -60.0
MIN_LAT, MAX_LAT =   20.0,   55.0
IMG_WIDTH  = 1024
IMG_HEIGHT = 512    # keeps the 2:1 aspect ratio for 70°×35°

# 2. Filenames & GitHub Pages URL
PNG_FILENAME = "forecast.png"
KML_FILENAME = "temperature-overlay.kml"
GH_PAGES_URL = "https://jeandeauxmail-cell.github.io/temperaturetest/forecast.png"


# 3. Correct WMS base URL (no /rest/)
WMS_BASE = (
    "https://mapservices.weather.noaa.gov/"
    "raster/services/NDFD/NDFD_temp/MapServer/WmsServer"
)

def get_latest_cycle_iso():
    """Round current UTC down to the last 3‐hour forecast cycle."""
    now = datetime.utcnow()
    cycle_hour = (now.hour // 3) * 3
    cycle = now.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)
    return cycle.strftime("%Y-%m-%dT%H:%M:%SZ")

def build_wms_url(time_iso):
    """
    Assemble a WMS GetMap URL that returns just the temperature grid
    with no legend or timestamps baked in.
    """
    params = {
        "SERVICE":    "WMS",
        "REQUEST":    "GetMap",
        "VERSION":    "1.1.1",              # use 1.1.1 for lon,lat BBOX order
        "LAYERS":     "0",                  # only the temp raster layer
        "STYLES":     "",
        "FORMAT":     "image/png",
        "TRANSPARENT":"true",
        "SRS":        "EPSG:4326",          # axis order lon,lat
        "BBOX":       f"{MIN_LON},{MIN_LAT},{MAX_LON},{MAX_LAT}",
        "WIDTH":      str(IMG_WIDTH),
        "HEIGHT":     str(IMG_HEIGHT),
        "TIME":       time_iso
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{WMS_BASE}?{qs}"

def fetch_png(url: str, dest: Path):
    print(f"[→] Fetching PNG:\n    {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"[✓] Saved {dest.name}")

def build_kml_text(png_url: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>NOAA CONUS Temperature (WMS)</name>
    <GroundOverlay>
      <name>CONUS Temperature</name>
      <Icon>
        <href>{png_url}</href>
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

def save_kml(text: str, dest: Path):
    dest.write_text(text, encoding="utf-8")
    print(f"[✓] Wrote {dest.name}")

def main():
    cycle = get_latest_cycle_iso()
    print(f"⏱ Forecast cycle: {cycle}")

    wms_url = build_wms_url(cycle)
    png_path = Path(PNG_FILENAME)
    fetch_png(wms_url, png_path)

    hosted_png = f"{GH_PAGES_URL}/{PNG_FILENAME}"
    kml = build_kml_text(hosted_png)
    save_kml(kml, Path(KML_FILENAME))

if __name__ == "__main__":
    main()
