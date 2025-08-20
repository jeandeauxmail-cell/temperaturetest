#!/usr/bin/env python3
"""
Fixed version: Fetches the latest NDFD temperature data and generates a proper KML 
with GroundOverlay that works reliably in Google Earth.
"""

import requests
import json
from datetime import datetime, timezone
import urllib.parse
import xml.sax.saxutils

# Current working NDFD endpoints (try in order of preference)
BASE_URL = "https://mapservices.weather.noaa.gov/raster/rest/services/NDFD/NDFD_temp/MapServer"

OUTPUT_KML = "conus_temp_live.kml"

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
    # Use the MapServer export endpoint
    export_endpoint = f"{base_url}/export"
    
    # Parameters for the image request - key fix: specify the correct layers
    params = {
        'bbox': '-130,20,-60,55',  # CONUS bounding box
        'size': '1200,800',        # Higher resolution
        'format': 'png',
        'f': 'image',
        'transparent': 'true',     # Changed to true for proper overlay
        'imageSR': '4326',         # WGS84 coordinate system
        'bboxSR': '4326',
        'layers': 'show:0,1,2',    # Show temperature layers (TempF layers)
        'dpi': '96'
    }
    
    # Only add time if we have a valid timestamp
    if time_ms and str(time_ms) != 'None':
        params['time'] = str(time_ms)
    
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
      </Icon>
      <LatLonBox>
        <north>55</north>
        <south>20</south>
        <east>-60</east>
        <west>-130</west>
        <rotation>0</rotation>
      </LatLonBox>
      <color>aaffffff</color>
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
    print("Finding working NDFD temperature endpoint...")
    
    try:
        # Use the working endpoint
        base_url = BASE_URL
        
        # Get the latest timestamp
        latest_time_ms = get_latest_time(base_url)
        print(f"Using timestamp: {latest_time_ms}")
        
        # Build the image URL
        image_url = build_image_url(base_url, latest_time_ms)
        print(f"Testing image URL: {image_url}")
        
        # Test if the image URL works with better debugging
        test_resp = requests.get(image_url, timeout=30)
        print(f"Response status: {test_resp.status_code}")
        print(f"Response headers: {dict(test_resp.headers)}")
        
        if test_resp.status_code == 200:
            print(f"✓ Image URL working! Content-Type: {test_resp.headers.get('content-type')}")
            print(f"Image size: {len(test_resp.content)} bytes")
        else:
            print(f"✗ Image URL failed with status {test_resp.status_code}")
            print(f"Response text: {test_resp.text[:200]}...")
            
            # Try a simpler request without time parameter
            simple_params = {
                'bbox': '-130,20,-60,55',
                'size': '800,600',
                'format': 'png',
                'f': 'image',
                'transparent': 'true',
                'imageSR': '4326',
                'bboxSR': '4326',
                'layers': 'show:0'
            }
            simple_url = f"{base_url}/export?" + urllib.parse.urlencode(simple_params)
            print(f"Trying simpler URL: {simple_url}")
            
            simple_resp = requests.get(simple_url, timeout=30)
            if simple_resp.status_code == 200:
                print("✓ Simple URL works! Using this instead.")
                image_url = simple_url
            else:
                print(f"✗ Simple URL also failed: {simple_resp.status_code}")
                print("Proceeding with original URL anyway...")
        
        print(f"Final image URL: {image_url[:100]}...")
        
        # Generate KML
        print(f"Raw image URL: {image_url}")
        kml_content = create_kml(image_url, latest_time_ms)
        
        # Debug: Show the problematic line
        lines = kml_content.split('\n')
        if len(lines) >= 12:
            print(f"Line 12 content: {lines[11]}")
            print(f"Characters around column 134: '{lines[11][130:140]}'")
        
        # Validate XML before writing
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(kml_content)
            print("✓ KML XML is valid!")
        except ET.ParseError as e:
            print(f"✗ KML XML validation failed: {e}")
            # Try alternative escaping approach
            print("Trying alternative URL encoding...")
            
            # Use CDATA section for the URL instead
            escaped_url = f"<![CDATA[{image_url}]]>"
            alt_kml = kml_content.replace(f"<href>{xml.sax.saxutils.escape(image_url)}</href>", 
                                       f"<href>{escaped_url}</href>")
            
            try:
                ET.fromstring(alt_kml)
                print("✓ Alternative CDATA encoding works!")
                kml_content = alt_kml
            except ET.ParseError as e2:
                print(f"✗ CDATA encoding also failed: {e2}")
                return False
        
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
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
