import os
import sys
import hmac
import hashlib
import json

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from webhook.providers.github import GitHubProvider

SECRET = "test-secret"
BRANCH = "main"


def _sign(body: bytes) -> str:
    mac = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={mac}"


class TestGitHubProvider:
    def setup_method(self):
        self.provider = GitHubProvider(secret=SECRET, branch=BRANCH)

    def test_validate_valid_signature(self):
        body = b'{"ref": "refs/heads/main"}'
        sig = _sign(body)
        assert self.provider.validate({"X-Hub-Signature-256": sig}, body)

    def test_validate_missing_signature(self):
        body = b'{"ref": "refs/heads/main"}'
        assert not self.provider.validate({}, body)

    def test_validate_invalid_signature(self):
        body = b'{"ref": "refs/heads/main"}'
        assert not self.provider.validate({"X-Hub-Signature-256": "sha256=bad"}, body)

    def test_extract_ref(self):
        payload = {"ref": "refs/heads/main"}
        assert self.provider.extract_ref(payload) == "refs/heads/main"

    def test_extract_ref_missing(self):
        assert self.provider.extract_ref({}) is None

    def test_is_ping_true(self):
        assert self.provider.is_ping({"X-GitHub-Event": "ping"})

    def test_is_ping_false(self):
        assert not self.provider.is_ping({"X-GitHub-Event": "push"})

    def test_is_ping_missing_header(self):
        assert not self.provider.is_ping({})

    def test_matches_branch(self):
        assert self.provider.matches_branch("refs/heads/main")

    def test_matches_branch_wrong(self):
        assert not self.provider.matches_branch("refs/heads/develop")
