import os
import sys

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from webhook.providers.gitlab import GitLabProvider

SECRET = "test-token"
BRANCH = "main"


class TestGitLabProvider:
    def setup_method(self):
        self.provider = GitLabProvider(secret=SECRET, branch=BRANCH)

    def test_validate_valid_token(self):
        body = b'{"ref": "refs/heads/main"}'
        assert self.provider.validate({"X-Gitlab-Token": SECRET}, body)

    def test_validate_missing_token(self):
        body = b'{"ref": "refs/heads/main"}'
        assert not self.provider.validate({}, body)

    def test_validate_wrong_token(self):
        body = b'{"ref": "refs/heads/main"}'
        assert not self.provider.validate({"X-Gitlab-Token": "wrong"}, body)

    def test_extract_ref(self):
        payload = {"ref": "refs/heads/main"}
        assert self.provider.extract_ref(payload) == "refs/heads/main"

    def test_extract_ref_missing(self):
        assert self.provider.extract_ref({}) is None

    def test_is_ping_always_false(self):
        assert not self.provider.is_ping({"X-Gitlab-Event": "Push Hook"})
        assert not self.provider.is_ping({})

    def test_matches_branch(self):
        assert self.provider.matches_branch("refs/heads/main")

    def test_matches_branch_wrong(self):
        assert not self.provider.matches_branch("refs/heads/develop")
