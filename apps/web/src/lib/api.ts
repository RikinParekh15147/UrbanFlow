import createClient from 'openapi-fetch';
import type { paths, components } from './schema';

const client = createClient<paths>();
export type Filters = NonNullable<paths['/api/v1/overview']['get']['parameters']['query']>;
export type Point = components['schemas']['Point'];
export type Metrics = components['schemas']['Metrics'];
export type Zone = components['schemas']['Zone'];
export type Geography = components['schemas']['GeographyResponse'];
function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.data !== undefined) return result.data;
  const problem = result.error as { error?: { message?: string } } | undefined;
  throw new Error(problem?.error?.message ?? `The request failed (${result.response.status}). Please retry.`);
}
export const api = {
  status: async (signal?: AbortSignal) => unwrap(await client.GET('/api/v1/datasets/status', { signal })),
  zones: async (run_id?: string, signal?: AbortSignal) => unwrap(await client.GET('/api/v1/zones', { params: { query: { run_id } }, signal })),
  overview: async (filters: Filters, signal?: AbortSignal) => unwrap(await client.GET('/api/v1/overview', { params: { query: filters }, signal })),
  daily: async (filters: Filters, signal?: AbortSignal) => unwrap(await client.GET('/api/v1/demand/daily', { params: { query: filters }, signal })),
  hourly: async (filters: Filters, signal?: AbortSignal) => unwrap(await client.GET('/api/v1/demand/hourly', { params: { query: filters }, signal })),
  geography: async (filters: Filters, signal?: AbortSignal) => unwrap(await client.GET('/api/v1/geography/heatmap', { params: { query: filters }, signal })),
  routes: async (filters: Filters, signal?: AbortSignal) => unwrap(await client.GET('/api/v1/routes/top', { params: { query: filters }, signal })),
  efficiency: async (filters: Filters, group_by: 'zone' | 'hour', signal?: AbortSignal) => unwrap(await client.GET('/api/v1/trips/efficiency', { params: { query: { ...filters, group_by } }, signal })),
  fares: async (filters: Filters, signal?: AbortSignal) => unwrap(await client.GET('/api/v1/fares/summary', { params: { query: filters }, signal })),
  benchmarks: async (run_id?: string, signal?: AbortSignal) => unwrap(await client.GET('/api/v1/benchmarks', { params: { query: { run_id } }, signal })),
};
