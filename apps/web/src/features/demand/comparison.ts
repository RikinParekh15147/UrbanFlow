import type { Point } from '../../lib/api';

const DAY = 86_400_000;
const stamp = (date: string) => Date.parse(`${date}T00:00:00Z`);
export function calendarDays(start: string, end: string) {
  return Math.max(0, Math.round((stamp(end) - stamp(start)) / DAY) + 1);
}
export function comparisonDefault(start: string, end: string, availableStart: string) {
  const days = calendarDays(start, end);
  const previousStart = stamp(start) - days * DAY;
  if (days > 0 && previousStart >= stamp(availableStart)) {
    return { start: new Date(previousStart).toISOString().slice(0, 10), end: new Date(stamp(start) - DAY).toISOString().slice(0, 10) };
  }
  return { start: availableStart, end: new Date(Math.min(stamp(end), stamp(availableStart) + 6 * DAY)).toISOString().slice(0, 10) };
}
export function dailyAverage(rows: Pick<Point, 'trip_count'>[], start: string, end: string) {
  const days = calendarDays(start, end);
  return days > 0 ? rows.reduce((sum, row) => sum + row.trip_count, 0) / days : null;
}
