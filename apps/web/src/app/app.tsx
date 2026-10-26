import { lazy, Suspense, useEffect, useState } from 'react';
import { NavLink, Route, Routes, useLocation, Link } from 'react-router-dom';
import { Activity, ArrowUpRight, BookOpen, CalendarDays, ChartColumn, Database, FlaskConical, Gauge, LayoutDashboard, MapPinned, Route as RouteIcon, RotateCcw, X, Wallet } from 'lucide-react';
import { useDataset } from './data-context';
import { Button } from '../components/ui/button';
import { QueryState } from '../components/panels';

const Overview = lazy(() => import('../features/overview/page'));
const Demand = lazy(() => import('../features/demand/page'));
const Geography = lazy(() => import('../features/geo-analysis/page'));
const Trips = lazy(() => import('../features/trips/page'));
const Fares = lazy(() => import('../features/fares/page'));
const Benchmarks = lazy(() => import('../features/benchmarks/page'));
const DatasetModel = lazy(() => import('../features/dataset-model/page'));
const destinations = [
  { path: '/', label: 'City overview', icon: LayoutDashboard },
  { path: '/demand', label: 'Demand intelligence', icon: ChartColumn },
  { path: '/geography', label: 'Geographic analytics', icon: MapPinned },
  { path: '/trips', label: 'Trip efficiency', icon: Gauge },
  { path: '/fares', label: 'Fare analytics', icon: Wallet },
  { path: '/lab', label: 'Big Data Lab', icon: FlaskConical },
  { path: '/dataset-model', label: 'Dataset & Model', icon: BookOpen },
];

function Filters() {
  const { filters, update, reset, zones, start, end } = useDataset();
  const lab = ['/lab', '/dataset-model'].includes(useLocation().pathname);
  const [from, setFrom] = useState(filters.start_date ?? '');
  const [to, setTo] = useState(filters.end_date ?? '');
  useEffect(() => { setFrom(filters.start_date ?? ''); setTo(filters.end_date ?? ''); }, [filters.start_date, filters.end_date]);
  const valid = !!from && !!to && from <= to && from >= start && to <= end;
  const changed = from !== filters.start_date || to !== filters.end_date;
  const selected = zones.find(z => z.zone_id === filters.zone_id);
  return <div className="filters-area"><form className="filters" onSubmit={event => { event.preventDefault(); if (valid) update({ start_date: from, end_date: to }); }}>
    <div className="date-range"><CalendarDays size={17} /><label><span className="sr-only">Start date</span><input type="date" min={start} max={to || end} value={from} disabled={lab} onChange={e => setFrom(e.target.value)} required /></label><span className="date-separator">to</span><label><span className="sr-only">End date</span><input type="date" min={from || start} max={end} value={to} disabled={lab} onChange={e => setTo(e.target.value)} required /></label></div>
    {changed && <Button type="submit" disabled={!valid || lab}>Apply dates</Button>}
    <label className="select-label"><span className="sr-only">Borough</span><select value={filters.borough ?? ''} disabled={lab} onChange={e => update({ borough: e.target.value || undefined, zone_id: undefined })}><option value="">All boroughs</option>{[...new Set(zones.map(z => z.borough))].sort().map(b => <option key={b}>{b}</option>)}</select></label>
    <label className="select-label zone-select"><span className="sr-only">Pickup zone</span><select value={filters.zone_id ?? ''} disabled={lab} onChange={e => update({ zone_id: e.target.value ? Number(e.target.value) : undefined })}><option value="">All pickup zones</option>{zones.filter(z => !filters.borough || z.borough === filters.borough).map(z => <option key={z.zone_id} value={z.zone_id}>{z.name}</option>)}</select></label>
    <Button type="button" variant="ghost" disabled={lab} onClick={reset} aria-label="Reset all trip filters"><RotateCcw size={15} /><span>Reset</span></Button>
  </form>{lab ? <p className="filter-caption">Dataset-wide processing results · trip filters do not apply here.</p> : selected && <div className="selection-chip">Pickup zone: <strong>{selected.name}</strong><button aria-label="Clear selected pickup zone" onClick={() => update({ zone_id: undefined })}><X size={14} /></button></div>}</div>;
}

export default function App() {
  const { status, run_id, start, end } = useDataset();
  const location = useLocation();
  const current = destinations.find(d => d.path === location.pathname);
  return <div className="app-shell"><a className="skip-link" href="#main">Skip to analysis</a>
    <aside className="sidebar"><Link className="brand" to="/" aria-label="UrbanFlow home"><span className="brand-mark"><RouteIcon size={24} /></span><span>UrbanFlow<small>Urban mobility, understood.</small></span></Link>
      <div className="workspace-label"><span className="city-dot" />New York City<ArrowUpRight size={15} /></div>
      <nav aria-label="Analytics sections">{destinations.map(({ path, label, icon: Icon }) => <NavLink key={path} to={path} end={path === '/'}><Icon size={19} strokeWidth={1.7} /><span>{label}</span>{location.pathname === path && <span className="nav-active-dot" />}</NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="batch-symbol"><Activity size={21} /></div><strong>Big data. Real journeys.</strong><p>Historical NYC taxi records, transformed into a city perspective.</p><div className="sidebar-source"><span className="status-dot" />NYC TLC Yellow Taxi</div><span className="sidebar-small">Batch analytics · No live tracking</span></div>
    </aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb">Workspace<span>/</span><strong>{current?.label ?? 'UrbanFlow'}</strong></div><div className="source-badge"><span className="status-dot" /><Database size={14} />{status.data?.source === 'local_snapshot' ? 'Local snapshot' : 'MongoDB'}<span className="badge-divider" />{status.data?.status === 'published' ? 'Published dataset' : 'Connecting'}</div></header>
      <main id="main" tabIndex={-1}>
        <Filters />
        <QueryState loading={status.isPending} error={status.error} retry={() => status.refetch()} />
        {status.data?.status === 'not_published' && <div className="query-state"><Database size={30}/><h1>No dataset published yet</h1><p>Run the ETL and publishing jobs, then reload this workspace.</p><Button onClick={() => status.refetch()}>Check dataset</Button></div>}
        {!!run_id && <Suspense fallback={<QueryState loading error={null} retry={() => {}} />}><Routes><Route path="/" element={<Overview />} /><Route path="/demand" element={<Demand />} /><Route path="/geography" element={<Geography />} /><Route path="/trips" element={<Trips />} /><Route path="/fares" element={<Fares />} /><Route path="/lab" element={<Benchmarks />} /><Route path="/dataset-model" element={<DatasetModel />} /><Route path="*" element={<div className="query-state"><h1>Analysis not found</h1><Link to="/">Return to city overview</Link></div>} /></Routes></Suspense>}
        <footer className="workspace-footer"><span>NYC TLC Yellow Taxi · {start} to {end}</span><span>Dataset <code>{run_id ?? 'unavailable'}</code></span><span>Historical analysis · NYC local time</span></footer>
      </main>
    </div>
  </div>;
}
