import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from continuum_bench.protocol import request_json, wait_ready


def test_wait_ready_has_global_deadline():
    with pytest.raises(TimeoutError):
        wait_ready("http://127.0.0.1:1", deadline_seconds=0.05)


def test_request_timeout_is_a_global_wall_clock_deadline():
    payload = json.dumps({"status": "ok", "padding": "x" * 40}).encode()

    class DripHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            for byte in payload:
                try:
                    self.wfile.write(bytes([byte]))
                    self.wfile.flush()
                except BrokenPipeError:
                    break
                time.sleep(0.01)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), DripHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    started = time.monotonic()
    try:
        with pytest.raises(RuntimeError, match="deadline|timed out"):
            request_json(f"http://127.0.0.1:{server.server_port}/", timeout=0.08)
        assert time.monotonic() - started < 0.3
    finally:
        server.shutdown()
