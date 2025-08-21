#!/usr/bin/env python3
"""
Generate a KML with a live CONUS temperature overlay
using NOAA's ArcGIS REST MapServer (export endpoint).
"""

# ArcGIS REST MapServer export endpoint (CONUS temps)
EXPORT_URL = (
    "https://mapservices.weather.noaa.gov/raster/rest/services/NDFD/NDFD_temp/MapServer/export"
    "?bbox=-130,20,-60,55"
    "&size=1024,768"
    "&format=png"
    "&f=image"
    "&layers=show:0"
    "&imageSR=4326"
    "&bboxSR=4326"
    "&transparent=true"
    "&showLabels=false"
    "&renderingRule=%7B%22rasterFunction%22%3A%22None%22%7D"
)

OUTPUT_KML = "conus_temp_live.kml"
NETWORK_LINK_KML = "network_link.kml"


def build_overlay_kml():
    # GroundOverlay with correct lat/lon bounds for CONUS
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Live CONUS Temperature (NDFD)</name>

    <GroundOverlay>
      <name>Temperature Overlay</name>
      <Icon>
        <href>{EXPORT_URL}</href>
      </Icon>
      <LatLonBox>
        <north>55</north>
        <south>20</south>
        <east>-60</east>
        <west>-130</west>
      </LatLonBox>
    </GroundOverlay>

    <!-- Legend -->
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


def build_networklink_kml():
    # A network link to auto-refresh every 15 minutes
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>NetworkLink - Live CONUS Temperature</name>
    <NetworkLink>
      <name>CONUS Current Temperature</name>
      <refreshVisibility>1</refreshVisibility>
      <Link>
        <href>https://jeandeauxmail-cell.github.io/temperaturetest/{OUTPUT_KML}</href>
        <refreshMode>onInterval</refreshMode>
        <refreshInterval>900</refreshInterval>
      </Link>
    </NetworkLink>
  </Document>
</kml>
"""


def main():
    overlay = build_overlay_kml()
    with open(OUTPUT_KML, "w", encoding="utf-8") as f:
        f.write(overlay)

    netlink = build_networklink_kml()
    with open(NETWORK_LINK_KML, "w", encoding="utf-8") as f:
        f.write(netlink)

    print(f"Wrote {OUTPUT_KML} and {NETWORK_LINK_KML}")


if __name__ == "__main__":
    main()
