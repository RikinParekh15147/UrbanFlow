import { Link } from 'react-router-dom';
import { useDataset } from '../../app/data-context';
import { Panel, Title } from '../../components/panels';
import { number } from '../../lib/utils';
import './page.css';

function record(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown> : {};
}
function text(value: unknown) {
  return typeof value === 'string' || typeof value === 'number' ? String(value) : 'Not recorded';
}
function count(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value) ? number(value) : 'Not recorded';
}

export default function DatasetModelPage() {
  const { manifest, run_id, start, end, status } = useDataset();
  const quality = record(manifest?.quality);
  const machine = record(manifest?.machine);
  const curated = record(manifest?.curated);
  const sources = Array.isArray(manifest?.sources) ? manifest.sources.map(record) : [];
  const collections = Object.entries(record(manifest?.collection_counts));
  return <>
    <Title title="Dataset & Model" description="Understand the records, analytical methods and boundaries behind UrbanFlow." />
    <dl className="kpi-strip">
      <div><dt>Source records</dt><dd>{count(manifest?.source_rows)}</dd><span>Before period and metric eligibility checks</span></div>
      <div><dt>In-period pickups</dt><dd>{count(manifest?.eligible_demand_rows)}</dd><span>{start} to {end}</span></div>
      <div><dt>Zone metadata</dt><dd>{count(record(manifest?.collection_counts).zones)}</dd><span>Only zones with official geometry appear on maps</span></div>
      <div><dt>Analysis type</dt><dd className="info-method">Descriptive</dd><span>Batch Spark SQL analytics</span></div>
    </dl>
    <div className="two-columns">
      <Panel title="The dataset" detail="NYC Taxi & Limousine Commission · Yellow Taxi trip records">
        <dl className="quality-list info-facts">
          <div><dt>Coverage</dt><dd>{start} to {end}, inclusive</dd></div>
          <div><dt>Published version</dt><dd>{run_id}</dd></div>
          <div><dt>Time convention</dt><dd>New York local wall-clock time</dd></div>
          <div><dt>Serving source</dt><dd>{status.data?.source === 'local_snapshot' ? 'Bundled real-data snapshot' : 'MongoDB aggregates'}</dd></div>
          <div><dt>Curated records</dt><dd>{count(curated.rows)}</dd></div>
          <div><dt>Storage</dt><dd>Raw and curated Parquet; summarized serving data</dd></div>
        </dl>
        <p className="explanation">Records describe reported taxi journeys. Pickup/drop-off times and zone IDs, distance, fares, tips, payment types and surcharges support the dashboard. Official TLC taxi-zone boundaries provide geographic context.</p>
      </Panel>
      <Panel title="The analytical model" detail="A reproducible aggregation pipeline, with no trained prediction model">
        <p className="explanation">UrbanFlow calculates historical summaries using Apache Spark and Spark SQL. It groups eligible journeys by date, pickup hour, zone and route, then publishes versioned results for the application.</p>
        <dl className="quality-list info-facts">
          <div><dt>ETL version</dt><dd>{text(manifest?.etl_version)}</dd></div>
          <div><dt>Engine</dt><dd>{text(manifest?.engine)}</dd></div>
          <div><dt>Spark version</dt><dd>{text(manifest?.spark_version)}</dd></div>
          <div><dt>Shuffle partitions</dt><dd>{count(manifest?.partitions)}</dd></div>
          <div><dt>Training / prediction</dt><dd>Not used in this release</dd></div>
          <div><dt>Accuracy score</dt><dd>Not applicable to descriptive analytics</dd></div>
        </dl>
        <p className="explanation">Correctness is checked through fixture tests, reconciled record counts and matching benchmark outputs. Predictions, train/test splits and forecast accuracy would require a separate future model.</p>
      </Panel>
    </div>
    <Panel title="How the measurements are calculated" detail="Metric-specific eligible records keep invalid measurements out of averages">
      <div className="table-scroll"><table className="info-definitions"><thead><tr><th>Measurement</th><th>Definition and scope</th></tr></thead><tbody>
        <tr><td>Demand</td><td>Count of pickups within the published period and current selection.</td></tr>
        <tr><td>Average distance</td><td>Sum of usable recorded miles / distance-eligible trips; distance from 0 to 100 miles.</td></tr>
        <tr><td>Trip efficiency</td><td>Positive distance up to 100 miles, duration 1–240 minutes and estimated speed up to 100 mph.</td></tr>
        <tr><td>Estimated travel speed</td><td>Total efficiency-eligible miles / total corresponding travel hours.</td></tr>
        <tr><td>Average base fare</td><td>Eligible base-fare sum / fare-eligible trips; fares from $0 to $1,000.</td></tr>
        <tr><td>Base fare per mile</td><td>Eligible fare sum / corresponding positive usable miles.</td></tr>
        <tr><td>Route flows</td><td>Only the top 100 routes per day are retained; filtered rankings cover this limited sample.</td></tr>
      </tbody></table></div>
    </Panel>
    <div className="two-columns">
      <Panel title="Data quality and interpretation" detail="Exclusion flags overlap; these are not distinct discarded-trip totals">
        <dl className="quality-list">{Object.entries(quality).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{count(value)}</dd></div>)}</dl>
        <ul className="notes-list"><li>A trip may count toward demand while being excluded from a particular fare or efficiency calculation.</li><li>Taxi activity does not measure all city travel, observed road congestion or accident hotspots.</li><li>Local timestamps carry daylight-saving ambiguity. Payment records do not fully capture cash tips.</li></ul>
      </Panel>
      <Panel title="Processing and reproducibility" detail="Dashboard queries use saved summaries and do not start Spark jobs">
        <dl className="quality-list info-facts">
          <div><dt>Run recorded at</dt><dd>{text(manifest?.created_at)}</dd></div>
          <div><dt>ETL elapsed</dt><dd>{typeof manifest?.elapsed_seconds === 'number' ? `${number(manifest.elapsed_seconds, 1)} seconds` : 'Not recorded'}</dd></div>
          <div><dt>Python</dt><dd>{text(machine.python)}</dd></div>
          <div><dt>CPUs / RAM</dt><dd>{count(machine.cpu_count)} / {text(machine.memory_gb)} GB</dd></div>
          <div><dt>Driver memory</dt><dd>{text(manifest?.driver_memory)}</dd></div>
        </dl>
        <p className="explanation">Benchmarks compare equivalent Pandas and Spark zone-count tasks, using repeated runs and verified matching outputs. Timings include Parquet reads and exclude Spark session startup. They do not represent model accuracy or a universal speed ranking.</p>
        <Link className="info-link" to="/lab">View measured benchmarks in Big Data Lab →</Link>
      </Panel>
    </div>
    <Panel title="Source files and provenance" detail="Published manifest values; checksums identify the exact input files">
      {sources.length ? <div className="info-sources">{sources.map((source, index) => <details key={String(source.name ?? index)}><summary>{text(source.name)}<span>{typeof source.bytes === 'number' ? `${number(source.bytes)} bytes` : 'Size not recorded'}</span></summary><dl><dt>Source URL</dt><dd>{text(source.url)}</dd><dt>SHA-256</dt><dd><code>{text(source.sha256)}</code></dd></dl></details>)}</div> : <p className="explanation">Individual source files were not recorded in this version’s manifest.</p>}
    </Panel>
    {!!collections.length && <Panel title="Published analytical outputs" detail="Aggregate documents in this version, not raw trip counts"><dl className="quality-list">{collections.map(([name, value]) => <div key={name}><dt>{name.replaceAll('_', ' ')}</dt><dd>{count(value)}</dd></div>)}</dl></Panel>}
  </>;
}
