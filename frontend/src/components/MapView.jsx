import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Rectangle, useMap, LayersControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Preset Regions
const PRESETS = [
    { id: "wayanad", name: "Wayanad, Kerala", lat: 11.6854, lon: 76.1320, bbox: [11.5, 75.9, 11.9, 76.3] },
    { id: "kamrup", name: "Kamrup, Assam", lat: 26.3161, lon: 91.5984, bbox: [26.1, 91.3, 26.5, 91.8] },
    { id: "chamoli", name: "Chamoli, Uttarakhand", lat: 30.2736, lon: 79.3234, bbox: [30.0, 79.1, 30.5, 79.5] }
];

const pulsingIcon = new L.DivIcon({
  className: 'custom-pulsing-icon-container',
  html: '<div class="custom-pulsing-icon"></div>',
  iconSize: [24, 24],
  iconAnchor: [12, 12]
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
      map.setView(center, 5); // Using initial zoom level instead of zoomed-in 8 for center view
    }
  }, [center[0], center[1], bbox ? bbox.join(',') : '', map]);
  return null;
};

const MapView = ({ selectedRegion, onSelectRegion, riskLevel }) => {
  const center = selectedRegion ? [selectedRegion.lat, selectedRegion.lon] : [20.5937, 78.9629]; // India center
  
  const getRiskColor = (level) => {
    switch(level) {
      case 'CRITICAL': return '#D32F2F';
      case 'HIGH': return '#F57C00';
      case 'MODERATE': return '#FBC02D';
      case 'LOW': return '#388E3C';
      default: return '#D32F2F'; // Default to critical marker color
    }
  };

  const boxColor = riskLevel ? getRiskColor(riskLevel) : '#D32F2F';

  return (
    <MapContainer 
      center={center} 
      zoom={5} 
      className="map-container"
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
    >
      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="Google Streets (Live View)">
          <TileLayer
            url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
            attribution='&copy; Google Maps'
            maxZoom={20}
          />
        </LayersControl.BaseLayer>

        <LayersControl.BaseLayer name="Google Hybrid (Satellite + Streets)">
          <TileLayer
            url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
            attribution='&copy; Google Maps'
            maxZoom={20}
          />
        </LayersControl.BaseLayer>

        <LayersControl.BaseLayer name="OpenStreetMap (Standard)">
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap contributors'
          />
        </LayersControl.BaseLayer>
        
        <LayersControl.BaseLayer name="Esri World Imagery">
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution='Tiles &copy; Esri'
          />
        </LayersControl.BaseLayer>
      </LayersControl>
      
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
          pathOptions={{ color: boxColor, weight: 2, fillOpacity: 0.15 }}
        />
      )}
    </MapContainer>
  );
};

export default MapView;
