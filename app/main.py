import os
import time
import random
import threading
import math
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

MODE = os.environ.get("MODE", "stable")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
APP_PORT = int(os.environ.get("APP_PORT", "3000"))
START_TIME = time.time()

chaos_state = {"mode": None, "duration": 0, "rate": 0.0, "active": False}
chaos_lock = threading.Lock()

# Metrics storage
metrics_lock = threading.Lock()
request_counts = {}
request_durations = {}
BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]


def record_metrics(method, path, status_code, duration):
    with metrics_lock:
        key = (method, path, str(status_code))
        request_counts[key] = request_counts.get(key, 0) + 1
        if path not in request_durations:
            request_durations[path] = []
        request_durations[path].append(duration)
        if len(request_durations[path]) > 10000:
            request_durations[path] = request_durations[path][-10000:]


def get_chaos_active():
    with chaos_lock:
        if not chaos_state["active"]:
            return 0
        if chaos_state["mode"] == "slow":
            return 1
        if chaos_state["mode"] == "error":
            return 2
    return 0


def apply_chaos():
    with chaos_lock:
        state = dict(chaos_state)
    if not state["active"]:
        return None
    if state["mode"] == "slow":
        time.sleep(state["duration"])
        return None
    if state["mode"] == "error":
        if random.random() < state["rate"]:
            return 500
    return None


def generate_metrics():
    lines = []
    lines.append("# HELP http_requests_total Total HTTP requests")
    lines.append("# TYPE http_requests_total counter")
    with metrics_lock:
        for (method, path, status), count in request_counts.items():
            lines.append(f'http_requests_total{{method="{method}",path="{path}",status_code="{status}"}} {count}')

    lines.append("# HELP http_request_duration_seconds HTTP request duration")
    lines.append("# TYPE http_request_duration_seconds histogram")
    with metrics_lock:
        for path, durations in request_durations.items():
            count = len(durations)
            total = sum(durations)
            for bucket in BUCKETS:
                bucket_count = sum(1 for d in durations if d <= bucket)
                lines.append(f'http_request_duration_seconds_bucket{{le="{bucket}",path="{path}"}} {bucket_count}')
            lines.append(f'http_request_duration_seconds_bucket{{le="+Inf",path="{path}"}} {count}')
            lines.append(f'http_request_duration_seconds_sum{{path="{path}"}} {total:.6f}')
            lines.append(f'http_request_duration_seconds_count{{path="{path}"}} {count}')

    uptime = time.time() - START_TIME
    lines.append("# HELP app_uptime_seconds Application uptime")
    lines.append("# TYPE app_uptime_seconds gauge")
    lines.append(f"app_uptime_seconds {uptime:.2f}")

    lines.append("# HELP app_mode Current app mode 0=stable 1=canary")
    lines.append("# TYPE app_mode gauge")
    lines.append(f"app_mode {1 if MODE == 'canary' else 0}")

    lines.append("# HELP chaos_active Chaos state 0=none 1=slow 2=error")
    lines.append("# TYPE chaos_active gauge")
    lines.append(f"chaos_active {get_chaos_active()}")

    return chr(10).join(lines) + chr(10)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, code, data, extra_headers=None):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if MODE == "canary":
            self.send_header("X-Mode", "canary")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        if MODE == "canary":
            self.send_header("X-Mode", "canary")
        self.end_headers()

    def do_GET(self):
        start = time.time()
        path = self.path.split("?")[0]

        if path == "/":
            chaos_result = apply_chaos()
            status = chaos_result or 200
            if status == 200:
                self.send_json(200, {
                    "message": "Welcome to SwiftDeploy API",
                    "mode": MODE,
                    "version": APP_VERSION,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            else:
                self.send_json(500, {"error": "chaos error injection"})
        elif path == "/healthz":
            self.send_json(200, {
                "status": "ok",
                "mode": MODE,
                "uptime": round(time.time() - START_TIME, 2)
            })
        elif path == "/metrics":
            body = generate_metrics().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            duration = time.time() - start
            record_metrics("GET", "/metrics", 200, duration)
            return
        else:
            self.send_json(404, {"error": "not found"})
            status = 404

        duration = time.time() - start
        record_metrics("GET", path, status if path != "/" else 200, duration)

    def do_POST(self):
        start = time.time()
        if self.path == "/chaos":
            if MODE != "canary":
                self.send_json(403, {"error": "chaos only available in canary mode"})
                record_metrics("POST", "/chaos", 403, time.time() - start)
                return
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except Exception:
                self.send_json(400, {"error": "invalid JSON"})
                return
            with chaos_lock:
                m = data.get("mode")
                if m == "recover":
                    chaos_state.update({"mode": None, "active": False, "duration": 0, "rate": 0.0})
                    self.send_json(200, {"status": "chaos recovered"})
                elif m == "slow":
                    chaos_state.update({"mode": "slow", "active": True, "duration": data.get("duration", 2)})
                    self.send_json(200, {"status": "chaos active", "mode": "slow"})
                elif m == "error":
                    chaos_state.update({"mode": "error", "active": True, "rate": data.get("rate", 0.5)})
                    self.send_json(200, {"status": "chaos active", "mode": "error"})
                else:
                    self.send_json(400, {"error": "unknown chaos mode"})
            record_metrics("POST", "/chaos", 200, time.time() - start)
        else:
            self.send_json(404, {"error": "not found"})


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", APP_PORT), Handler)
    print(f"SwiftDeploy API running on port {APP_PORT} in {MODE} mode")
    server.serve_forever()
