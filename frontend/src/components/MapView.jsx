import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Rectangle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Preset Regions
const PRESETS = [
    { id: "wayanad", name: "Wayanad, Kerala", lat: 11.6854, lon: 76.1320, bbox: [11.5, 75.9, 11.9, 76.3] },
    { id: "kamrup", name: "Kamrup, Assam", lat: 26.3161, lon: 91.5984, bbox: [26.1, 91.3, 26.5, 91.8] },
    { id: "chamoli", name: "Chamoli, Uttarakhand", lat: 30.2736, lon: 79.3234, bbox: [30.0, 79.1, 30.5, 79.5] }
];

const pulsingIcon = new L.DivIcon({
  className: 'custom-pulsing-icon',
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

// Component to handle map centering when a region is selected
const MapUpdater = ({ center, bbox }) => {
  const map = useMap();
  useEffect(() => {
    if (bbox && bbox.length === 4) {
      const bounds = [
        [bbox[0], bbox[1]], // lat_min, lon_min
        [bbox[2], bbox[3]]  // lat_max, lon_max
      ];
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (center) {
      map.setView(center, 8);
    }
  }, [center, bbox, map]);
  return null;
};

const MapView = ({ selectedRegion, onSelectRegion }) => {
  const center = selectedRegion ? [selectedRegion.lat, selectedRegion.lon] : [20.5937, 78.9629]; // India center
  
  return (
    <MapContainer 
      center={center} 
      zoom={5} 
      className="map-container"
      style={{ height: '100%', width: '100%' }}
      zoomControl={false}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
      />
      
      <MapUpdater center={center} bbox={selectedRegion?.bbox} />

      {PRESETS.map((region) => (
        <Marker 
          key={region.id}
          position={[region.lat, region.lon]}
          icon={pulsingIcon}
          eventHandlers={{
            click: () => onSelectRegion(region)
          }}
        />
      ))}

      {selectedRegion && selectedRegion.bbox && (
        <Rectangle
          bounds={[
            [selectedRegion.bbox[0], selectedRegion.bbox[1]],
            [selectedRegion.bbox[2], selectedRegion.bbox[3]]
          ]}
          pathOptions={{ color: '#00BCD4', weight: 1, fillOpacity: 0.3 }}
        />
      )}
    </MapContainer>
  );
};

export default MapView;
