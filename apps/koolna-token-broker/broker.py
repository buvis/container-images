#!/usr/bin/env python3
"""Koolna token broker: stores and serves a Claude OAuth token.

Workspace pods call GET /token to retrieve the current token for the
CLAUDE_CODE_OAUTH_TOKEN environment variable. Administrators seed the
token via POST /bootstrap (called from the koolna-webui settings page
or directly via curl).

The token produced by `claude setup-token` is valid for ~1 year. No
refresh logic is needed; the broker is a thin persistence layer so the
token survives pod restarts and is accessible to all workspaces
in-cluster without exposing it as a broadly-visible K8s Secret.
"""

from __future__ import annotations

import http.server
import json
import logging
import os
import re
from pathlib import Path

TOKEN_FILE = Path(os.environ.get("HOME", "/home/node")) / ".claude" / "token"
LISTEN_PORT = 8080
BOOTSTRAP_MAX_BYTES = 8 * 1024
TOKEN_PATTERN = re.compile(r"^sk-ant-[a-z0-9]+-[A-Za-z0-9_-]+$")

_logger = logging.getLogger("koolna-token-broker")


def _read_token() -> str | None:
    try:
        value = TOKEN_FILE.read_text().strip()
        return value if value else None
    except FileNotFoundError:
        return None
    except OSError as exc:
        _logger.warning("failed to read %s: %s", TOKEN_FILE, exc)
        return None


def _write_token_atomic(token: str) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = TOKEN_FILE.with_suffix(".tmp")
    tmp.write_text(token)
    os.replace(tmp, TOKEN_FILE)


class _TokenHandler(http.server.BaseHTTPRequestHandler):
    server_version = "koolna-token-broker/0.2"

    def do_GET(self) -> None:
        if self.path == "/token":
            self._handle_token()
        elif self.path == "/health":
            self._handle_health()
        elif self.path == "/status":
            self._handle_status()
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path == "/bootstrap":
            self._handle_bootstrap()
        else:
            self.send_error(404)

    def _handle_token(self) -> None:
        token = _read_token()
        if not token:
            self.send_error(503, "no token available - broker not bootstrapped")
            return
        body = token.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _handle_health(self) -> None:
        if _read_token():
            self.send_response(200)
            body = b"ok\n"
        else:
            self.send_response(503)
            body = b"no token\n"
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_status(self) -> None:
        bootstrapped = _read_token() is not None
        status = {"bootstrapped": bootstrapped}
        body = json.dumps(status).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _handle_bootstrap(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            self.send_error(400, "missing or empty body")
            return
        if length > BOOTSTRAP_MAX_BYTES:
            self.send_error(413, f"payload exceeds {BOOTSTRAP_MAX_BYTES} bytes")
            return
        raw = self.rfile.read(length).decode(errors="replace").strip()
        if not raw:
            self.send_error(400, "empty token")
            return
        if not TOKEN_PATTERN.match(raw):
            self.send_error(400, "token does not match expected format (sk-ant-*)")
            return
        try:
            _write_token_atomic(raw)
        except OSError as exc:
            _logger.error("bootstrap: failed to write token: %s", exc)
            self.send_error(500, "failed to persist token")
            return
        _logger.info("bootstrap: token accepted (%d chars)", len(raw))
        body = b'{"ok":true}\n'
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        _logger.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # Ensure the token directory exists so bootstrap can write to it.
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    _logger.info("koolna-token-broker listening on :%d", LISTEN_PORT)
    if not _read_token():
        _logger.warning("no token found; broker will return 503 until bootstrapped")
    server = http.server.ThreadingHTTPServer(("", LISTEN_PORT), _TokenHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
