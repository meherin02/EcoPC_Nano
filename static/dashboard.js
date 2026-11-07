const $ = id => document.getElementById(id);
const put = (id, value) => { $(id).textContent = value; };
const num = (value, digits=1) => value == null ? '—' : Number(value).toFixed(digits);
const date = value => value ? new Date(value).toLocaleString() : '—';
const actionToken = document.querySelector('meta[name="ecopc-action-token"]').content;
let actionBusy = false;
let sleepAvailable = false;
let pendingSleep = null;
let serverSleepPending = false;
let warningsPaused = false;

function updateButtons() {
  $('sleep-now').disabled = actionBusy || !sleepAvailable || pendingSleep !== null || serverSleepPending;
  $('keep-awake').disabled = actionBusy;
  $('resume-warnings').hidden = !warningsPaused;
  $('resume-warnings').disabled = actionBusy;
}

async function powerAction(action) {
  if (actionBusy) return;
  const sleep = action === 'sleep';
  if (sleep && (pendingSleep || serverSleepPending || !window.confirm('Put this Windows PC to sleep now?'))) return;
  const requestId = sleep ? crypto.randomUUID() : null;
  if (sleep) pendingSleep = {id: requestId, sentAt: Date.now()};
  actionBusy = true;
  updateButtons();
  const progress = {
    sleep: 'Requesting Windows sleep…',
    'keep-awake': 'Pausing EcoPC warnings…',
    'resume-warnings': 'Resuming EcoPC warnings…',
  };
  put('power-result', progress[action]);
  try {
    const response = await fetch('/api/actions/' + action, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-EcoPC-Token': actionToken},
      body: JSON.stringify({confirmed: sleep, request_id: requestId}),
      signal: AbortSignal.timeout(5000),
    });
    const result = await response.json();
    if (!response.ok) {
      if (sleep) pendingSleep = null;
      put('power-result', result.error || 'Power action failed.');
      return;
    }
    if (action === 'keep-awake') warningsPaused = true;
    if (action === 'resume-warnings') warningsPaused = false;
    put('power-result', result.message);
  } catch {
    put('power-result', sleep
      ? 'Connection interrupted. Checking whether Windows received the sleep request…'
      : 'Could not confirm the warning setting. Check the countdown or reopen the dashboard.');
  } finally {
    actionBusy = false;
    updateButtons();
  }
}

$('sleep-now').addEventListener('click', () => powerAction('sleep'));
$('keep-awake').addEventListener('click', () => powerAction('keep-awake'));
$('resume-warnings').addEventListener('click', () => powerAction('resume-warnings'));

async function refresh() {
  try {
    const response = await fetch('/api/status', {cache:'no-store', signal:AbortSignal.timeout(5000)});
    if (!response.ok) throw new Error('Server unavailable');
    const d = await response.json(), l = d.log, s = d.settings;
    sleepAvailable = d.sleep_available;
    const sleepResult = d.sleep_request;
    serverSleepPending = sleepResult?.status === 'pending';
    if (pendingSleep && sleepResult?.id === pendingSleep.id) {
      put('power-result', sleepResult.message);
      if (!serverSleepPending) pendingSleep = null;
    } else if (pendingSleep && !actionBusy && Date.now() - pendingSleep.sentAt > 5000) {
      put('power-result', 'The server could not confirm this sleep request. Open the local dashboard in Chrome or Edge before trying again.');
      pendingSleep = null;
    }
    const paused = Math.ceil(d.warning_pause_seconds);
    warningsPaused = paused > 0;
    updateButtons();
    put('pause-countdown', paused > 0
      ? `EcoPC warnings paused · ${Math.floor(paused / 60)}m ${paused % 60}s remaining`
      : 'Keep awake pauses EcoPC warnings for 15 minutes. Windows manages its own sleep timer.');
    put('connection', d.live ? (s.simulated ? 'Live · simulation' : 'Live · Arduino mode') : 'Monitoring offline / stale');
    const hero = document.querySelector('.hero');
    hero.className = 'hero' + (!d.live ? ' stale' : l?.state === 'ENERGY_WASTE_SUSPECTED' ? ' warning' : '');
    put('state', d.live && l ? l.state.replaceAll('_',' ') : 'Waiting for live readings');
    put('decision', d.live && l ? l.decision : 'Saved values may be old. Start or restart run_simulation.py.');
    put('recorded', date(l?.timestamp));
    put('idle', num(l?.idle_seconds) + ' s'); put('cpu', num(l?.cpu_usage) + ' %'); put('memory', num(l?.memory_usage) + ' %');
    $('cpu-bar').value = l?.cpu_usage ?? 0; $('memory-bar').value = l?.memory_usage ?? 0;
    put('motion', !d.live || l?.presence == null ? 'Unknown' : l.presence ? 'Motion detected' : 'No motion');
    put('absence', 'No-motion duration: ' + num(l?.absence_seconds) + ' s');
    put('energy', num(d.energy?.estimated_energy_wh,3) + ' Wh');
    put('waste', 'Time in suspected-waste state: ' + num(d.energy?.waste_seconds) + ' s');
    put('estimate-time', 'Estimate updated: ' + date(d.energy?.timestamp));
    put('power', 'Assumed PC power: ' + s.power_watts + ' W');
    put('settings', 'Input idle threshold: ' + s.idle_seconds + ' s · CPU threshold: ' + s.cpu_threshold + '% · No-motion confirmation: ' + s.motion_grace_seconds + ' s');
    const readings = d.history.slice().reverse();
    $('cpu-line').setAttribute('points', readings.map((r,i) => `${i*600/Math.max(1,readings.length-1)},${150-1.5*Math.min(100,Math.max(0,r.cpu_usage??0))}`).join(' '));
    $('events').replaceChildren();
    for (const e of d.events) { const li = document.createElement('li'); li.textContent = date(e.timestamp) + ' · ' + e.message; $('events').append(li); }
    if (!d.events.length) { const li=document.createElement('li'); li.textContent='No events yet.'; $('events').append(li); }
  } catch (error) {
    sleepAvailable = false;
    updateButtons();
    put('connection','Dashboard disconnected'); put('state','Live data unavailable');
    put('decision','Check that app.py is running. Previously displayed values may be old.');
    put('motion','Unknown'); document.querySelector('.hero').className='hero stale';
  } finally { setTimeout(refresh,1000); }
}
refresh();