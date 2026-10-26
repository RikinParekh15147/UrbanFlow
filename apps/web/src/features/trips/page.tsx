import { useAnalytics } from '../../app/data-context';
import { api } from '../../lib/api';
import { Chart, bars } from '../../components/chart';
import { Panel, QueryState, Title, Empty } from '../../components/panels';
import { number } from '../../lib/utils';

export default function TripsPage() {
  const query = useAnalytics('efficiency-zones', (f,s) => api.efficiency(f, 'zone', s));
  const hours = useAnalytics('efficiency-hours', (f,s) => api.efficiency(f, 'hour', s));
  const rows = query.data?.data ?? [];
  const hourly = hours.data?.data ?? [];
  return <>
    <Title title="Trip efficiency" description="Understand journey duration, distance, and estimated travel speed." rows={rows} file="urbanflow-efficiency.csv" />
    <div className="method-note standalone">Speed is total eligible miles divided by total eligible travel hours. These taxi-trip estimates do not measure road congestion.</div>
    <QueryState loading={query.isPending || hours.isPending} error={query.error ?? hours.error} retry={() => { query.refetch(); hours.refetch(); }} />
    {query.data && hours.data && <>
      {!rows.length && <Empty />}
      <div className="two-columns"><Panel title="Travel speed by pickup hour" detail="Total eligible miles / total eligible travel hours · mph"><Chart option={bars(hourly.map(r => `${String(r.hour).padStart(2,'0')}:00`), hourly.map(r => r.speed_mph))} label="Estimated taxi travel speed by pickup hour in miles per hour" /></Panel><Panel title="Typical journey duration" detail="Average eligible trip duration · minutes"><Chart option={bars(hourly.map(r => `${String(r.hour).padStart(2,'0')}:00`), hourly.map(r => r.avg_duration_min))} label="Average taxi trip duration by hour in minutes" /></Panel></div>
      <Panel title="Zone efficiency comparisons" detail="Top 50 pickup zones by trip volume; eligible observations shown separately"><div className="table-scroll"><table><thead><tr><th>Pickup zone</th><th>Borough</th><th className="numeric">Trips</th><th className="numeric">Eligible</th><th className="numeric">Duration</th><th className="numeric">Speed</th></tr></thead><tbody>{rows.map(r => <tr key={r.zone_id}><td>{r.name}</td><td>{r.borough}</td><td className="numeric">{number(r.trip_count)}</td><td className="numeric">{number(r.efficiency_count)}</td><td className="numeric">{number(r.avg_duration_min, 1)} min</td><td className="numeric">{number(r.speed_mph, 1)} mph</td></tr>)}</tbody></table></div></Panel>
      <Panel title="What is included?" detail="Eligibility is specific to each metric"><p className="explanation">Efficiency calculations use trips with positive distance up to 100 miles, duration from 1 to 240 minutes, and an estimated speed up to 100 mph. A trip outside these bounds may still count toward pickup demand. Null values mean there are no eligible observations for that measurement.</p></Panel>
    </>}
  </>;
}
