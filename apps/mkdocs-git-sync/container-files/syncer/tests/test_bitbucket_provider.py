import os
import sys

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from webhook.providers.bitbucket import BitbucketProvider

SECRET = "test-url-token"
BRANCH = "main"


class TestBitbucketProvider:
    def setup_method(self):
        self.provider = BitbucketProvider(secret=SECRET, branch=BRANCH)

    def test_validate_valid_token(self):
        body = b'{"push": {"changes": []}}'
        assert self.provider.validate({"X-Request-Path-Token": SECRET}, body)

    def test_validate_missing_token(self):
        body = b'{"push": {"changes": []}}'
        assert not self.provider.validate({}, body)

    def test_validate_wrong_token(self):
        body = b'{"push": {"changes": []}}'
        assert not self.provider.validate({"X-Request-Path-Token": "wrong"}, body)

    def test_extract_ref(self):
        payload = {
            "push": {
                "changes": [{"new": {"name": "main", "type": "branch"}}]
            }
        }
        assert self.provider.extract_ref(payload) == "refs/heads/main"

    def test_extract_ref_empty_changes(self):
        payload = {"push": {"changes": []}}
        assert self.provider.extract_ref(payload) is None

    def test_extract_ref_missing_push(self):
        assert self.provider.extract_ref({}) is None

    def test_extract_ref_no_new(self):
        payload = {"push": {"changes": [{"old": {"name": "main"}}]}}
        assert self.provider.extract_ref(payload) is None

    def test_is_ping_true(self):
        assert self.provider.is_ping({"X-Event-Key": "diagnostics:ping"})

    def test_is_ping_false(self):
        assert not self.provider.is_ping({"X-Event-Key": "repo:push"})

    def test_is_ping_missing_header(self):
        assert not self.provider.is_ping({})

    def test_matches_branch(self):
        assert self.provider.matches_branch("refs/heads/main")

    def test_matches_branch_wrong(self):
        assert not self.provider.matches_branch("refs/heads/develop")
