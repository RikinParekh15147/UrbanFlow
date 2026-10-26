import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { LineChart, BarChart, PieChart, ScatterChart, HeatmapChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, AriaComponent, DataZoomComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { compact } from '../lib/utils';
import type { Point } from '../lib/api';

echarts.use([LineChart, BarChart, PieChart, ScatterChart, HeatmapChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, AriaComponent, DataZoomComponent, CanvasRenderer]);
export type Option = echarts.EChartsCoreOption;
export const colors = ['#216e55', '#bf612b', '#3878a3', '#8f6d9f', '#a59943', '#65837c'];
export function Chart({ option, label, height = 260 }: { option: Option; label: string; height?: number }) {
  const element = useRef<HTMLDivElement>(null);
  const instance = useRef<echarts.EChartsType | null>(null);
  useEffect(() => {
    if (!element.current) return;
    const chart = echarts.init(element.current, undefined, { renderer: 'canvas' });
    instance.current = chart;
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(element.current);
    return () => { observer.disconnect(); chart.dispose(); instance.current = null; };
  }, []);
  useEffect(() => {
    instance.current?.setOption({ color: colors, textStyle: { fontFamily: 'DM Sans Variable, sans-serif', color: '#52665e' },
      animation: !matchMedia('(prefers-reduced-motion: reduce)').matches, animationDuration: 350,
      aria: { enabled: true, description: label }, ...option }, { notMerge: true });
  }, [option, label]);
  return <div ref={element} className="chart" role="img" aria-label={label} style={{ height }} />;
}
export function demandLine(data: Point[], key: 'trip_count' | 'avg_fare' = 'trip_count'): Option {
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => v.toLocaleString('en-US', { maximumFractionDigits: 2 }) },
    grid: { left: 54, right: 16, top: 24, bottom: 32 },
    xAxis: { type: 'category', boundaryGap: false, data: data.map(r => r.date?.slice(5)), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#52665e', fontSize: 11, interval: Math.max(0, Math.ceil(data.length / 5) - 1) } },
    yAxis: { type: 'value', axisLabel: { formatter: compact }, splitLine: { lineStyle: { color: '#e9eee7', type: 'dashed' } } },
    series: [{ type: 'line', data: data.map(r => r[key]), smooth: 0.25, symbol: 'circle', showSymbol: false, lineStyle: { width: 2.5 }, areaStyle: { color: '#216e55', opacity: 0.07 } }],
  };
}
export function bars(labels: string[], values: (number | null | undefined)[], horizontal = false): Option {
  const category = { type: 'category', data: labels, axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: '#52665e', overflow: 'truncate', width: horizontal ? 142 : 90 } };
  const value = { type: 'value', axisLabel: { formatter: compact }, splitLine: { lineStyle: { color: '#e9eee7', type: 'dashed' } } };
  return { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, grid: { left: horizontal ? 155 : 50, right: 20, top: 12, bottom: 30 }, xAxis: horizontal ? value : category, yAxis: horizontal ? { ...category, inverse: true } : value,
    series: [{ type: 'bar', data: values, barMaxWidth: 24, itemStyle: { borderRadius: horizontal ? [0, 3, 3, 0] : [3, 3, 0, 0] } }] };
}
