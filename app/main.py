import os
import time
import random
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

MODE = os.environ.get("MODE", "stable")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
APP_PORT = int(os.environ.get("APP_PORT", "3000"))
START_TIME = time.time()

chaos_state = {"mode": None, "duration": 0, "rate": 0.0, "active": False}
chaos_lock = threading.Lock()


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
        self.do_GET()

    def do_GET(self):
        if self.path == "/":
            self.send_json(200, {
                "message": "Welcome to SwiftDeploy API",
                "mode": MODE,
                "version": APP_VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        elif self.path == "/healthz":
            self.send_json(200, {
                "status": "ok",
                "mode": MODE,
                "uptime": round(time.time() - START_TIME, 2)
            })
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/chaos":
            if MODE != "canary":
                self.send_json(403, {"error": "chaos only available in canary mode"})
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
        else:
            self.send_json(404, {"error": "not found"})


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", APP_PORT), Handler)
    print(f"SwiftDeploy API running on port {APP_PORT} in {MODE} mode")
    server.serve_forever()
