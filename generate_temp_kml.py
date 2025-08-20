#!/usr/bin/env python3
"""
Generates a live KML NetworkLink for the CONUS current temperature
layer using the ArcGIS ImageServer endpoint
(working in Google Earth) and the latest valid timestamp from the
<Extent name="time"> element.
"""

import requests
import xml.etree.ElementTree as ET

# ImageServer (Google Earth-friendly) endpoint
BASE_URL = "https://idpgis.ncep.noaa.gov/arcgis/rest/services/NDFDTemps/CONUS_Temp/ImageServer"

# Output KML file
OUTPUT_KML = "conus_temp_live.kml"

def get_latest_time():
    # Use the same endpoint but call "GetCapabilities" to read the extent info
    caps_url = f"{BASE_URL}?f=pjson"
    resp = requests.get(caps_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Extent values are in data["timeInfo"]["timeExtent"] list (start, end, interval)
    start, end, interval = data["timeInfo"]["timeExtent"]
    # Use 'end' minus one interval
    end_ms = end - interval
    # ArcGIS returns milliseconds since epoch -> convert to ISO string
    from datetime import datetime
    t = datetime.utcfromtimestamp(end_ms / 1000.0)
    return t.isoformat() + "Z"

def build_kml(time_value):
    # CONUS bbox in EPSG:4326 (ImageServer is WGS84 by default)
    bbox = "-125,24,-66,49"
    # Build exportImage URL
    img_url = (
     f"{BASE_URL}/exportImage?bbox={bbox}&size=1024,768"
     f"&format=png&transparent=true&f=image&time={time_value}"
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Live CONUS Temperature (NDFD - ImageServer)</name>
    <NetworkLink>
      <name>Current Temperature (ImageServer)</name>
      <Link>
        <href><![CDATA[{img_url}]]></href>
        <refreshMode>onInterval</refreshMode>
        <refreshInterval>900</refreshInterval>
      </Link>
    </NetworkLink>

    <ScreenOverlay>
      <name>Legend</name>
      <Icon>
        <href>https://digital.weather.gov/staticpages/legend/tempscale_conus.png</href>
      </Icon>
      <overlayXY x="0" y="0" xunits="fraction" yunits="fraction"/>
      <screenXY  x="0.02" y="0.02" xunits="fraction" yunits="fraction"/>
      <size      x="0" y="0" xunits="pixels" yunits="pixels"/>
    </ScreenOverlay>
  </Document>
</kml>"""

def main():
    ts = get_latest_time()
    print("Using time:", ts)
    kml = build_kml(ts)
    with open("conus_temp_live.kml", "w", encoding="utf-8") as f:
        f.write(kml)

if __name__ == "__main__":
    main()
