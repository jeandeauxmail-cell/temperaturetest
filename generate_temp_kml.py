#!/usr/bin/env python3
"""
Builds a live KML NetworkLink for the NOAA NDFD CONUS temperature layer
using the **current UTC hour** as the 'time' parameter.
This avoids relying on dimension values in GetCapabilities.
"""

import datetime

# Base WMS endpoint
WMS_BASE = "https://digital.weather.gov/ndfd/wms"
LAYER = "ndfd.conus.temp"
OUTPUT_KML = "conus_temp_live.kml"

def build_kml():
    # Use current UTC hour (rounded down)
    now = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    time_value = now.isoformat() + "Z"

    bbox = "-14200679.12,2500000,-7400000,6505689.94"  # EPSG:3857 CONUS
    href = (
        f"{WMS_BASE}?service=WMS&version=1.3.0&request=GetMap"
        f"&layers={LAYER}&styles=&crs=EPSG:3857&bbox={bbox}"
        f"&width=1024&height=768&format=image/png&transparent=true"
        f"&time={time_value}"
    )

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
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
      <size      x="0"  y="0" xunits="pixels" yunits="pixels"/>
    </ScreenOverlay>
  </Document>
</kml>
"""
    return kml

def main():
    kml = build_kml()
    with open(OUTPUT_KML, "w", encoding="utf-8") as f:
        f.write(kml)
    print(f"Wrote {OUTPUT_KML}")

if __name__ == "__main__":
    main()
