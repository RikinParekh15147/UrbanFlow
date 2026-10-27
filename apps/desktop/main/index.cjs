const { app, BrowserWindow, dialog, session } = require('electron');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');

app.setName('UrbanFlow');
app.setPath('userData', path.join(app.getPath('appData'), 'UrbanFlow'));

let backend;
let window;
let quitting = false;
const smokeOutput = process.argv.find(value => value.startsWith('--smoke-output='))?.slice('--smoke-output='.length);
const root = path.resolve(__dirname, '../../..');
const lock = app.requestSingleInstanceLock();
if (!lock) app.quit();
app.on('second-instance', () => { if (window) { if (window.isMinimized()) window.restore(); window.focus(); } });

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => { const port = server.address().port; server.close(() => resolve(port)); });
  });
}
async function startBackend() {
  const port = await freePort();
  const resources = app.isPackaged ? process.resourcesPath : root;
  const executable = app.isPackaged ? path.join(resources, 'backend', 'urbanflow-api.exe') : path.join(root, '.venv', 'Scripts', 'python.exe');
  const args = app.isPackaged ? [] : ['-m', 'app.desktop_entry'];
  args.push('--port', String(port), '--snapshot-dir', path.join(resources, app.isPackaged ? 'serving' : 'data/serving'), '--web-dir', path.join(resources, app.isPackaged ? 'web' : 'apps/web/dist'));
  const log = fs.createWriteStream(path.join(app.getPath('userData'), 'backend.log'), { flags: 'a' });
  backend = spawn(executable, args, { cwd: resources, windowsHide: true,
    env: { ...process.env, URBANFLOW_ENV: 'production', URBANFLOW_ENV_FILE: path.join(app.getPath('userData'), '.env') },
    stdio: ['ignore', 'pipe', 'pipe'] });
  backend.stdout.pipe(log); backend.stderr.pipe(log);
  let failure;
  backend.once('error', error => { failure = error.message; });
  backend.once('exit', code => { failure = `Backend exited (${code}).`; if (window && !quitting) { dialog.showErrorBox('UrbanFlow backend stopped', 'Restart UrbanFlow to reconnect. Details are in the application backend.log.'); app.quit(); } });
  const origin = `http://127.0.0.1:${port}`;
  for (let attempt = 0; attempt < 150; attempt++) {
    if (failure) throw new Error(failure);
    try {
      const response = await fetch(`${origin}/health`, { signal: AbortSignal.timeout(1000) });
      const health = await response.json();
      if (response.ok && health.service === 'urbanflow-api') return origin;
    } catch { /* backend is still starting */ }
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  throw new Error('The backend did not become ready within 30 seconds. See backend.log.');
}

if (lock) app.whenReady().then(async () => {
  try {
    const origin = await startBackend();
    session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
    session.defaultSession.setPermissionCheckHandler(() => false);
    const policy = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'";
    session.defaultSession.webRequest.onHeadersReceived((details, callback) => callback({ responseHeaders: { ...details.responseHeaders, 'Content-Security-Policy': [policy] } }));
    window = new BrowserWindow({ width: 1440, height: 960, minWidth: 760, minHeight: 600,
      title: 'UrbanFlow', backgroundColor: '#f4f5f0', show: false, autoHideMenuBar: true,
      webPreferences: { preload: path.join(__dirname, '../preload/index.cjs'), contextIsolation: true, sandbox: true, nodeIntegration: false, webSecurity: true } });
    window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    window.webContents.on('will-navigate', (event, url) => {
      try { if (new URL(url).origin !== origin) event.preventDefault(); }
      catch { event.preventDefault(); }
    });
    window.once('ready-to-show', () => window.show());
    await window.loadURL(origin);
    if (smokeOutput) {
      const result = await window.webContents.executeJavaScript(`(async () => {
        const response = await fetch('/api/v1/overview');
        const overview = await response.json();
        let dashboardReady = false;
        for (let attempt = 0; attempt < 150; attempt++) {
          if (document.querySelector('.overview-grid canvas')) { dashboardReady = true; break; }
          await new Promise(resolve => setTimeout(resolve, 200));
        }
        if (dashboardReady) await new Promise(resolve => setTimeout(resolve, 1000));
        document.querySelector('a[href="/geography"]')?.click();
        let mapReady = false;
        let mapState = 'missing';
        for (let attempt = 0; attempt < 225; attempt++) {
          mapState = document.querySelector('main [data-map-state]')?.getAttribute('data-map-state') ?? 'missing';
          if (location.pathname === '/geography' && mapState === 'ready') { mapReady = true; break; }
          if (mapState === 'error') break;
          await new Promise(resolve => setTimeout(resolve, 200));
        }
        if (mapReady) await new Promise(resolve => setTimeout(resolve, 500));
        return { title: document.title, apiStatus: response.status,
          overview, dashboardReady, mapReady, mapState, route: location.pathname,
          rootChildren: document.getElementById('root')?.childElementCount,
          nodeDisabled: typeof require === 'undefined', desktop: window.urbanflow?.desktop };
      })()`);
      if (result.apiStatus !== 200 || !result.dashboardReady || !result.mapReady || !result.rootChildren || !result.nodeDisabled || !result.desktop) throw new Error(`Desktop smoke check failed (dashboard: ${result.dashboardReady}, map: ${result.mapState}, route: ${result.route}).`);
      fs.mkdirSync(path.dirname(path.resolve(smokeOutput)), { recursive: true });
      fs.writeFileSync(smokeOutput, JSON.stringify(result, null, 2));
      const screenshot = await window.webContents.capturePage();
      fs.writeFileSync(`${smokeOutput}.png`, screenshot.toPNG());
      app.quit();
    }
  } catch (error) {
    if (smokeOutput) {
      fs.mkdirSync(path.dirname(path.resolve(smokeOutput)), { recursive: true });
      fs.writeFileSync(smokeOutput, JSON.stringify({ error: error.message }, null, 2));
      quitting = true;
      if (backend && !backend.killed) backend.kill();
      app.exit(1);
    } else {
      dialog.showErrorBox('UrbanFlow could not start', error.message);
      app.quit();
    }
  }
});
app.on('window-all-closed', () => app.quit());
app.on('before-quit', () => { quitting = true; if (backend && !backend.killed) backend.kill(); });
