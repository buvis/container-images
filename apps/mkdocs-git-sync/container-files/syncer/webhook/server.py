import hmac
import hashlib
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class _WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/hooks/github":
            self._respond(404, "not found")
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))

        sig_header = self.headers.get("X-Hub-Signature-256")
        if not sig_header:
            self._respond(401, "missing signature")
            return

        expected = "sha256=" + hmac.new(
            self.server.secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            logger.warning("Webhook rejected: invalid signature")
            self._respond(403, "invalid signature")
            return

        event_type = self.headers.get("X-GitHub-Event", "")
        if event_type == "ping":
            logger.info("Webhook ping received")
            self._respond(200, "pong")
            return

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, "invalid json")
            return

        ref = payload.get("ref", "")
        expected_ref = f"refs/heads/{self.server.branch}"
        if ref != expected_ref:
            logger.info(f"Webhook ignored: branch {ref} != {expected_ref}")
            self._respond(200, "ignored: branch mismatch")
            return

        logger.info(f"Webhook trigger: push to {ref}")
        self.server.trigger_event.set()
        self._respond(200, "rebuild triggered")

    def do_GET(self):
        self._respond(405, "method not allowed")

    def do_PUT(self):
        self._respond(405, "method not allowed")

    def _respond(self, code: int, message: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": message}).encode())

    def log_message(self, format, *args):
        logger.debug(f"Webhook HTTP: {format % args}")


class WebhookServer:
    def __init__(self, trigger_event: threading.Event, secret: str, branch: str, port: int):
        self._httpd = HTTPServer(("0.0.0.0", port), _WebhookHandler)
        self._httpd.trigger_event = trigger_event
        self._httpd.secret = secret
        self._httpd.branch = branch
        self._thread = None

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    def start(self):
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"Webhook server listening on port {self.port}")

    def stop(self):
        self._httpd.shutdown()
        if self._thread:
            self._thread.join()
