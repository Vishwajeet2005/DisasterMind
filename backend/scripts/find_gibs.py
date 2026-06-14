import urllib.request
import xml.etree.ElementTree as ET

url = "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0"
response = urllib.request.urlopen(url)
xml_data = response.read()
root = ET.fromstring(xml_data)

layers = []
for elem in root.iter():
    if 'Layer' in elem.tag:
        name_elem = elem.find('{http://www.opengis.net/wms}Name')
        if name_elem is not None:
            layers.append(name_elem.text)

print("Surface Temp layers:")
for l in layers:
    if 'Surface_Temp' in l or 'LST' in l:
        print(l)

print("\nSoil Moisture layers:")
for l in layers:
    if 'Soil_Moisture' in l or 'SMAP' in l:
        print(l)
