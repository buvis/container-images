import os
import sys

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from unittest.mock import patch
from config import Config


class TestWebhookConfig:
    @patch.dict(os.environ, {"GIT_REPO": "https://github.com/test/repo"}, clear=False)
    def test_webhook_disabled_by_default(self):
        c = Config()
        assert c.webhook_providers == {}
        assert c.webhook_port == 9000
        assert c.webhook_enabled is False

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "GITHUB_WEBHOOK_SECRET": "mysecret",
        },
        clear=False,
    )
    def test_github_only(self):
        c = Config()
        assert c.webhook_providers == {"github": "mysecret"}
        assert c.webhook_enabled is True

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "GITLAB_WEBHOOK_SECRET": "gltoken",
        },
        clear=False,
    )
    def test_gitlab_only(self):
        c = Config()
        assert c.webhook_providers == {"gitlab": "gltoken"}
        assert c.webhook_enabled is True

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "BITBUCKET_WEBHOOK_SECRET": "bbtoken",
        },
        clear=False,
    )
    def test_bitbucket_only(self):
        c = Config()
        assert c.webhook_providers == {"bitbucket": "bbtoken"}
        assert c.webhook_enabled is True

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "GITHUB_WEBHOOK_SECRET": "gh",
            "GITLAB_WEBHOOK_SECRET": "gl",
            "BITBUCKET_WEBHOOK_SECRET": "bb",
        },
        clear=False,
    )
    def test_all_providers(self):
        c = Config()
        assert c.webhook_providers == {"github": "gh", "gitlab": "gl", "bitbucket": "bb"}
        assert c.webhook_enabled is True

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "GITHUB_WEBHOOK_SECRET": "s",
            "WEBHOOK_PORT": "8080",
        },
        clear=False,
    )
    def test_webhook_port_from_env(self):
        c = Config()
        assert c.webhook_port == 8080

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "WEBHOOK_PORT": "notanumber",
        },
        clear=False,
    )
    def test_webhook_port_invalid_uses_default(self):
        c = Config()
        assert c.webhook_port == 9000
