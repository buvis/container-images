import hmac
import logging

from webhook.providers.base import WebhookProvider

logger = logging.getLogger(__name__)


class GitLabProvider(WebhookProvider):
    name = "gitlab"

    def validate(self, headers: dict, body: bytes) -> bool:
        token = headers.get("X-Gitlab-Token")
        if not token:
            logger.warning("GitLab webhook rejected: missing token")
            return False
        if not hmac.compare_digest(token, self.secret):
            logger.warning("GitLab webhook rejected: invalid token")
            return False
        return True

    def extract_ref(self, payload: dict) -> str | None:
        return payload.get("ref")

    def is_ping(self, headers: dict) -> bool:
        return False
