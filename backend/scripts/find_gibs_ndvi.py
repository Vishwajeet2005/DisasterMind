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

for l in layers:
    if 'NDVI' in l or 'Aerosol' in l:
        print(l)
