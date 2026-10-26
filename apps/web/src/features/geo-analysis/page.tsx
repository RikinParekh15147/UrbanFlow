import { useAnalytics, useDataset } from '../../app/data-context';
import { api } from '../../lib/api';
import { ZoneMap } from '../../components/zone-map';
import { Panel, QueryState, Title, ZoneTable } from '../../components/panels';
import { number } from '../../lib/utils';

export default function GeographyPage() {
  const query = useAnalytics('geography', api.geography);
  const overview = useAnalytics('overview', api.overview);
  const routes = useAnalytics('routes', api.routes);
  const { update, filters, zones } = useDataset();
  const selected = zones.find(z => z.zone_id === filters.zone_id);
  return <>
    <Title title="Geographic analytics" description="Explore the city’s actual taxi zones and the journeys connecting them." rows={overview.data?.busiest_zones} file="urbanflow-zones.csv" />
    <QueryState loading={query.isPending} error={query.error} retry={() => query.refetch()} />
    {query.data && <div className="geography-grid"><Panel title="NYC pickup demand" detail="Select a polygon or use the zone list. Wheel to zoom; drag to explore.">
      <ZoneMap large data={query.data} selected={filters.zone_id} onSelect={id => update({ zone_id: id })} />
    </Panel><Panel title={selected?.name ?? 'Explore a taxi zone'} detail={selected?.borough ?? 'Choose a zone to focus every analysis'}>
      {selected ? <div className="selected-zone"><span className="zone-id">TLC zone {selected.zone_id}</span><strong>{number(overview.data?.metrics.trip_count)}</strong><p>pickups in the selected period</p><p>Taxi-zone boundaries identify pickup areas, not individual roads or accident locations.</p><button className="text-button" onClick={() => update({ zone_id: undefined })}>Clear selected zone</button></div> : <div className="zone-directory">{(overview.data?.busiest_zones ?? []).map(z => <button key={z.zone_id} onClick={() => update({ zone_id: z.zone_id })}><strong>{z.name}</strong><span>{number(z.trip_count)} trips</span></button>)}</div>}
      <div className="method-note">Unknown and outside-NYC location IDs remain in demand totals where present; the map shows only zones with official geometry.</div>
    </Panel></div>}
    <Panel title="Top route connections" detail="Origin–destination pairs retained among the top 100 routes each day; this is a limited route sample.">
      <QueryState loading={routes.isPending} error={routes.error} retry={() => routes.refetch()} />
      {routes.data && <div className="table-scroll"><table><thead><tr><th>Pickup zone</th><th>Drop-off zone</th><th className="numeric">Trips in retained routes</th></tr></thead><tbody>{routes.data.data.map(r => <tr key={`${r.pickup_zone}-${r.dropoff_zone}`}><td>{r.pickup_name}</td><td>{r.dropoff_name}</td><td className="numeric">{number(r.trip_count)}</td></tr>)}</tbody></table>{!routes.data.data.length && <p className="method-note">No retained top routes match this selection. This does not establish that no trips occurred.</p>}</div>}
    </Panel>
    {overview.data && <Panel title="Zone observations" detail="Select a row to apply its zone across all sections"><ZoneTable rows={overview.data.busiest_zones} onSelect={id => update({ zone_id: id })} /></Panel>}
  </>;
}
