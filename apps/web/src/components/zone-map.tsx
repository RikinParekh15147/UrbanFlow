import { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import type { FeatureCollection } from 'geojson';
import type { Geography } from '../lib/api';
import { compact } from '../lib/utils';

// Vite must emit the worker as a separate bundled asset for production/Electron.
maplibregl.setWorkerUrl(workerUrl);

const palette = ['#dce8cb', '#acc995', '#78a575', '#477d57', '#1d523e'];
function fillExpression(maximum: number): maplibregl.ExpressionSpecification {
  const scale = Math.sqrt(Math.max(1, maximum));
  return ['interpolate', ['linear'], ['sqrt', ['coalesce', ['get', 'trip_count'], 0]],
    0, '#eef1e5', scale * .2, palette[0], scale * .4, palette[1],
    scale * .6, palette[2], scale * .8, palette[3], scale, palette[4]];
}
export function ZoneMap({ data, onSelect, selected, large = false }: { data: Geography; onSelect: (id: number) => void; selected?: number | null; large?: boolean }) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const callback = useRef(onSelect); callback.current = onSelect;
  const current = useRef(data); current.current = data;
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');
  const maximum = Math.max(0, ...data.features.map(f => Number(f.properties?.trip_count ?? 0)));
  useEffect(() => {
    if (!container.current) return;
    let instance: maplibregl.Map;
    try {
      instance = new maplibregl.Map({ container: container.current, attributionControl: false,
        style: { version: 8, sources: {}, layers: [{ id: 'water', type: 'background', paint: { 'background-color': '#e7efed' } }] },
        bounds: [[-74.27, 40.49], [-73.68, 40.94]], fitBoundsOptions: { padding: 18 }, maxZoom: 15, minZoom: 8 });
    } catch { setState('error'); return; }
    map.current = instance;
    instance.on('error', () => setState('error'));
    instance.on('idle', () => {
      if (instance.getLayer('zones-fill') && instance.isSourceLoaded('zones') &&
        instance.queryRenderedFeatures({ layers: ['zones-fill'] }).length > 0) setState('ready');
    });
    instance.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    instance.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: 'NYC TLC taxi zones' }));
    const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12 });
    instance.on('load', () => {
      instance.addSource('zones', { type: 'geojson', data: current.current as unknown as FeatureCollection, promoteId: 'zone_id' });
      const max = Math.max(0, ...current.current.features.map(f => Number(f.properties?.trip_count ?? 0)));
      instance.addLayer({ id: 'zones-fill', type: 'fill', source: 'zones', paint: {
        'fill-color': fillExpression(max),
        'fill-opacity': ['case', ['==', ['get', 'in_selection'], false], .22, .93],
      } });
      instance.addLayer({ id: 'zones-outline', type: 'line', source: 'zones', paint: { 'line-color': '#ffffff', 'line-width': .5 } });
      instance.addLayer({ id: 'zones-selected', type: 'line', source: 'zones', filter: ['==', ['get', 'zone_id'], -1], paint: { 'line-color': '#bf612b', 'line-width': 2.5 } });
      instance.on('mousemove', 'zones-fill', event => {
        const properties = event.features?.[0]?.properties;
        if (!properties) return;
        instance.getCanvas().style.cursor = 'pointer';
        const label = document.createElement('div');
        const title = document.createElement('strong'); title.textContent = String(properties.name);
        const detail = document.createElement('div'); detail.textContent = properties.in_selection === false ? 'Outside the current filter selection' : `${compact(Number(properties.trip_count))} pickups · ${properties.borough}`;
        label.append(title, detail); popup.setLngLat(event.lngLat).setDOMContent(label).addTo(instance);
      });
      instance.on('mouseleave', 'zones-fill', () => { instance.getCanvas().style.cursor = ''; popup.remove(); });
      instance.on('click', 'zones-fill', event => {
        const id = Number(event.features?.[0]?.properties?.zone_id);
        if (id) callback.current(id);
      });
    });
    const observer = new ResizeObserver(() => instance.resize()); observer.observe(container.current);
    return () => { observer.disconnect(); popup.remove(); instance.remove(); map.current = null; };
  }, []);
  useEffect(() => {
    const instance = map.current;
    if (!instance) return;
    const update = () => {
      (instance.getSource('zones') as maplibregl.GeoJSONSource | undefined)?.setData(data as unknown as FeatureCollection);
      if (instance.getLayer('zones-fill')) instance.setPaintProperty('zones-fill', 'fill-color', fillExpression(maximum));
      if (instance.getLayer('zones-selected')) instance.setFilter('zones-selected', ['==', ['get', 'zone_id'], selected ?? -1]);
    };
    if (instance.isStyleLoaded()) update(); else instance.once('load', update);
    return () => { instance.off('load', update); };
  }, [data, selected, maximum]);
  return <div className={`map-wrap ${large ? 'map-large' : ''}`} data-map-state={state}>
    <div ref={container} className="zone-map" aria-label="Interactive NYC taxi-zone pickup map. Select a zone here or in the zone list." />
    {state === 'loading' && <div className="map-error" role="status">Loading taxi-zone boundaries…</div>}
    {state === 'error' && <div className="map-error" role="alert">Map rendering is unavailable. Explore the same zones in the list, or reopen this section to retry.</div>}
    <div className="map-location">New York City<span>Taxi pickup zones</span></div>
    <div className="map-legend"><span>Fewer pickups</span><div>{palette.map(color => <i key={color} style={{ background: color }} />)}</div><span>{compact(maximum)} max</span></div>
  </div>;
}
