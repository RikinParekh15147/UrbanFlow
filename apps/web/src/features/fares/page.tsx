import { useAnalytics, useDataset } from '../../app/data-context';
import { api } from '../../lib/api';
import { Chart, bars, colors } from '../../components/chart';
import { Panel, QueryState, Title, ZoneTable } from '../../components/panels';
import { dollars, number } from '../../lib/utils';

function TotalMoney({ value }: { value: number | null | undefined }) {
  const exact = dollars(value);
  const short = value == null ? exact : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1 }).format(value);
  return <><dd title={exact} aria-label={exact}>{short}</dd><details><summary>Exact USD amount</summary><span style={{ overflowWrap: 'anywhere' }}>{exact}</span></details></>;
}

export default function FaresPage() {
  const query = useAnalytics('fares', api.fares);
  const { update } = useDataset();
  const data = query.data;
  return <>
    <Title title="Fare analytics" description="Explore base fares, payment patterns, tips, and recorded surcharges. CSV contains pickup-zone fare summaries." rows={data?.zones} file="urbanflow-fare-zones.csv" />
    <QueryState loading={query.isPending} error={query.error} retry={() => query.refetch()} />
    {data && <>
      <dl className="kpi-strip"><div><dt>Recorded base fares</dt><TotalMoney value={data.metrics.total_fare} /><span>Excludes tips, tolls, and surcharges</span></div><div><dt>Average base fare</dt><dd>{dollars(data.metrics.avg_fare)}</dd><span>{number(data.metrics.fare_count)} eligible records</span></div><div><dt>Base fare per mile</dt><dd>{dollars(data.fare_per_mile)}</dd><span>Fare sum / corresponding positive miles</span></div><div><dt>Recorded tips</dt><TotalMoney value={data.total_tips} /><span>Cash tips are not fully represented</span></div></dl>
      <div className="two-columns"><Panel title="Fare distribution" detail="Eligible base fares · USD · upper bounds excluded except final bin"><Chart option={bars(data.distribution.map(r => r.label), data.distribution.map(r => r.trip_count))} label="Taxi base-fare distribution" /></Panel><Panel title="How passengers paid" detail="Payment types for all demand-eligible trips"><Chart option={{ tooltip: { trigger: 'item' }, legend: { bottom: 0, type: 'scroll' }, series: [{ type: 'pie', radius: ['43%', '68%'], center: ['50%', '43%'], label: { show: false }, color: colors, data: data.payment_types.filter(r => r.trip_count > 0).map(r => ({ name: r.label, value: r.trip_count })) }] }} label="Taxi payment type breakdown" /></Panel></div>
      <Panel title="Fare patterns by pickup zone" detail="Top 20 pickup zones by trip volume"><ZoneTable rows={data.zones} onSelect={id => update({ zone_id: id })} /></Panel>
      <div className="method-note standalone">Eligible base fares range from $0 to $1,000. Negative and refund-like fares are excluded from fare metrics, while their pickups may remain in demand totals. Recorded congestion charges total {dollars(data.congestion_fees)}; these charges do not establish measured road congestion.</div>
    </>}
  </>;
}
