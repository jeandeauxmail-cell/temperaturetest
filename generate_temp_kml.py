#!/usr/bin/env python3
"""
Improved NDFD temperature KML generator with better error handling and multiple service options
"""

import requests
import json
from datetime import datetime, timezone
import urllib.parse
import xml.sax.saxutils

# Multiple NDFD endpoints to try (in order of preference)
NDFD_ENDPOINTS = [
    "https://mapservices.weather.noaa.gov/raster/rest/services/NDFD/NDFD_temp/MapServer",
    "https://nowcoast.noaa.gov/arcgis/rest/services/nowcoast/forecast_meteoceanhydro_sfc_ndfd_time/MapServer",
    "https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/NDFD_temp/MapServer"
]

# Alternative: Try WMS service as backup
WMS_ENDPOINTS = [
    {
        'name': 'NDFD WMS',
        'url': 'https://digital.weather.gov/wms.php',
        'layer': 'temp',
        'format': 'image/png'
    }
]

OUTPUT_KML = "conus_temp_live.kml"
NETWORK_KML = "network_link.kml"

def test_service_endpoint(base_url):
    """Test if a service endpoint is working"""
    try:
        info_url = f"{base_url}?f=pjson"
        resp = requests.get(info_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        print(f"✓ Service active: {base_url}")
        print(f"  Service name: {data.get('mapName', 'Unknown')}")
        
        # Check for layers
        layers = data.get('layers', [])
        print(f"  Available layers: {len(layers)}")
        for layer in layers[:3]:  # Show first 3 layers
            print(f"    - {layer.get('name', 'Unknown')} (ID: {layer.get('id', 'N/A')})")
        
        return True, data
    except Exception as e:
        print(f"✗ Service failed: {base_url} - {e}")
        return False, None

def try_wms_service():
    """Try WMS service as alternative to MapServer"""
    wms_config = WMS_ENDPOINTS[0]
    
    params = {
        'service': 'WMS',
        'version': '1.3.0',
        'request': 'GetMap',
        'layers': wms_config['layer'],
        'styles': '',
        'width': '800',
        'height': '600',
        'crs': 'EPSG:4326',
        'bbox': '20,-130,55,-60',  # Note: WMS 1.3.0 uses lat,lon order for EPSG:4326
        'format': wms_config['format'],
        'transparent': 'true'
    }
    
    wms_url = f"{wms_config['url']}?" + urllib.parse.urlencode(params)
    print(f"\nTrying WMS service: {wms_url}")
    
    if test_image_url(wms_url):
        print("✓ WMS service works!")
        return wms_url, wms_config['name']
    else:
        print("✗ WMS service failed")
        return None, None
def get_working_endpoint():
    """Find the first working NDFD endpoint"""
    for endpoint in NDFD_ENDPOINTS:
        print(f"\nTesting endpoint: {endpoint}")
        working, service_info = test_service_endpoint(endpoint)
        if working:
            return endpoint, service_info
    
    # Try WMS as fallback
    print("\nMapServer endpoints failed, trying WMS...")
    wms_url, wms_name = try_wms_service()
    if wms_url:
        return wms_url, {'mapName': wms_name, 'layers': [], 'wms': True}
    
    raise Exception("No working NDFD endpoints found!")

def get_latest_time(base_url, service_info):
    """Get the most recent available timestamp from the service"""
    try:
        # Check if service has time info
        time_info = service_info.get("timeInfo", {})
        if time_info:
            time_extent = time_info.get("timeExtent", [])
            if len(time_extent) >= 2:
                start_ms, end_ms = time_extent[0], time_extent[1]
                dt = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc)
                print(f"Service time range ends at: {dt}")
                return int(end_ms)
        
        # Alternative: check individual layers for time info
        layers = service_info.get('layers', [])
        for layer in layers:
            if 'timeInfo' in layer:
                layer_time = layer['timeInfo'].get('timeExtent', [])
                if len(layer_time) >= 2:
                    end_ms = layer_time[1]
                    dt = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc)
                    print(f"Layer {layer['id']} time ends at: {dt}")
                    return int(end_ms)
        
        # Fallback: use current time
        print("No time extent found, using current time")
        now = datetime.now(timezone.utc)
        return int(now.timestamp() * 1000)
            
    except Exception as e:
        print(f"Error getting time info: {e}")
        now = datetime.now(timezone.utc)
        return int(now.timestamp() * 1000)

def build_image_url(base_url, time_ms, service_info):
    """Build the image export URL with proper parameters"""
    export_endpoint = f"{base_url}/export"
    
    # Get the first temperature layer
    temp_layer_id = 0
    layers = service_info.get('layers', [])
    for layer in layers:
        name = layer.get('name', '').lower()
        if 'temp' in name and 'max' not in name and 'min' not in name:
            temp_layer_id = layer.get('id', 0)
            print(f"Using temperature layer: {layer.get('name')} (ID: {temp_layer_id})")
            break
    
    # Try multiple parameter combinations to find one that works without text overlay
    param_sets = [
        # Option 1: Disable dynamic layers and text
        {
            'bbox': '-130,20,-60,55',
            'size': '800,600',
            'format': 'png32',
            'f': 'image',
            'layers': f'show:{temp_layer_id}',
            'imageSR': '4326',
            'bboxSR': '4326',
            'transparent': 'true',
            'dynamicLayers': '',  # Disable dynamic layers
            'layerDefs': '',      # No layer definitions
            'mapScale': '',       # No scale
            'rotation': '',       # No rotation
            'datumTransformations': '',
            'layerTimeOptions': '',
            'gdbVersion': '',
            'historicMoment': '',
            'mapRangeValues': '',
            'layerRangeValues': '',
            'layerParameterValues': ''
        },
        # Option 2: Very minimal parameters
        {
            'bbox': '-130,20,-60,55',
            'size': '800,600',
            'format': 'png',
            'f': 'image',
            'layers': f'show:{temp_layer_id}',
            'imageSR': '4326',
            'bboxSR': '4326',
            'transparent': 'false'  # Try without transparency
        },
        # Option 3: Different image format
        {
            'bbox': '-130,20,-60,55',
            'size': '800,600',
            'format': 'jpg',  # JPG instead of PNG
            'f': 'image',
            'layers': f'show:{temp_layer_id}',
            'imageSR': '4326',
            'bboxSR': '4326'
        },
        # Option 4: Web Mercator projection
        {
            'bbox': '-14465442.4,2273030.9,-6679169.4,7361866.1',  # Web Mercator CONUS
            'size': '800,600',
            'format': 'png',
            'f': 'image',
            'layers': f'show:{temp_layer_id}',
            'imageSR': '3857',
            'bboxSR': '3857',
            'transparent': 'true'
        }
    ]
    
    for i, params in enumerate(param_sets):
        # Add time parameter only if available and for first few attempts
        if i < 3 and time_ms and time_ms > 0:
            params['time'] = str(int(time_ms))
        
        # Remove empty parameters to clean up URL
        clean_params = {k: v for k, v in params.items() if v != ''}
        
        test_url = f"{export_endpoint}?" + urllib.parse.urlencode(clean_params)
        print(f"\nTrying parameter set {i+1}:")
        print(f"URL: {test_url[:100]}...")
        
        if test_image_url(test_url):
            print(f"✓ Parameter set {i+1} works!")
            return test_url
        else:
            print(f"✗ Parameter set {i+1} failed")
    
    # Fallback to first parameter set
    params = param_sets[1]  # Use the minimal parameters as fallback
    if time_ms and time_ms > 0:
        params['time'] = str(int(time_ms))
    
    clean_params = {k: v for k, v in params.items() if v != ''}
    return f"{export_endpoint}?" + urllib.parse.urlencode(clean_params)

def test_image_url(image_url):
    """Test if the image URL returns valid data"""
    try:
        print(f"Testing image URL...")
        resp = requests.get(image_url, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type')}")
        print(f"Content-Length: {len(resp.content)} bytes")
        
        if resp.status_code == 200:
            content_type = resp.headers.get('content-type', '').lower()
            if 'image' in content_type:
                print("✓ Valid image response!")
                return True
            elif 'json' in content_type or 'text' in content_type:
                # Might be an error response
                print(f"Response text: {resp.text[:500]}")
                return False
        
        return resp.status_code == 200
        
    except Exception as e:
        print(f"Error testing image URL: {e}")
        return False

def create_kml(image_url, timestamp_ms, service_name="NDFD"):
    """Create the KML content with proper GroundOverlay structure"""
    
    # Convert timestamp for display
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
    time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
    
    # XML escape the URL
    safe_image_url = xml.sax.saxutils.escape(image_url)
    
    kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>CONUS Temperature - {time_str}</name>
    <description>Live {service_name} temperature data for Continental United States. Updates every 30 minutes.</description>
    
    <Style id="tempStyle">
      <ListStyle>
        <ItemIcon>
          <href>https://maps.google.com/mapfiles/kml/paddle/T.png</href>
        </ItemIcon>
      </ListStyle>
    </Style>
    
    <!-- Temperature Ground Overlay -->
    <GroundOverlay>
      <name>Temperature Data</name>
      <description>Current Temperature - Updated: {time_str}</description>
      <styleUrl>#tempStyle</styleUrl>
      <Icon>
        <href>{safe_image_url}</href>
        <refreshMode>onInterval</refreshMode>
        <refreshInterval>1800</refreshInterval>
        <viewRefreshMode>never</viewRefreshMode>
      </Icon>
      <LatLonBox>
        <north>55</north>
        <south>20</south>
        <east>-60</east>
        <west>-130</west>
        <rotation>0</rotation>
      </LatLonBox>
      <color>ccffffff</color>
      <drawOrder>10</drawOrder>
    </GroundOverlay>
    
    <!-- Temperature Legend -->
    <ScreenOverlay>
      <name>Temperature Legend</name>
      <description>Temperature scale in Fahrenheit</description>
      <Icon>
        <href>https://digital.weather.gov/staticpages/legend/tempscale_conus.png</href>
      </Icon>
      <overlayXY x="0" y="1" xunits="fraction" yunits="fraction"/>
      <screenXY x="0.02" y="0.98" xunits="fraction" yunits="fraction"/>
      <size x="200" y="0" xunits="pixels" yunits="fraction"/>
    </ScreenOverlay>
    
    <!-- Default view -->
    <LookAt>
      <longitude>-98</longitude>
      <latitude>39</latitude>
      <altitude>0</altitude>
      <range>4000000</range>
      <tilt>0</tilt>
      <heading>0</heading>
      <altitudeMode>absolute</altitudeMode>
    </LookAt>
    
  </Document>
</kml>'''
    
    return kml_content

def create_network_link_kml(github_username, repo_name):
    """Create a network link KML for GitHub Pages"""
    network_kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Live CONUS Temperature</name>
    <description>Auto-updating temperature data from NOAA NDFD</description>
    
    <NetworkLink>
      <name>CONUS Temperature Data</name>
      <description>Updates every 30 minutes</description>
      <refreshVisibility>0</refreshVisibility>
      <flyToView>1</flyToView>
      <Link>
        <href>https://{github_username}.github.io/{repo_name}/conus_temp_live.kml</href>
        <refreshMode>onInterval</refreshMode>
        <refreshInterval>1800</refreshInterval>
        <viewRefreshMode>never</viewRefreshMode>
      </Link>
    </NetworkLink>
    
  </Document>
</kml>'''
    
    return network_kml

def main():
    """Main execution function"""
    print("=" * 60)
    print("NDFD Temperature KML Generator")
    print("=" * 60)
    
    try:
        # Find working endpoint
        base_url, service_info = get_working_endpoint()
        service_name = service_info.get('mapName', 'NDFD')
        
        # Get latest timestamp
        latest_time_ms = get_latest_time(base_url, service_info)
        print(f"\nUsing timestamp: {latest_time_ms}")
        
        # Build image URL
        image_url = build_image_url(base_url, latest_time_ms, service_info)
        print(f"\nGenerated image URL:")
        print(f"{image_url}")
        
        # Test the image URL
        if not test_image_url(image_url):
            print("\n⚠️  Image URL test failed, but proceeding anyway...")
            print("Google Earth might still be able to load it.")
        
        # Generate main KML
        kml_content = create_kml(image_url, latest_time_ms, service_name)
        
        with open(OUTPUT_KML, 'w', encoding='utf-8') as f:
            f.write(kml_content)
        
        print(f"\n✓ Successfully created {OUTPUT_KML}")
        print(f"  File size: {len(kml_content):,} bytes")
        
        # Generate network link KML (update with your GitHub info)
        network_content = create_network_link_kml("jeandeauxmail-cell", "temperaturetest")
        
        with open(NETWORK_KML, 'w', encoding='utf-8') as f:
            f.write(network_content)
        
        print(f"✓ Successfully created {NETWORK_KML}")
        
        print("\n" + "=" * 60)
        print("SUCCESS! Files generated:")
        print(f"  - {OUTPUT_KML} (main data file)")
        print(f"  - {NETWORK_KML} (for linking in Google Earth)")
        print("\nTo use:")
        print("  1. Open Google Earth")
        print(f"  2. File > Open > {NETWORK_KML}")
        print("  3. The layer will auto-refresh every 30 minutes")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
