import type { ReactNode } from 'react';
import { AlertCircle, Download, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { dollars, downloadCsv, number } from '../lib/utils';
import type { Metrics, Point } from '../lib/api';
import { useDataset } from '../app/data-context';

export function Panel({ title, detail, children, className = '', action }: { title: string; detail?: string; children: ReactNode; className?: string; action?: ReactNode }) {
  return <section className={`panel ${className}`}><div className="panel-heading"><div><h2>{title}</h2>{detail && <p>{detail}</p>}</div>{action}</div>{children}</section>;
}
export function Title({ title, description, rows, file, datasetWide = false }: { title: string; description: string; rows?: object[]; file?: string; datasetWide?: boolean }) {
  const { filters, run_id } = useDataset();
  const exportRows = () => downloadCsv(file ?? 'urbanflow.csv', (rows ?? []).map(row => ({ run_id, scope: datasetWide ? 'dataset' : 'trip_selection', ...(datasetWide ? {} : { filter_start: filters.start_date, filter_end: filters.end_date, filter_borough: filters.borough, filter_zone: filters.zone_id }), ...row })));
  return <div className="page-title"><div><h1>{title}</h1><p>{description}</p></div>{rows && <Button variant="outline" disabled={!rows.length} onClick={exportRows}><Download size={16} />Export CSV</Button>}</div>;
}
export function QueryState({ loading, error, retry }: { loading: boolean; error: Error | null; retry: () => void }) {
  if (error) return <div className="query-state error" role="alert"><AlertCircle size={26} /><h2>We couldn’t load this analysis</h2><p>{error.message}</p><Button variant="outline" onClick={retry}><RefreshCw size={16} />Retry analysis</Button></div>;
  if (loading) return <div className="query-state" role="status"><div className="loading-mark" /><h2>Reading the published dataset</h2><p>Loading the selected analysis…</p></div>;
  return null;
}
export function Empty() { return <div className="empty"><h3>No trips in this selection</h3><p>Try another zone or a wider date range.</p></div>; }
export function Kpis({ metrics }: { metrics: Metrics }) {
  const items = [
    ['Taxi trips', number(metrics.trip_count), 'Recorded pickups in your selection'],
    ['Average fare', dollars(metrics.avg_fare), 'Base fare · eligible fare records'],
    ['Average duration', `${number(metrics.avg_duration_min, 1)} min`, 'Eligible trips · 1–240 minutes'],
    ['Average distance', `${number(metrics.avg_distance_miles, 2)} mi`, 'Usable recorded distances'],
  ];
  return <dl className="kpi-strip">{items.map(([label, value, detail]) => <div key={label}><dt>{label}</dt><dd>{value}</dd><span>{detail}</span></div>)}</dl>;
}
export function ZoneTable({ rows, onSelect }: { rows: Point[]; onSelect?: (id: number) => void }) {
  return <div className="table-scroll"><table><thead><tr><th>Pickup zone</th><th>Borough</th><th className="numeric">Trips</th><th className="numeric">Avg. fare</th><th className="numeric">Duration</th></tr></thead><tbody>{rows.map(r => <tr key={r.zone_id}><td>{onSelect ? <button className="text-button" onClick={() => r.zone_id && onSelect(r.zone_id)}>{r.name}</button> : r.name}</td><td>{r.borough}</td><td className="numeric">{number(r.trip_count)}</td><td className="numeric">{dollars(r.avg_fare)}</td><td className="numeric">{number(r.avg_duration_min, 1)} min</td></tr>)}</tbody></table>{!rows.length && <Empty />}</div>;
}
