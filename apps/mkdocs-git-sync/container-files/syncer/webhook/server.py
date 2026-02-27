import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from webhook.providers.github import GitHubProvider
from webhook.providers.gitlab import GitLabProvider
from webhook.providers.bitbucket import BitbucketProvider

logger = logging.getLogger(__name__)

PROVIDER_CLASSES = {
    "github": GitHubProvider,
    "gitlab": GitLabProvider,
    "bitbucket": BitbucketProvider,
}


class _WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        provider, path_token = self._resolve_provider()
        if provider is None:
            self._respond(404, "not found")
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        headers = dict(self.headers)

        # Inject path token as synthetic header for Bitbucket
        if path_token:
            headers["X-Request-Path-Token"] = path_token

        if not provider.validate(headers, body):
            self._respond(403, "authentication failed")
            return

        if provider.is_ping(headers):
            logger.info(f"Webhook ping received ({provider.name})")
            self._respond(200, "pong")
            return

        payload = provider.parse_body(body)
        if payload is None:
            self._respond(400, "invalid json")
            return

        ref = provider.extract_ref(payload)
        if ref is None or not provider.matches_branch(ref):
            logger.info(
                f"Webhook ignored ({provider.name}): ref {ref} != refs/heads/{provider.branch}"
            )
            self._respond(200, "ignored: branch mismatch")
            return

        logger.info(f"Webhook trigger ({provider.name}): push to {ref}")
        self.server.trigger_event.set()
        self._respond(200, "rebuild triggered")

    def _resolve_provider(self):
        """Match request path to a configured provider.

        Returns (provider, path_token) tuple. path_token is set only for
        Bitbucket (secret-in-URL). Returns (None, None) if no match.
        """
        path = self.path.rstrip("/")
        providers = self.server.providers

        # Exact match: /hooks/github, /hooks/gitlab
        if path in providers:
            return providers[path], None

        # Prefix match: /hooks/bitbucket/<token>
        bb_prefix = "/hooks/bitbucket/"
        if path.startswith(bb_prefix) and bb_prefix.rstrip("/") in providers:
            token = path[len(bb_prefix):]
            if token:
                return providers[bb_prefix.rstrip("/")], token

        return None, None

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
    def __init__(
        self,
        trigger_event: threading.Event,
        branch: str,
        port: int,
        providers: dict[str, str],
    ):
        self._httpd = HTTPServer(("0.0.0.0", port), _WebhookHandler)
        self._httpd.trigger_event = trigger_event

        # Build provider instances keyed by route path
        self._httpd.providers = {}
        for name, secret in providers.items():
            cls = PROVIDER_CLASSES.get(name)
            if cls is None:
                logger.warning(f"Unknown webhook provider: {name}")
                continue
            route = f"/hooks/{name}"
            self._httpd.providers[route] = cls(secret=secret, branch=branch)
            logger.info(f"Webhook route registered: {route} ({name})")

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
