import { Link } from 'react-router-dom';
import { ArrowUpRight, ArrowRight } from 'lucide-react';
import { useAnalytics, useDataset } from '../../app/data-context';
import { api } from '../../lib/api';
import { Chart, demandLine } from '../../components/chart';
import { ZoneMap } from '../../components/zone-map';
import { Kpis, Panel, QueryState, Title, ZoneTable, Empty } from '../../components/panels';
import { compact, number } from '../../lib/utils';

export default function OverviewPage() {
  const { update, filters } = useDataset();
  const query = useAnalytics('overview', api.overview);
  const geography = useAnalytics('geography', api.geography);
  const data = query.data;
  return <>
    <Title title="City overview" description="A clearer view of how New York moves, one taxi trip at a time." rows={data?.daily} file="urbanflow-daily-demand.csv" />
    <QueryState loading={query.isPending} error={query.error} retry={() => query.refetch()} />
    {data && <>
      <Kpis metrics={data.metrics} />
      {!data.metrics.trip_count && <Empty />}
      <div className="overview-grid">
        <Panel title="The rhythm of the city" detail="Daily pickups · NYC local time" action={<Link className="panel-link" to="/demand">Explore demand <ArrowUpRight size={16} /></Link>}>
          <Chart option={demandLine(data.daily)} label="Daily taxi pickups for the selected dates" height={270} />
          <div className="chart-foot"><span>{data.meta.start_date} to {data.meta.end_date}</span><span>{number(data.metrics.trip_count)} recorded trips</span></div>
        </Panel>
        <Panel title="Across the boroughs" detail="Share of pickups in your selection">
          <div className="borough-list">{data.boroughs.map((row, index) => <div key={row.borough} className="borough-row"><span className="rank">{index + 1}</span><div className="borough-measure"><div><strong>{row.borough}</strong><span>{compact(row.trip_count)} <small>{number(row.trip_count / Math.max(1, data.metrics.trip_count) * 100, 1)}%</small></span></div><div className="track"><i style={{ width: `${row.trip_count / Math.max(1, data.metrics.trip_count) * 100}%` }} /></div></div></div>)}</div>
        </Panel>
        <Panel title="Where journeys begin" detail="Pickup demand across official TLC taxi zones" action={<Link className="panel-link" to="/geography">Open map <ArrowUpRight size={16} /></Link>}>
          {geography.data ? <ZoneMap data={geography.data} selected={filters.zone_id} onSelect={id => update({ zone_id: id })} /> : <QueryState loading={geography.isPending} error={geography.error} retry={() => geography.refetch()} />}
        </Panel>
        <Panel title="Busiest pickup zones" detail="Ranked by trips · select a zone to explore">
          <ol className="zone-ranking">{data.busiest_zones.slice(0, 7).map((row, index) => <li key={row.zone_id}><button onClick={() => update({ zone_id: row.zone_id })}><span className="rank">{String(index + 1).padStart(2, '0')}</span><span className="zone-label"><strong>{row.name}</strong><small>{row.borough}</small></span><span className="zone-count">{compact(row.trip_count)}</span><ArrowRight size={15} /></button></li>)}</ol>
          <Link className="list-footer" to="/geography">Explore all pickup zones <ArrowRight size={16} /></Link>
        </Panel>
      </div>
      <Panel title="Your selection, in detail" detail="Weighted averages use the eligible records for each metric"><ZoneTable rows={data.busiest_zones} onSelect={id => update({ zone_id: id })} /></Panel>
    </>}
  </>;
}
