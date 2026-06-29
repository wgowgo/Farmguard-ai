'use client';

import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Circle, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const fieldIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const pestIcon = L.divIcon({
  className: '',
  html: '<div style="background:#ef4444;width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.3)"></div>',
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});

export interface MapLayers {
  field: { lat: number; lng: number };
  circles: {
    center: { lat: number; lng: number };
    radius_m: number;
    pest_name: string;
    intensity?: number;
    distance_km: number;
  }[];
  pest_markers: {
    lat: number; lng: number;
    pest_name: string;
    value?: number;
    distance_km?: number;
  }[];
}

export default function RiskMapView({ layers }: { layers: MapLayers }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return <div className="h-72 bg-surface-muted rounded-2xl animate-pulse" />;

  const { field, circles, pest_markers } = layers;
  const center: [number, number] = [field.lat, field.lng];

  return (
    <MapContainer center={center} zoom={14} className="h-72 w-full rounded-2xl z-0 overflow-hidden border border-border">
      <TileLayer
        attribution='&copy; OSM'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker position={center} icon={fieldIcon}>
        <Popup>내 필지</Popup>
      </Marker>
      {circles.map((c, i) => (
        <Circle
          key={`c-${i}`}
          center={[c.center.lat, c.center.lng]}
          radius={c.radius_m}
          pathOptions={{
            color: '#f97316',
            fillColor: '#fb923c',
            fillOpacity: 0.08,
            weight: 1.5,
            dashArray: '6 4',
          }}
        >
          <Popup>
            {c.pest_name}, {c.distance_km}km 이내
            {c.intensity != null && ` (강도 ${c.intensity})`}
          </Popup>
        </Circle>
      ))}
      {pest_markers.map((m, i) => (
        <Marker key={`m-${i}`} position={[m.lat, m.lng]} icon={pestIcon}>
          <Popup>
            <strong>{m.pest_name}</strong><br />
            약 {m.distance_km}km, 강도 {m.value ?? '-'}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
