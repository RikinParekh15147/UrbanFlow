import { describe, expect, it } from 'vitest';
import { number, dollars } from './utils';

describe('measurement formatting', () => {
  it('distinguishes absent observations from zero', () => {
    expect(number(null)).toBe('—');
    expect(number(0)).toBe('0');
    expect(dollars(null)).toBe('—');
    expect(dollars(0)).toBe('$0.00');
  });
});
