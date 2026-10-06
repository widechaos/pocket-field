"""Loopback-only HTTP interface. No remote APIs, request logs or telemetry."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engine import Selector

ROOT = Path(__file__).parent / "web"
SELECTOR = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, body, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self.respond(200, b'{"ready":true,"mode":"local CPU"}')
        elif path in ("/", "/index.html"):
            self.respond(200, (ROOT / "index.html").read_bytes(), "text/html")
        else:
            self.respond(404, b'{"error":"Not found"}')

    def do_POST(self):
        if self.path != "/api/select":
            self.respond(404, b'{"error":"Not found"}')
            return
        expected_hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if self.headers.get("Host") not in expected_hosts:
            self.respond(403, b'{"error":"Use the loopback address printed at startup"}')
            return
        # Browsers outside this loopback origin may not submit personal input.
        origin = self.headers.get("Origin")
        allowed = (f"http://{self.headers.get('Host')}",)
        if origin and origin not in allowed:
            self.respond(403, b'{"error":"Use the local app to submit your request"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("The request is too large or empty.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Expected an activity request.")
            result = SELECTOR.select(body.get("query"), body.get("minutes", 10),
                body.get("movement", "any"), body.get("place", "any"))
            self.respond(200, json.dumps(result).encode())
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            self.respond(400, json.dumps(dict(error=str(e))).encode())


if __name__ == "__main__":
    SELECTOR = Selector()
    port = int(os.environ.get("PORT", "8797"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Pocket Field ready at http://127.0.0.1:{server.server_port}", flush=True)
    server.serve_forever()
