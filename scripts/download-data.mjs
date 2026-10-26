// Local fallback when Colab is unavailable. Never commit data or credentials.
import { createHash } from 'node:crypto';
import { createReadStream, createWriteStream } from 'node:fs';
import { mkdir, readFile, rename, stat, writeFile, open } from 'node:fs/promises';
import path from 'node:path';
import { Readable, Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';

const configPath = process.argv[2] ?? 'configs/yellow-2025-01.json';
const output = path.resolve(process.argv[3] ?? 'data/raw');
const config = JSON.parse(await readFile(configPath, 'utf8'));
await mkdir(output, { recursive: true });
const statusPath = path.join(output, 'download-progress.json');
const manifestPath = path.join(output, `${config.period}-manifest.json`);
let previous;
try { previous = JSON.parse(await readFile(manifestPath, 'utf8')); } catch { previous = { files: [] }; }
const manifest = { dataset: config.dataset, period: config.period, downloaded_at: new Date().toISOString(), files: [] };

async function checksum(file) {
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(file)) hash.update(chunk);
  return hash.digest('hex');
}

try {
  for (const file of config.files) {
    if (path.basename(file.name) !== file.name) throw new Error('Unsafe destination filename');
    const destination = path.join(output, file.name);
    const prior = previous.files.find(row => row.name === file.name && row.url === file.url);
    if (prior && await stat(destination).then(s => s.size === prior.bytes).catch(() => false)
        && await checksum(destination) === prior.sha256) {
      manifest.files.push(prior);
      console.log(`${file.name}: verified existing file`);
      continue;
    }
    const response = await fetch(file.url, { signal: AbortSignal.timeout(300_000) });
    if (!response.ok) throw new Error(`${response.status}: ${file.url}`);
    const total = Number(response.headers.get('content-length')) || null;
    let bytes = 0;
    let lastReport = 0;
    const started = Date.now();
    const hash = createHash('sha256');
    const temporary = `${destination}.partial`;
    const progress = new Transform({ transform(chunk, _encoding, callback) {
      bytes += chunk.length;
      hash.update(chunk);
      if (Date.now() - lastReport >= 2000) {
        lastReport = Date.now();
        console.log(`${file.name}: ${(bytes / 1e6).toFixed(1)} MB${total ? ` / ${(total / 1e6).toFixed(1)} MB` : ''}`);
      }
      callback(null, chunk);
    }});
    await writeFile(statusPath, JSON.stringify({ state: 'downloading', file: file.name, total_bytes: total }));
    await pipeline(Readable.fromWeb(response.body), progress, createWriteStream(temporary));
    if (total !== null && bytes !== total) throw new Error('Incomplete download');
    if (file.kind === 'parquet') {
      if (bytes < 12) throw new Error('Truncated Parquet');
      const handle = await open(temporary, 'r');
      try {
        const first = Buffer.alloc(4), last = Buffer.alloc(4);
        await handle.read(first, 0, 4, 0); await handle.read(last, 0, 4, bytes - 4);
        if (first.toString() !== 'PAR1' || last.toString() !== 'PAR1') throw new Error('Invalid Parquet signature');
      } finally { await handle.close(); }
    }
    await rename(temporary, destination);
    manifest.files.push({ ...file, bytes, sha256: hash.digest('hex'), elapsed_seconds: (Date.now() - started) / 1000 });
    await writeFile(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
    console.log(`${file.name}: complete (${bytes} bytes)`);
  }
  await writeFile(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  await writeFile(statusPath, JSON.stringify({ state: 'complete', manifest: manifestPath, files: manifest.files.length }));
  console.log(`Ready for upload: ${output}`);
} catch (error) {
  await writeFile(statusPath, JSON.stringify({ state: 'failed', error: error.message }));
  console.error(error.message); process.exitCode = 1;
}
