#!/usr/bin/env python3
"""
Fetches the latest valid timestamp (timeExtent) from the CONUS ImageServer
and generates a KML file containing a NetworkLink to a GroundOverlay so that
Google Earth will actually display the image.
"""

import requests
import json
from datetime import datetime

# ArcGIS ImageServer endpoint (Google Earth friendly)
BASE_URL = "https://idpgis.ncep.noaa.gov/arcgis/rest/services/NDFDTemps/CONUS_Temp/ImageServer"

OUTPUT_KML = "conus_temp_live.kml"

def get_latest_time():
    info_url = f"{BASE_URL}?f=pjson"
    resp = requests.get(info_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    start, end, interval = data["timeInfo"]["timeExtent"]
    # Use the last published time by subtracting one interval
    latest_ms = end - interval
    dt = datetime.utcfromtimestamp(latest_ms / 1000.0)
    return dt.isoformat() + "Z"

def build_kml(time_value):
    # ImageServer exportImage request
    img_url = (
        f"{BASE_URL}/exportImage?bbox=-125,24,-66,49"
        f"&size=1024,768&f=image&transparent=true"
        f"&format=png&time={time_value}"
    )

    # KML with a GroundOverlay (wrapped in a NetworkLink so it refreshes)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Live CONUS Temperature (NDFD ImageServer)</name>

    <NetworkLink>
      <name>Current Temperature Image Overlay</name>
      <refreshInterval>900</refreshInterval>
      <refreshMode>onInterval</refreshMode>
      <Link>
        <href><![CDATA[data:text/xml,
<GroundOverlay>
  <name>Temperature Overlay</name>
  <Icon>
    <href>{img_url}</href>
  </Icon>
  <LatLonBox>
    <north>49</north>
    <south>24</south>
    <east>-66</east>
    <west>-125</west>
  </LatLonBox>
</GroundOverlay>]]></href>
      </Link>
    </NetworkLink>

    <ScreenOverlay>
      <name>Legend</name>
      <Icon>
        <href>https://digital.weather.gov/staticpages/legend/tempscale_conus.png</href>
      </Icon>
      <overlayXY x="0" y="0" xunits="fraction" yunits="fraction"/>
      <screenXY  x="0.02" y="0.02" xunits="fraction" yunits="fraction"/>
      <size      x="0"  y="0" xunits="pixels" yunits="pixels"/>
    </ScreenOverlay>

  </Document>
</kml>"""

def main():
    latest = get_latest_time()
    kml = build_kml(latest)
    with open(OUTPUT_KML, "w", encoding="utf-8") as f:
        f.write(kml)
    print("Wrote", OUTPUT_KML)

if __name__ == "__main__":
    main()
