#!/usr/bin/env python3
"""
Fixed version: Fetches the latest NDFD temperature data and generates a proper KML 
with GroundOverlay that works reliably in Google Earth.
"""

import requests
import json
from datetime import datetime, timezone
import urllib.parse

# Current working NDFD endpoints (try in order of preference)
ENDPOINTS = [
    "https://mapservices.weather.noaa.gov/raster/rest/services/NDFD/NDFD_temp/MapServer",
    "https://nowcoast.noaa.gov/arcgis/rest/services/nowcoast/forecast_meteoceanhydro_sfc_ndfd_time/MapServer",
    "https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/NDFD_temp/MapServer"
]
OUTPUT_KML = "conus_temp_live.kml"

def find_working_endpoint():
    """Find the first working NDFD endpoint"""
    for base_url in ENDPOINTS:
        try:
            info_url = f"{base_url}?f=pjson"
            resp = requests.get(info_url, timeout=15)
            if resp.status_code == 200:
                print(f"Using endpoint: {base_url}")
                return base_url
        except Exception as e:
            print(f"Endpoint {base_url} failed: {e}")
            continue
    
    raise Exception("No working NDFD endpoints found!")

def get_latest_time(base_url):
    """Get the most recent available timestamp from the service"""
    try:
        info_url = f"{base_url}?f=pjson"
        resp = requests.get(info_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Get time extent info
        time_info = data.get("timeInfo", {})
        time_extent = time_info.get("timeExtent", [])
        
        if len(time_extent) >= 2:
            start_ms, end_ms = time_extent[0], time_extent[1]
            # Use the end time (most recent)
            dt = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc)
            print(f"Service time range: {datetime.fromtimestamp(start_ms/1000.0, tz=timezone.utc)} to {dt}")
            return int(end_ms)  # Return as milliseconds for the API
        else:
            # Fallback: use current time
            print("No time extent found, using current time")
            now = datetime.now(timezone.utc)
            return int(now.timestamp() * 1000)
            
    except Exception as e:
        print(f"Error getting time info: {e}")
        # Fallback: use current time
        now = datetime.now(timezone.utc)
        return int(now.timestamp() * 1000)

def build_image_url(base_url, time_ms):
    """Build the proper image export URL"""
    # Check if it's a MapServer or ImageServer
    if "ImageServer" in base_url:
        export_endpoint = f"{base_url}/exportImage"
    else:
        export_endpoint = f"{base_url}/export"
    
    # Parameters for the image request
    params = {
        'bbox': '-130,20,-60,55',  # CONUS bounding box
        'size': '1200,800',        # Higher resolution
        'format': 'png',
        'f': 'image',
        'transparent': 'false',    # Set to false for better visibility
        'time': str(time_ms),
        'imageSR': '4326',         # WGS84 coordinate system
        'bboxSR': '4326',
        'layers': 'show:0'         # Show first layer (temperature)
    }
    
    # Build URL with proper encoding
    query_string = urllib.parse.urlencode(params)
    return f"{export_endpoint}?{query_string}"

def create_kml(image_url, timestamp_ms):
    """Create the KML content with proper GroundOverlay structure"""
    
    # Convert timestamp for display
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
    time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
    
    kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>CONUS Temperature - {time_str}</name>
    <description>Live NDFD temperature data for Continental United States</description>
    
    <!-- Temperature Ground Overlay -->
    <GroundOverlay>
      <name>Temperature Data</name>
      <description>NDFD Temperature - Updated: {time_str}</description>
      <Icon>
        <href>{image_url}</href>
        <refreshMode>onExpire</refreshMode>
        <refreshInterval>1800</refreshInterval>
      </Icon>
      <LatLonBox>
        <north>55</north>
        <south>20</south>
        <east>-60</east>
        <west>-130</west>
        <rotation>0</rotation>
      </LatLonBox>
      <color>ccffffff</color>
    </GroundOverlay>
    
    <!-- Temperature Legend -->
    <ScreenOverlay>
      <name>Temperature Legend</name>
      <Icon>
        <href>https://digital.weather.gov/staticpages/legend/tempscale_conus.png</href>
      </Icon>
      <overlayXY x="0" y="1" xunits="fraction" yunits="fraction"/>
      <screenXY x="0.02" y="0.98" xunits="fraction" yunits="fraction"/>
      <size x="0" y="0" xunits="pixels" yunits="pixels"/>
    </ScreenOverlay>
    
    <!-- View settings -->
    <LookAt>
      <longitude>-98</longitude>
      <latitude>39</latitude>
      <altitude>0</altitude>
      <range>4000000</range>
      <tilt>0</tilt>
      <heading>0</heading>
    </LookAt>
    
  </Document>
</kml>'''
    
    return kml_content

def main():
    """Main execution function"""
    print("Fetching latest NDFD temperature data...")
    
    try:
        # Get the latest timestamp
        latest_time_ms = get_latest_time()
        print(f"Using timestamp: {latest_time_ms}")
        
        # Build the image URL
        image_url = build_image_url(latest_time_ms)
        print(f"Image URL: {image_url[:100]}...")
        
        # Test if the image URL works
        test_resp = requests.head(image_url, timeout=30)
        if test_resp.status_code != 200:
            print(f"Warning: Image URL returned status {test_resp.status_code}")
        
        # Generate KML
        kml_content = create_kml(image_url, latest_time_ms)
        
        # Write to file
        with open(OUTPUT_KML, 'w', encoding='utf-8') as f:
            f.write(kml_content)
        
        print(f"Successfully wrote {OUTPUT_KML}")
        print(f"File size: {len(kml_content)} bytes")
        
        # Also create a network link KML for GitHub Pages
        network_kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Live CONUS Temperature</name>
    <NetworkLink>
      <name>Temperature Data</name>
      <refreshVisibility>0</refreshVisibility>
      <flyToView>1</flyToView>
      <Link>
        <href>https://jeandeauxmail-cell.github.io/temperaturetest/conus_temp_live.kml</href>
        <refreshMode>onInterval</refreshMode>
        <refreshInterval>1800</refreshInterval>
      </Link>
    </NetworkLink>
  </Document>
</kml>'''
        
        with open('network_link.kml', 'w', encoding='utf-8') as f:
            f.write(network_kml)
        print("Also created network_link.kml for GitHub Pages")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
