import { describe, expect, it } from 'vitest';
import { calendarDays, comparisonDefault, dailyAverage } from './comparison';

describe('date-range demand comparison', () => {
  it('uses inclusive calendar days, including the DST transition', () => {
    expect(calendarDays('2025-03-08', '2025-03-10')).toBe(3);
    expect(calendarDays('2025-01-15', '2025-01-15')).toBe(1);
  });
  it('prefers an equal-length preceding period when available', () => {
    expect(comparisonDefault('2025-02-01', '2025-02-07', '2025-01-01'))
      .toEqual({ start: '2025-01-25', end: '2025-01-31' });
  });
  it('keeps the fallback baseline inside available data', () => {
    expect(comparisonDefault('2025-01-01', '2025-03-31', '2025-01-01'))
      .toEqual({ start: '2025-01-01', end: '2025-01-07' });
    expect(comparisonDefault('2025-01-01', '2025-01-02', '2025-01-01').end).toBe('2025-01-02');
  });
  it('counts zero-demand days in the denominator', () => {
    expect(dailyAverage([{ trip_count: 30 }], '2025-01-01', '2025-01-03')).toBe(10);
    expect(dailyAverage([], '2025-01-01', '2025-01-03')).toBe(0);
  });
});
