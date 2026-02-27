import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class WebhookProvider(ABC):
    """Base class for webhook providers."""

    name: str = "unknown"

    def __init__(self, secret: str, branch: str):
        self.secret = secret
        self.branch = branch

    @abstractmethod
    def validate(self, headers: dict, body: bytes) -> bool:
        """Return True if request is authenticated."""

    @abstractmethod
    def extract_ref(self, payload: dict) -> str | None:
        """Extract branch ref from parsed payload. Return None if not found."""

    @abstractmethod
    def is_ping(self, headers: dict) -> bool:
        """Return True if this is a ping/test event."""

    def matches_branch(self, ref: str) -> bool:
        """Check if extracted ref matches the monitored branch."""
        expected = f"refs/heads/{self.branch}"
        return ref == expected

    def parse_body(self, body: bytes) -> dict | None:
        """Parse JSON body. Returns None on failure."""
        try:
            return json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return None
