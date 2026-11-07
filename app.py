import secrets
import sqlite3
import sys
import time
from threading import Lock, Timer
from uuid import UUID
from urllib.parse import urlsplit
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from database import initialize_database, get_recent_logs, get_recent_events, get_energy_summary
from config import ASSUMED_PC_POWER_WATTS, IDLE_LIMIT_SECONDS, CPU_HIGH_THRESHOLD, DATABASE_LOG_INTERVAL_SECONDS, SIMULATION_MODE, GRACE_PERIOD_SECONDS

from database import get_warning_pause_until, pause_warning
from windows_sleep import sleep_windows

app = Flask(__name__)
action_token = secrets.token_urlsafe(32)
sleep_lock = Lock()
sleep_request = None
pause_duration_seconds = 15 * 60
initialize_database()

@app.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/')
def home():
    return render_template('index.html', action_token=action_token)

@app.route('/api/status')
def status():
    logs = get_recent_logs(limit=60)
    latest = logs[0] if logs else None
    age = None
    if latest:
        age = max(0, (datetime.now().astimezone() - datetime.fromisoformat(latest['timestamp'])).total_seconds())
    return jsonify(log=latest, history=logs, events=get_recent_events(limit=12),
        energy=get_energy_summary(), age_seconds=age,
        live=age is not None and age <= max(5, DATABASE_LOG_INTERVAL_SECONDS * 3),
        settings=dict(power_watts=ASSUMED_PC_POWER_WATTS, idle_seconds=IDLE_LIMIT_SECONDS,
                      cpu_threshold=CPU_HIGH_THRESHOLD, motion_grace_seconds=GRACE_PERIOD_SECONDS, simulated=SIMULATION_MODE),
        buzzer_enabled=False,
        warning_pause_seconds=max(0, get_warning_pause_until() - time.time()),
        sleep_available=sys.platform == 'win32' and not SIMULATION_MODE,
        sleep_request=sleep_request)


def complete_sleep_request(request_id):
    global sleep_request
    try:
        sleep_windows()
    except OSError as error:
        app.logger.warning('Windows sleep failed: %s', error)
        sleep_request = dict(id=request_id, status='failed', message=f'Windows could not enter sleep: {error}')
    except Exception:
        app.logger.exception('Unexpected Windows sleep failure')
        sleep_request = dict(id=request_id, status='failed', message='Sleep failed. See the dashboard Terminal.')
    else:
        sleep_request = dict(id=request_id, status='completed', message='Windows accepted the sleep request.')
    finally:
        sleep_lock.release()


@app.route('/api/actions/<action>', methods=['POST'])
def power_action(action):
    global sleep_request
    host = urlsplit(request.host_url).hostname
    if (
        request.remote_addr not in ('127.0.0.1', '::1')
        or host not in ('127.0.0.1', 'localhost', '::1')
        or request.headers.get('Origin') != request.host_url.rstrip('/')
        or not secrets.compare_digest(request.headers.get('X-EcoPC-Token', ''), action_token)
    ):
        return jsonify(error='Open the local dashboard and refresh before using power controls.'), 403

    if action == 'keep-awake':
        pause_warning(pause_duration_seconds)
        return jsonify(message='EcoPC warnings paused for 15 minutes.')

    if action == 'resume-warnings':
        pause_warning(0)
        return jsonify(message='EcoPC warnings resumed.')

    if action != 'sleep':
        return jsonify(error='Unknown power action.'), 404
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or payload.get('confirmed') is not True:
        return jsonify(error='Confirm Sleep now first.'), 400
    if SIMULATION_MODE or sys.platform != 'win32':
        return jsonify(error='Sleep now requires local Windows hardware mode.'), 409
    try:
        request_id = str(UUID(payload['request_id']))
    except (KeyError, ValueError, AttributeError, TypeError):
        return jsonify(error='Refresh the dashboard and confirm Sleep now again.'), 400
    if not sleep_lock.acquire(blocking=False):
        return jsonify(error='A sleep request is already running.'), 409
    if sleep_request is not None and sleep_request['id'] == request_id:
        sleep_lock.release()
        return jsonify(sleep_request), 200
    sleep_request = dict(id=request_id, status='pending', message='Sleep requested. Checking the result when Windows is available…')
    worker = Timer(1.0, complete_sleep_request, args=(request_id,))
    worker.daemon = True
    try:
        worker.start()
    except RuntimeError:
        sleep_request = None
        sleep_lock.release()
        return jsonify(error='Could not start the sleep request.'), 503
    return jsonify(sleep_request), 202

@app.route('/api/history')
def history():
    return jsonify(get_recent_logs(limit=60))

@app.route('/api/events')
def events():
    return jsonify(get_recent_events(limit=20))

@app.errorhandler(sqlite3.Error)
def database_error(error):
    app.logger.error('Database error: %s', error)
    return jsonify(error='Database unavailable. Please retry.'), 503

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
