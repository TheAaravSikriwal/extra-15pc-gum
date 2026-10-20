"""The ground station's web page, served from the laptop with Python's own HTTP server.

GET /         the page
GET /state    the latest snapshot, as JSON
GET /events   the snapshot five times a second, as server-sent events (the page's live feed)
POST /param   {"name": ..., "value": ...}: sets a parameter, answers with the drone's value

No framework and nothing to install: the page is one file (page.html) with its own script."""

import asyncio
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = Path(__file__).with_name("page.html")
EVENTS_HZ = 5.0


def handler_for(station, run_coroutine=None):
    """A request handler bound to `station` (anything with snapshot() and an async
    set_param(name, value)). `run_coroutine` runs set_param on the station's event loop."""

    def call(coroutine):
        if run_coroutine is not None:
            return run_coroutine(coroutine)
        return asyncio.run_coroutine_threadsafe(coroutine, station.loop).result(timeout=10)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # quiet: the page polls
            pass

        def _send(self, code: int, body: bytes, kind: str):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802 (the stdlib's name)
            if self.path == "/":
                self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/state":
                self._send(200, json.dumps(station.snapshot()).encode(), "application/json")
            elif self.path.startswith("/events"):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                count = int(self.path.split("n=", 1)[1]) if "n=" in self.path else None
                sent = 0
                try:
                    while count is None or sent < count:
                        data = json.dumps(station.snapshot())
                        self.wfile.write(f"data: {data}\n\n".encode())
                        self.wfile.flush()
                        sent += 1
                        time.sleep(1 / EVENTS_HZ)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self._send(404, b"not here", "text/plain")

        def do_POST(self):  # noqa: N802
            if self.path != "/param":
                self._send(404, b"not here", "text/plain")
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                asked = json.loads(self.rfile.read(length))
                value = call(station.set_param(str(asked["name"]), float(asked["value"])))
            except Exception as e:  # noqa: BLE001 (the page shows what went wrong)
                self._send(400, json.dumps({"error": str(e)}).encode(), "application/json")
                return
            self._send(200, json.dumps({"name": asked["name"], "value": value}).encode(),
                       "application/json")  # fmt: skip

    return Handler


def serve(station, host: str = "127.0.0.1", port: int = 8714, run_coroutine=None):
    """Starts the page's server in its own thread; returns the server (its .server_address has
    the port, which is useful with port 0)."""
    server = ThreadingHTTPServer((host, port), handler_for(station, run_coroutine))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
