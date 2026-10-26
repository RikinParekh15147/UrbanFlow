import { createContext, useContext, useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, type Filters } from '../lib/api';

function useDatasetState() {
  const status = useQuery({ queryKey: ['status'], queryFn: ({ signal }) => api.status(signal), staleTime: Infinity });
  const manifest = status.data?.manifest;
  const run_id = status.data?.run_id ?? undefined;
  const zones = useQuery({ queryKey: ['zones', run_id], queryFn: ({ signal }) => api.zones(run_id, signal), enabled: !!run_id, staleTime: Infinity });
  const [selection, setSelection] = useState<Filters>({});
  const start = typeof manifest?.start_date === 'string' ? manifest.start_date : '';
  const end = typeof manifest?.end_date === 'string' ? manifest.end_date : '';
  const filters: Filters = { start_date: start || undefined, end_date: end || undefined, ...selection, run_id };
  const update = (patch: Partial<Filters>) => setSelection(s => ({ ...s, ...patch }));
  const reset = () => setSelection({});
  return { status, zones: zones.data?.data ?? [], filters, update, reset, start, end, run_id, manifest };
}
type State = ReturnType<typeof useDatasetState>;
const DataContext = createContext<State | null>(null);
export function DataProvider({ children }: { children: ReactNode }) {
  const state = useDatasetState();
  return <DataContext.Provider value={state}>{children}</DataContext.Provider>;
}
export function useDataset() {
  const state = useContext(DataContext);
  if (!state) throw new Error('Dataset provider is missing');
  return state;
}
export function useAnalytics<T>(name: string, load: (filters: Filters, signal: AbortSignal) => Promise<T>) {
  const { filters, run_id } = useDataset();
  return useQuery({ queryKey: [name, filters], queryFn: ({ signal }) => load(filters, signal), enabled: !!run_id, staleTime: 60_000 });
}
