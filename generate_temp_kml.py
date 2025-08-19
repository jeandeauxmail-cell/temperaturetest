#!/usr/bin/env python3
"""
Fetches the NOAA NDFD CONUS temperature WMS GetCapabilities,
extracts the most recent available timestamp, and builds a
NetworkLink KML file that references the WMS with the correct time value.
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Base WMS endpoint
WMS_BASE = "https://digital.weather.gov/ndfd/wms"

# Layer name for current temperature (CONUS)
LAYER = "ndfd.conus.temp"

# Output KML file name
OUTPUT_KML = "conus_temp_live.kml"

def get_latest_time(capabilities_xml):
    """Extract the latest <Dimension name="time"> value from the capabilities XML."""
    ns = {"wms": "http://www.opengis.net/wms"}
    root = ET.fromstring(capabilities_xml)
    # find Layer dimension
    for layer in root.findall(".//wms:Layer", ns):
        name = layer.find("wms:Name", ns)
        if name is not None and name.text == LAYER:
            dim = layer.find("wms:Dimension", ns)
            if dim is not None and dim.attrib.get("name") == "time":
                # dimension text = comma separated ISO timestamps
                times = dim.text.strip().split(",")
                # use the last timestamp (usually the most recent)
                return times[-1]
    return None

def build_kml(time_value):
    """Return the KML string using the given timestamp."""
    bbox = "-14200679.12,2500000,-7400000,6505689.94"
    href = (f"{WMS_BASE}?service=WMS&version=1.3.0&request=GetMap"
            f"&layers={LAYER}&styles=&crs=EPSG:3857&bbox={bbox}"
            f"&width=1024&height=768&format=image/png&transparent=true"
            f"&time={time_value}")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Live CONUS Temperature (NDFD)</name>

    <NetworkLink>
      <name>Current Temperature (NDFD)</name>
      <Link>
        <href><![CDATA[{href}]]></href>
        <refreshMode>onInterval</refreshMode>
        <refreshInterval>1800</refreshInterval>
      </Link>
    </NetworkLink>

    <!-- Legend Overlay -->
    <ScreenOverlay>
      <name>Legend</name>
      <Icon>
        <href>https://digital.weather.gov/staticpages/legend/tempscale_conus.png</href>
      </Icon>
      <overlayXY x="0" y="0" xunits="fraction" yunits="fraction"/>
      <screenXY  x="0.02" y="0.02" xunits="fraction" yunits="fraction"/>
      <size      x="0"    y="0"   xunits="pixels"  yunits="pixels"/>
    </ScreenOverlay>

  </Document>
</kml>
"""

def main():
    caps_url = f"{WMS_BASE}?service=WMS&request=GetCapabilities&version=1.3.0"
    resp = requests.get(caps_url, timeout=30)
    resp.raise_for_status()
    latest_time = get_latest_time(resp.text)
    if not latest_time:
        raise RuntimeError("Could not extract time dimension from GetCapabilities.")
    kml = build_kml(latest_time)
    with open(OUTPUT_KML, "w", encoding="utf-8") as f:
        f.write(kml)
    print(f"Wrote {OUTPUT_KML} (time={latest_time})")

if __name__ == "__main__":
    main()
