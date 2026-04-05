#!/usr/bin/env python3
"""Koolna token broker: serves short-lived Claude OAuth access tokens.

Runs as a single-replica deployment so the `.credentials.json` file backing
the Claude CLI has exactly one writer, avoiding the rotating-refresh-token
races documented in anthropics/claude-code#24317 and #27933.

Workspace pods call GET /token to obtain a fresh access token for the
CLAUDE_CODE_OAUTH_TOKEN environment variable. The broker triggers a refresh
by invoking the Claude CLI when the current access token is close to expiry.
"""

from __future__ import annotations

import http.server
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path

CREDS_FILE = Path(os.environ.get("HOME", "/home/broker")) / ".claude" / ".credentials.json"
REFRESH_BUFFER_SECONDS = 300
REFRESH_TIMEOUT_SECONDS = 30
LISTEN_PORT = 8080

_refresh_lock = threading.Lock()
_logger = logging.getLogger("koolna-token-broker")


def _read_credentials() -> dict | None:
    try:
        return json.loads(CREDS_FILE.read_text())
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError) as exc:
        _logger.warning("failed to read %s: %s", CREDS_FILE, exc)
        return None


def _extract(creds: dict | None) -> tuple[str | None, int | None]:
    """Return (access_token, expires_at_unix_seconds) from a credentials blob."""
    if not creds:
        return None, None
    oauth = creds.get("claudeAiOauth") or {}
    access_token = oauth.get("accessToken")
    expires_at_raw = oauth.get("expiresAt")
    if expires_at_raw is None:
        return access_token, None
    # Heuristic: values >= 10^12 are milliseconds, smaller ones are seconds.
    expires_at_seconds = int(expires_at_raw / 1000) if expires_at_raw >= 10**12 else int(expires_at_raw)
    return access_token, expires_at_seconds


def _needs_refresh(expires_at_seconds: int | None) -> bool:
    if expires_at_seconds is None:
        return True
    return expires_at_seconds - time.time() < REFRESH_BUFFER_SECONDS


def _trigger_refresh() -> None:
    """Force Claude CLI to refresh its access token via a minimal prompt.

    The lock prevents concurrent HTTP handlers from spawning parallel refresh
    attempts, which would race on the credentials file.
    """
    with _refresh_lock:
        _, expires_at = _extract(_read_credentials())
        if not _needs_refresh(expires_at):
            return

        _logger.info("triggering claude refresh")
        try:
            result = subprocess.run(
                ["claude", "-p", "ok"],
                capture_output=True,
                timeout=REFRESH_TIMEOUT_SECONDS,
                check=False,
            )
        except FileNotFoundError:
            _logger.error("claude CLI not found in PATH")
            return
        except subprocess.TimeoutExpired:
            _logger.warning("claude refresh timed out after %ds", REFRESH_TIMEOUT_SECONDS)
            return

        if result.returncode != 0:
            stderr_snippet = result.stderr.decode(errors="replace")[:500]
            _logger.warning("claude refresh exited %d: %s", result.returncode, stderr_snippet)


def _get_current_token() -> str | None:
    access_token, expires_at = _extract(_read_credentials())
    if _needs_refresh(expires_at):
        _trigger_refresh()
        access_token, _ = _extract(_read_credentials())
    return access_token


class _TokenHandler(http.server.BaseHTTPRequestHandler):
    server_version = "koolna-token-broker/0.1"

    def do_GET(self) -> None:
        if self.path == "/token":
            self._handle_token()
        elif self.path == "/health":
            self._handle_health()
        else:
            self.send_error(404)

    def _handle_token(self) -> None:
        token = _get_current_token()
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
        if CREDS_FILE.exists():
            self.send_response(200)
            body = b"ok\n"
        else:
            self.send_response(503)
            body = b"no credentials\n"
        self.send_header("Content-Type", "text/plain; charset=utf-8")
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
    # Ensure the credentials directory exists so `kubectl cp` can seed a file
    # into it on a fresh PVC without the operator having to precreate it.
    CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _logger.info("koolna-token-broker listening on :%d", LISTEN_PORT)
    if not CREDS_FILE.exists():
        _logger.warning(
            "%s not found; broker will return 503 until bootstrapped", CREDS_FILE
        )
    server = http.server.ThreadingHTTPServer(("", LISTEN_PORT), _TokenHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
