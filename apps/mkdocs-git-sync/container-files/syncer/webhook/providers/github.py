import hmac
import hashlib
import logging

from webhook.providers.base import WebhookProvider

logger = logging.getLogger(__name__)


class GitHubProvider(WebhookProvider):
    name = "github"

    def validate(self, headers: dict, body: bytes) -> bool:
        sig_header = headers.get("X-Hub-Signature-256")
        if not sig_header:
            logger.warning("GitHub webhook rejected: missing signature")
            return False
        expected = "sha256=" + hmac.new(
            self.secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            logger.warning("GitHub webhook rejected: invalid signature")
            return False
        return True

    def extract_ref(self, payload: dict) -> str | None:
        return payload.get("ref")

    def is_ping(self, headers: dict) -> bool:
        return headers.get("X-GitHub-Event") == "ping"
