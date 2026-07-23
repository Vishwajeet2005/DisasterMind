import React, { useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, WMSTileLayer, Rectangle, Tooltip, useMap, LayersControl, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const RISK_FILLS = {
  CRITICAL: 'var(--risk-critical-color)',
  HIGH:     'var(--risk-high-color)',
  MODERATE: 'var(--risk-moderate-color)',
  LOW:      'var(--risk-low-color)',
  NONE:     'rgba(148, 163, 184, 0.2)', // Slate 400 faint
};

const RISK_OPACITY = {
  CRITICAL: 0.45,
  HIGH:     0.35,
  MODERATE: 0.25,
  LOW:      0.15,
  NONE:     0.05,
};

function MapViewRecenter({ selectedCell }) {
  const map = useMap();
  useEffect(() => {
    if (selectedCell) {
      const latMin = selectedCell.lat_min !== undefined ? selectedCell.lat_min : selectedCell.lat - 1.25;
      const latMax = selectedCell.lat_max !== undefined ? selectedCell.lat_max : selectedCell.lat + 1.25;
      const lonMin = selectedCell.lon_min !== undefined ? selectedCell.lon_min : selectedCell.lon - 1.25;
      const lonMax = selectedCell.lon_max !== undefined ? selectedCell.lon_max : selectedCell.lon + 1.25;
      
      const lat = (latMin + latMax) / 2;
      const lon = (lonMin + lonMax) / 2;
      map.flyTo([lat, lon], 7, { animate: true, duration: 1.5 });
    }
  }, [selectedCell, map]);
  return null;
}

export default function IndiaMap({ gridCells, heatmapData, selectedCell, onCellClick }) {
  const riskByCell = useMemo(() => {
    const map = {};
    (heatmapData || []).forEach(row => {
      map[row.cell_id] = row.risk_level;
    });
    return map;
  }, [heatmapData]);

  const center = [22.5, 82.5];
  const zoom = 5;

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: 'var(--bg-map)' }}>
      <MapContainer 
        center={center} 
        zoom={zoom} 
        style={{ width: '100%', height: '100%', background: 'transparent' }}
        zoomControl={false}
      >
        <ZoomControl position="bottomright" />
        <LayersControl position="bottomright">
          <LayersControl.BaseLayer checked name="Dark Matter">
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; OpenStreetMap &copy; CARTO'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Street Map">
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite">
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution='Tiles &copy; Esri'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Topographic">
            <TileLayer
              url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenTopoMap'
            />
          </LayersControl.BaseLayer>
          <LayersControl.Overlay name="Live Fires (NASA FIRMS)">
            <WMSTileLayer
              url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi"
              layers="VIIRS_SNPP_Thermal_Anomalies_375m_All"
              format="image/png"
              transparent={true}
              attribution="NASA GIBS"
            />
          </LayersControl.Overlay>
          <LayersControl.Overlay name="Precipitation (NASA GIBS)">
            <WMSTileLayer
              url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi"
              layers="IMERG_Precipitation_Rate"
              format="image/png"
              transparent={true}
              attribution="NASA GIBS"
              opacity={0.6}
            />
          </LayersControl.Overlay>
          <LayersControl.Overlay name="Vegetation Index (NDVI)">
            <WMSTileLayer
              url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi"
              layers="MODIS_Terra_NDVI_8Day"
              format="image/png"
              transparent={true}
              attribution="NASA GIBS"
              opacity={0.5}
              time={new Date(Date.now() - 8 * 86400000).toISOString().split('T')[0]}
            />
          </LayersControl.Overlay>
          <LayersControl.Overlay name="Land Surface Temp (LST)">
            <WMSTileLayer
              url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi"
              layers="MODIS_Terra_Land_Surface_Temp_Day"
              format="image/png"
              transparent={true}
              attribution="NASA GIBS"
              opacity={0.5}
              time={new Date(Date.now() - 2 * 86400000).toISOString().split('T')[0]}
            />
          </LayersControl.Overlay>
          <LayersControl.Overlay name="Aerosol Optical Depth">
            <WMSTileLayer
              url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi"
              layers="MODIS_Terra_Aerosol"
              format="image/png"
              transparent={true}
              attribution="NASA GIBS"
              opacity={0.5}
              time={new Date(Date.now() - 2 * 86400000).toISOString().split('T')[0]}
            />
          </LayersControl.Overlay>
          <LayersControl.Overlay name="Soil Moisture (Flood Proxy)">
            <WMSTileLayer
              url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi"
              layers="SMAP_L4_Analyzed_Surface_Soil_Moisture"
              format="image/png"
              transparent={true}
              attribution="NASA GIBS"
              opacity={0.5}
              time={new Date(Date.now() - 2 * 86400000).toISOString().split('T')[0]}
            />
          </LayersControl.Overlay>
        </LayersControl>
        
        <MapViewRecenter selectedCell={selectedCell} />

        {(gridCells || []).map(cell => {
          const lat = cell.lat;
          const lon = cell.lon;
          
          const risk     = riskByCell[cell.cell_id] || 'NONE';
          const fill     = RISK_FILLS[risk];
          const opacity  = RISK_OPACITY[risk];
          const isSelected = selectedCell?.cell_id === cell.cell_id;

          const latMin = cell.lat_min !== undefined ? cell.lat_min : cell.lat - 1.25;
          const latMax = cell.lat_max !== undefined ? cell.lat_max : cell.lat + 1.25;
          const lonMin = cell.lon_min !== undefined ? cell.lon_min : cell.lon - 1.25;
          const lonMax = cell.lon_max !== undefined ? cell.lon_max : cell.lon + 1.25;

          return (
            <Rectangle
              key={cell.cell_id}
              bounds={[[latMin, lonMin], [latMax, lonMax]]}
              pathOptions={{
                color: isSelected ? '#00FFFF' : ((risk === 'NONE' || risk === 'LOW') ? 'rgba(255,255,255,0.1)' : fill),
                weight: isSelected ? 2 : ((risk === 'NONE' || risk === 'LOW') ? 0.5 : 1.5),
                fillColor: fill,
                fillOpacity: isSelected ? 0.6 : ((risk === 'NONE' || risk === 'LOW') ? 0.0 : opacity),
                opacity: isSelected ? 1 : ((risk === 'NONE' || risk === 'LOW') ? 0.1 : 0.8),
                dashArray: isSelected ? '4 4' : ''
              }}
              eventHandlers={{
                click: () => onCellClick && onCellClick(cell, risk),
                mouseover: (e) => {
                  if (!isSelected) {
                    e.target.setStyle({ weight: 2, opacity: 0.8, color: '#00FFFF', fillOpacity: 0.1 });
                  }
                },
                mouseout: (e) => {
                  if (!isSelected) {
                    e.target.setStyle({
                      weight: (risk === 'NONE' || risk === 'LOW') ? 0.5 : 1.5,
                      opacity: (risk === 'NONE' || risk === 'LOW') ? 0.1 : 0.8,
                      color: (risk === 'NONE' || risk === 'LOW') ? 'rgba(255,255,255,0.1)' : fill,
                      fillOpacity: (risk === 'NONE' || risk === 'LOW') ? 0.0 : opacity
                    });
                  }
                }
              }}
            >
              <Tooltip direction="top" opacity={0.9}>
                <div style={{ fontFamily: 'var(--font-sans)', fontSize: '12px' }}>
                  <strong>{cell.name}</strong><br/>
                  <span style={{ color: fill, fontWeight: 600 }}>{risk !== 'NONE' ? risk : 'NO ACTIVE THREATS'}</span>
                </div>
              </Tooltip>
            </Rectangle>
          );
        })}
      </MapContainer>
    </div>
  );
}
