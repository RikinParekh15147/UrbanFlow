import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, Database, FileCheck2 } from 'lucide-react';
import { useDataset } from '../../app/data-context';
import { api } from '../../lib/api';
import { Chart } from '../../components/chart';
import { Panel, QueryState, Title } from '../../components/panels';
import { compact, number } from '../../lib/utils';

export default function BenchmarksPage() {
  const { run_id, manifest } = useDataset();
  const query = useQuery({ queryKey: ['benchmarks', run_id], queryFn: ({ signal }) => api.benchmarks(run_id, signal), enabled: !!run_id });
  const data = query.data;
  const rows = data?.data ?? [];
  const sizes = [...new Set(rows.map(r => Number(r.input_rows)))].sort((a,b) => a-b);
  return <>
    <Title title="Big Data Lab" description="Follow the evidence, from raw Parquet to the analysis on your screen." rows={rows} file="urbanflow-benchmarks.csv" datasetWide />
    <div className="method-note standalone">Experiments and quality counts cover the entire published dataset. Date, borough, and zone filters do not apply. Benchmark timings include reading Parquet and exclude Spark session startup.</div>
    <div className="pipeline-strip">{[[Database,'TLC Parquet'],[FileCheck2,'Validate & curate'],[Database,'Spark SQL'],[Database,'MongoDB'],[CheckCircle2,'Dashboard']].map(([Icon,label], i) => { const Component = Icon as typeof Database; return <div key={String(label)}><Component size={19}/><span>{String(label)}</span>{i < 4 && <span className="pipeline-arrow">→</span>}</div>; })}</div>
    <QueryState loading={query.isPending} error={query.error} retry={() => query.refetch()} />
    {data && <>
      <div className="two-columns"><Panel title="Measured processing performance" detail="Median of repeated equivalent zone-count tasks · includes Parquet reading">
        {rows.length ? <Chart height={300} label="Measured Pandas and Spark execution time by input row count" option={{ tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${number(v, 1)} ms` }, legend: { top: 0 }, grid: { left: 64, right: 20, top: 45, bottom: 32 }, xAxis: { type: 'category', data: sizes.map(compact), name: 'rows', nameGap: 5 }, yAxis: { type: 'value', name: 'milliseconds', splitLine: { lineStyle: { color: '#e9eee7', type: 'dashed' } } }, series: ['Pandas','Spark SQL'].map(engine => ({ name: engine, type: 'bar', barMaxWidth: 28, data: sizes.map(size => { const experiment = rows.find(r => r.engine === engine && Number(r.input_rows) === size); return experiment ? Number(experiment.elapsed_ms) : null; }) })) }} /> : <p className="explanation">No benchmark experiments have been published for this version.</p>}
      </Panel><Panel title="Data quality, made visible" detail="Dataset-wide counts; exclusion flags can overlap"><dl className="quality-list">{Object.entries(data.quality).map(([key,value]) => <div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{number(value)}</dd></div>)}</dl></Panel></div>
      <Panel title="Experiment results" detail="Observed results, not a claim that one engine always wins"><div className="table-scroll"><table><thead><tr><th>Engine</th><th className="numeric">Input rows</th><th className="numeric">Median</th><th className="numeric">Min–max</th><th className="numeric">Repeats</th><th>Verified</th></tr></thead><tbody>{rows.map(r => <tr key={String(r.experiment_id)}><td>{String(r.engine)}</td><td className="numeric">{number(Number(r.input_rows))}</td><td className="numeric">{number(Number(r.elapsed_ms), 1)} ms</td><td className="numeric">{number(Number(r.min_ms), 1)}–{number(Number(r.max_ms), 1)} ms</td><td className="numeric">{String(r.repetitions)}</td><td>{r.correctness_verified ? 'Outputs match' : 'Unverified'}</td></tr>)}</tbody></table></div></Panel>
      <div className="two-columns"><Panel title="Published processing run" detail={run_id}><dl className="quality-list"><div><dt>Source rows</dt><dd>{number(Number(manifest?.source_rows))}</dd></div><div><dt>ETL engine</dt><dd>{String(manifest?.engine ?? 'Spark SQL')}</dd></div><div><dt>Spark version</dt><dd>{String(manifest?.spark_version ?? '—')}</dd></div><div><dt>Shuffle partitions</dt><dd>{String(manifest?.partitions ?? '—')}</dd></div><div><dt>ETL elapsed</dt><dd>{number(Number(manifest?.elapsed_seconds), 1)} s</dd></div><div><dt>ETL version</dt><dd>{String(manifest?.etl_version ?? '—')}</dd></div></dl></Panel><Panel title="Reproducibility notes" detail="Read these alongside the chart"><ul className="notes-list">{(data.notes ?? []).map(note => <li key={note}>{note}</li>)}<li>Engine order alternates between repetitions. OS page caches are not cleared.</li><li>Environment: {String(data.machine.cpu_count ?? '—')} CPUs · {String(data.machine.memory_gb ?? '—')} GB RAM · Python {String(data.machine.python ?? '—')}.</li><li>Trip-level filters do not apply to these dataset-wide experiments.</li></ul></Panel></div>
    </>}
  </>;
}
