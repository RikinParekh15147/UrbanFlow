import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAnalytics, useDataset } from '../../app/data-context';
import { api } from '../../lib/api';
import { Chart, bars, demandLine, type Option } from '../../components/chart';
import { Panel, QueryState, Title, Empty } from '../../components/panels';
import { number } from '../../lib/utils';
import { calendarDays, comparisonDefault, dailyAverage } from './comparison';
import './comparison.css';

export default function DemandPage() {
  const query = useAnalytics('demand-daily', api.daily);
  const hourly = useAnalytics('demand-hourly', api.hourly);
  const { start, end, filters, update, run_id } = useDataset();
  const [baseline, setBaseline] = useState<{ start: string; end: string } | null>(null);
  const selectedStart = filters.start_date ?? start, selectedEnd = filters.end_date ?? end;
  const defaults = start && selectedStart && selectedEnd ? comparisonDefault(selectedStart, selectedEnd, start) : { start: '', end: '' };
  const comparisonDates = baseline ?? defaults;
  const invalidRange = !comparisonDates.start || !comparisonDates.end || comparisonDates.start < start || comparisonDates.end > end || comparisonDates.start > comparisonDates.end;
  const comparisonFilters = { ...filters, start_date: comparisonDates.start, end_date: comparisonDates.end };
  const baselineQuery = useQuery({ queryKey: ['demand-comparison', comparisonFilters], queryFn: ({ signal }) => api.daily(comparisonFilters, signal), enabled: !!run_id && !invalidRange, staleTime: 60_000 });
  const rows = query.data?.data ?? [];
  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const totals = Array(7).fill(0) as number[], days = Array(7).fill(0) as number[];
  rows.forEach(row => { const d = (new Date(`${row.date}T12:00:00`).getDay() + 6) % 7; totals[d] += row.trip_count; days[d]++; });
  const weekdayOption = bars(weekdays, totals.map((n, i) => days[i] ? Math.round(n / days[i]) : null));
  const h = hourly.data?.data ?? [];
  const peak = [...h].sort((a,b) => b.trip_count-a.trip_count)[0];
  const average = dailyAverage(rows, selectedStart, selectedEnd);
  const baselineAverage = baselineQuery.data ? dailyAverage(baselineQuery.data.data, comparisonDates.start, comparisonDates.end) : null;
  const change = baselineAverage && average != null ? (average / baselineAverage - 1) * 100 : null;
  const comparison: Option = bars(['Selected dates', 'Comparison dates'], [average, baselineAverage]);
  return <>
    <Title title="Demand intelligence" description="Find the hours, days, and places that shape taxi demand." rows={rows} file="urbanflow-demand.csv" />
    <QueryState loading={query.isPending || hourly.isPending} error={query.error ?? hourly.error} retry={() => { query.refetch(); hourly.refetch(); }} />
    {query.data && hourly.data && <>
      {!rows.length && <Empty />}
      <div className="insight-banner"><div><strong>{peak ? `${String(peak.hour).padStart(2, '0')}:00` : '—'}</strong><span>is the busiest pickup hour in this selection.</span></div><p>{number(average)} pickups per calendar day on average.</p></div>
      <div className="two-columns"><Panel title="Demand through the day" detail="Pickups summed by local hour across selected dates"><Chart option={bars(h.map(r => `${String(r.hour).padStart(2,'0')}:00`), h.map(r => r.trip_count))} label="Hourly taxi pickup demand" /></Panel><Panel title="The weekly pattern" detail="Average pickups per observed weekday"><Chart option={weekdayOption} label="Average daily pickup demand by weekday" /></Panel></div>
      <Panel title="Daily demand" detail="Use the date filters to inspect and compare periods" action={<button className="text-button" onClick={() => update({ start_date: start, end_date: end })}>Full dataset period</button>}><Chart option={demandLine(rows)} label="Daily pickup trend" height={300} /></Panel>
      <div className="two-columns"><Panel title="Compare date ranges" detail="Average daily pickups, using the same pickup-zone, borough, and dataset version">
        <div className="comparison-controls"><label>Compare from<input type="date" min={start} max={end} value={comparisonDates.start} onChange={e => setBaseline({ ...comparisonDates, start: e.target.value })} aria-describedby="comparison-summary" /></label><label>Compare through<input type="date" min={start} max={end} value={comparisonDates.end} onChange={e => setBaseline({ ...comparisonDates, end: e.target.value })} aria-describedby="comparison-summary" /></label></div>
        {invalidRange ? <p className="comparison-summary" role="alert">Choose dates from {start} through {end}, with the end on or after the start.</p> : <>
          <QueryState loading={baselineQuery.isPending} error={baselineQuery.error} retry={() => { baselineQuery.refetch(); }} />
          {baselineQuery.data && !baselineQuery.error && <><Chart option={comparison} label={`Average daily pickups: ${selectedStart} through ${selectedEnd} versus ${comparisonDates.start} through ${comparisonDates.end}`} /><p className="comparison-summary" id="comparison-summary">Selected: {selectedStart}–{selectedEnd} ({calendarDays(selectedStart, selectedEnd)} days). Comparison: {comparisonDates.start}–{comparisonDates.end} ({calendarDays(comparisonDates.start, comparisonDates.end)} days). {change != null ? `${number(Math.abs(change), 1)}% ${change >= 0 ? 'higher' : 'lower'} average daily demand.` : 'Percentage change is unavailable when the comparison has no pickups.'} All calendar days count, including days with zero pickups. Ranges may overlap.</p></>}
        </>}
      </Panel><Panel title="Selected daily observations" detail={`${filters.start_date} to ${filters.end_date}`}><div className="table-scroll limited-table"><table><thead><tr><th>Date</th><th className="numeric">Pickups</th></tr></thead><tbody>{rows.map(r => <tr key={r.date}><td>{r.date}</td><td className="numeric">{number(r.trip_count)}</td></tr>)}</tbody></table></div></Panel></div>
    </>}
  </>;
}
