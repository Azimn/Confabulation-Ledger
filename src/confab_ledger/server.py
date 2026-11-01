"""Local-only, dependency-free research dashboard and JSON interface.

Not an authenticated network service; never bind this prototype to a public host.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .demo import seed_demo
from .ledger import Ledger, LedgerError

INDEX = Path(__file__).parent / "static" / "index.html"


def handler_factory(database: Path):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status: int, data: object) -> None:
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            route = urlsplit(self.path)
            if route.path == "/":
                raw = INDEX.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy",
                    "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'")
                self.end_headers()
                self.wfile.write(raw)
                return
            if route.path not in ("/api/state", "/api/character"):
                self.respond(404, {"error": "not found"})
                return
            params = parse_qs(route.query)
            at = params.get("at", [date.today().isoformat()])[0]
            try:
                with Ledger(database) as ledger:
                    if route.path == "/api/state":
                        self.respond(200, ledger.snapshot(at))
                    else:
                        char = params.get("id", [""])[0]
                        self.respond(200, ledger.character_view(char, at))
            except LedgerError as exc:
                self.respond(400, {"error": str(exc)})

        def do_POST(self):
            if urlsplit(self.path).path != "/api/claims":
                self.respond(404, {"error": "not found"})
                return
            if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{self.server.server_port}",
                                                  f"http://localhost:{self.server.server_port}"):
                self.respond(403, {"error": "cross-origin requests are disallowed"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 1 or size > 16384:
                    self.respond(413, {"error": "payload must be 1 to 16384 bytes"})
                    return
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise LedgerError("JSON object required")
                accepted = {"speaker", "subject", "predicate", "value", "text",
                            "effective_date", "speech_act", "visibility",
                            "reference_status", "context", "source_type", "source_key"}
                if set(data) - accepted:
                    raise LedgerError("unknown claim field")
                with Ledger(database) as ledger:
                    result = ledger.propose(**data)
                self.respond(201, result)
            except (LedgerError, TypeError, ValueError, json.JSONDecodeError) as exc:
                self.respond(400, {"error": str(exc)})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Confabulation Ledger local research laboratory")
    parser.add_argument("--db", default="ledger.sqlite3", help="SQLite database path")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--seed-demo", action="store_true")
    args = parser.parse_args()
    path = Path(args.db).resolve()
    with Ledger(path) as ledger:
        if args.seed_demo:
            print(seed_demo(ledger))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_factory(path))
    print(f"Open http://127.0.0.1:{server.server_port} (local-only; DB: {path})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
