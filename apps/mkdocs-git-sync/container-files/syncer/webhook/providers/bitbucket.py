import hmac
import logging

from webhook.providers.base import WebhookProvider

logger = logging.getLogger(__name__)


class BitbucketProvider(WebhookProvider):
    name = "bitbucket"

    def validate(self, headers: dict, body: bytes) -> bool:
        token = headers.get("X-Request-Path-Token")
        if not token:
            logger.warning("Bitbucket webhook rejected: missing token")
            return False
        if not hmac.compare_digest(token, self.secret):
            logger.warning("Bitbucket webhook rejected: invalid token")
            return False
        return True

    def extract_ref(self, payload: dict) -> str | None:
        try:
            name = payload["push"]["changes"][0]["new"]["name"]
            return f"refs/heads/{name}"
        except (KeyError, IndexError, TypeError):
            return None

    def is_ping(self, headers: dict) -> bool:
        return headers.get("X-Event-Key") == "diagnostics:ping"
