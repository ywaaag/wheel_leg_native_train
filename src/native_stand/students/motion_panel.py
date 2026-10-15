"""Local browser panel for manual Motion preview: stdlib only, loopback only.

The panel never touches Isaac/PhysX objects. The GUI loop owns the policy and
exchanges two things with this module through Plan:

* commands (forward speed, yaw rate, stop, center, reset) written by the browser
  and consumed by the GUI loop once per step;
* telemetry published by the GUI loop and served read-only to the browser.

Explicit opt-in only (``--panel`` or ``NATIVE_MOTION_PANEL=1``); default port 8765
(``NATIVE_MOTION_PANEL_PORT``). Caps declared on the command line stay authoritative:
the browser may lower them for the session but can never raise them.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = 'native_motion_panel_v1'
DEFAULT_PORT = 8765
ENABLED_ENV = 'NATIVE_MOTION_PANEL'
PORT_ENV = 'NATIVE_MOTION_PANEL_PORT'
MAX_REQUEST_BYTES = 4096
COMMAND_KEYS = ('vx', 'yaw', 'stop', 'center', 'reset', 'max_speed', 'max_yaw_speed')
HTML_PATH = Path(__file__).with_name('motion_panel.html')


def enabled(flag):
    """Explicit opt-in; the environment variable is only a convenience alias."""
    if flag:
        return True
    return os.environ.get(ENABLED_ENV, '0').strip().lower() in ('1', 'true', 'yes')


def port_number(explicit=None):
    raw = explicit if explicit is not None else os.environ.get(PORT_ENV, DEFAULT_PORT)
    try:
        number = int(raw)
    except (TypeError, ValueError):
        raise ValueError('panel port must be an integer')
    if not 1 <= number <= 65535:
        raise ValueError('panel port must be within 1..65535')
    return number


def _bounded(name, value, low, high):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError('%s must be numeric' % name)
    if number != number or number in (float('inf'), float('-inf')):
        raise ValueError('%s must be finite' % name)
    if not low <= number <= high:
        raise ValueError('%s must be within %s..%s' % (name, low, high))
    return number


class Plan:
    """Locked holder shared by the GUI loop (owner) and the HTTP thread."""

    def __init__(self, max_speed, max_yaw_speed):
        self._lock = threading.Lock()
        self._declared = {'max_speed': _bounded('max_speed', max_speed, 1e-3, 4.),
                          'max_yaw_speed': _bounded('max_yaw_speed', max_yaw_speed, 0., 4.)}
        self._limits = dict(self._declared)
        self._target = [0., 0.]
        self._pending = {'stop': False, 'center': False, 'reset': False}
        self._telemetry = {}
        self.requests = 0

    def apply(self, payload):
        """Validate and apply one browser request; returns the applied subset."""
        if not isinstance(payload, dict):
            raise ValueError('command payload must be an object')
        unknown = [key for key in payload if key not in COMMAND_KEYS]
        if unknown:
            raise ValueError('unknown command fields: %s' % ','.join(sorted(unknown)))
        applied = {}
        with self._lock:
            if 'max_speed' in payload:
                value = _bounded('max_speed', payload['max_speed'], 1e-3, self._declared['max_speed'])
                self._limits['max_speed'] = value
                applied['max_speed'] = value
                self._target[0] = max(-value, min(value, self._target[0]))
            if 'max_yaw_speed' in payload:
                value = _bounded('max_yaw_speed', payload['max_yaw_speed'], 0., self._declared['max_yaw_speed'])
                self._limits['max_yaw_speed'] = value
                applied['max_yaw_speed'] = value
                self._target[1] = max(-value, min(value, self._target[1]))
            if 'vx' in payload:
                value = _bounded('vx', payload['vx'], -self._limits['max_speed'], self._limits['max_speed'])
                self._target[0] = value
                applied['vx'] = value
            if 'yaw' in payload:
                value = _bounded('yaw', payload['yaw'], -self._limits['max_yaw_speed'], self._limits['max_yaw_speed'])
                self._target[1] = value
                applied['yaw'] = value
            if payload.get('stop'):
                self._target = [0., 0.]
                self._pending['stop'] = True
                applied['stop'] = True
            if payload.get('center'):
                self._target = [0., 0.]
                self._pending['center'] = True
                applied['center'] = True
            if payload.get('reset'):
                self._pending['reset'] = True
                applied['reset'] = True
            self.requests += 1
        return applied

    def take(self):
        """Snapshot for the GUI loop; one-shot flags are consumed exactly once."""
        with self._lock:
            row = {'vx': self._target[0], 'yaw': self._target[1],
                   'max_speed': self._limits['max_speed'], 'max_yaw_speed': self._limits['max_yaw_speed'],
                   'stop': self._pending['stop'], 'center': self._pending['center'], 'reset': self._pending['reset']}
            self._pending = {'stop': False, 'center': False, 'reset': False}
        return row

    def publish(self, telemetry):
        with self._lock:
            self._telemetry = dict(telemetry)

    def snapshot(self):
        with self._lock:
            return {'version': VERSION, 'target': {'vx': self._target[0], 'yaw': self._target[1]},
                    'limits': dict(self._limits), 'declared_limits': dict(self._declared),
                    'requests': self.requests, 'telemetry': dict(self._telemetry)}


def handler_for(plan, html):
    """HTTP handler bound to one Plan; all responses are JSON except the page."""

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'
        server_version = VERSION

        def log_message(self, *args):
            pass

        def _send(self, code, body, content_type):
            data = body if isinstance(body, bytes) else body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def _json(self, code, payload):
            self._send(code, json.dumps(payload), 'application/json')

        def do_GET(self):
            if self.path in ('/', '/index.html'):
                self._send(200, html, 'text/html; charset=utf-8')
            elif self.path == '/telemetry':
                self._json(200, plan.snapshot())
            elif self.path == '/health':
                self._json(200, {'status': 'ok', 'version': VERSION})
            else:
                self._json(404, {'error': 'unknown path'})

        def do_POST(self):
            if self.path != '/command':
                self._json(404, {'error': 'unknown path'})
                return
            try:
                length = int(self.headers.get('Content-Length') or 0)
            except ValueError:
                length = -1
            if not 0 <= length <= MAX_REQUEST_BYTES:
                self._json(413, {'error': 'unsupported request size'})
                return
            try:
                payload = json.loads(self.rfile.read(length) or b'{}')
            except ValueError:
                self._json(400, {'error': 'invalid JSON'})
                return
            try:
                applied = plan.apply(payload)
            except ValueError as error:
                self._json(400, {'error': str(error)})
                return
            self._json(200, {'applied': applied, **plan.snapshot()})

    return Handler


def start(plan, port):
    """Serve on 127.0.0.1 only; returns (server, thread) for the caller to close."""
    html = HTML_PATH.read_text()
    server = ThreadingHTTPServer(('127.0.0.1', port), handler_for(plan, html))
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, name='motion-panel', daemon=True)
    thread.start()
    return server, thread


def stop(server):
    if server is None:
        return
    server.shutdown()
    server.server_close()
