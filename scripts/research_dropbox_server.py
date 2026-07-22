#!/usr/bin/env python3
"""Localhost dropbox for browser-side research scraping.

Calisphere's SPA pages are bot-blocked for curl, but in-page JavaScript run in
a real Chrome session can fetch them. Tool results back to the agent are
size-capped, so instead the page POSTs its harvest here:

    fetch('http://localhost:8931/save/<name>', {method: 'POST',
          headers: {'Content-Type': 'text/plain'}, body: JSON.stringify(data)})

Bodies land in data/calisphere/incoming/<name>.json (name is sanitized to
[a-z0-9._-]; no path traversal). Handles CORS + Chrome Private Network Access
preflights so a public-origin page may POST to localhost.
"""
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INCOMING = REPO / "data" / "calisphere" / "incoming"
PORT = 8931


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        m = re.fullmatch(r"/save/([a-z0-9._-]{1,80})", self.path)
        if not m or ".." in m.group(1):
            self.send_response(404)
            self._cors()
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        if length > 50_000_000:
            self.send_response(413)
            self._cors()
            self.end_headers()
            return
        body = self.rfile.read(length)
        INCOMING.mkdir(parents=True, exist_ok=True)
        name = m.group(1)
        if not name.endswith(".json"):
            name += ".json"
        (INCOMING / name).write_bytes(body)
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"saved {name} ({length} bytes)".encode())

    def log_message(self, fmt, *args):
        print("[dropbox]", fmt % args)


if __name__ == "__main__":
    print(f"research dropbox listening on http://localhost:{PORT}, saving to {INCOMING}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
