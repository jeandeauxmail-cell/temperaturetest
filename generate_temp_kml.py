#!/usr/bin/env python3
"""
Fetches the NDFD temperature GetCapabilities, extracts the latest
<Extent name="time"> value for the `ndfd.conus.temp` layer,
and builds a live KML NetworkLink pointing to that timestamp.
"""

import requests
import xml.etree.ElementTree as ET

# Working WMS endpoint
WMS_BASE = (
    "https://mapservices.weather.noaa.gov/raster/services/"
    "NDFD/NDFD_temp/MapServer/WMSServer"
)

LAYER = "ndfd.conus.temp"
OUTPUT_KML = "conus_temp_live.kml"

def get_latest_time():
    caps_url = f"{WMS_BASE}?service=WMS&request=GetCapabilities&version=1.3.0"
    resp = requests.get(caps_url, timeout=30)
    resp.raise_for_status()

    ns = {"wms": "http://www.opengis.net/wms"}
    root = ET.fromstring(resp.content)
    for lyr in root.findall(".//wms:Layer", ns):
        name_elt = lyr.find("wms:Name", ns)
        if name_elt is not None and name_elt.text == LAYER:
            time_extent = lyr.find("wms:Extent[@name='time']", ns)
            if time_extent is not None and time_extent.text:
                times = time_extent.text.strip().split(",")
                return times[-1]

    raise RuntimeError("Could not find <Extent name='time'> for layer.")

def build_kml(time_value):
    bbox = "-14200679.12,2500000,-7400000,6505689.94"
    href = (
        f"{WMS_BASE}?service=WMS&version=1.3.0&request=GetMap"
        f"&layers={LAYER}&styles=&crs=EPSG:3857&bbox={bbox}"
        f"&width=1024&height=768&format=image/png&transparent=true&opacity=1"
        f"&time={time_value}"
    )

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
    latest_time = get_latest_time()
    print(f"Using latest valid timestamp: {latest_time}")
    kml = build_kml(latest_time)
    with open(OUTPUT_KML, "w", encoding="utf-8") as f:
        f.write(kml)

if __name__ == "__main__":
    main()
