import pytest
import tempfile
import os
import yaml

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from linkcheck.config import LinkCheckConfig, DEFAULT_EXCLUSIONS


class TestLinkCheckConfigDisabled:
    def test_missing_file_returns_disabled(self):
        cfg = LinkCheckConfig("/nonexistent/linkcheck.yml")
        assert cfg.enabled is False

    def test_enabled_false_in_yaml(self, tmp_path):
        f = tmp_path / "linkcheck.yml"
        f.write_text(yaml.dump({"enabled": False}))
        cfg = LinkCheckConfig(str(f))
        assert cfg.enabled is False


class TestLinkCheckConfigEnabled:
    @pytest.fixture
    def config_file(self, tmp_path):
        data = {
            "enabled": True,
            "interval": 3600,
            "exclude": [r"^https?://example\.com"],
            "notifications": [
                {"type": "slack", "webhook_url": "https://hooks.slack.com/test"},
                {"type": "discord", "webhook_url": "https://discord.com/api/webhooks/test"},
            ],
        }
        f = tmp_path / "linkcheck.yml"
        f.write_text(yaml.dump(data))
        return str(f)

    def test_enabled(self, config_file):
        cfg = LinkCheckConfig(config_file)
        assert cfg.enabled is True

    def test_interval(self, config_file):
        cfg = LinkCheckConfig(config_file)
        assert cfg.interval == 3600

    def test_exclusions_merged(self, config_file):
        cfg = LinkCheckConfig(config_file)
        for pattern in DEFAULT_EXCLUSIONS:
            assert pattern in cfg.exclude_patterns
        assert r"^https?://example\.com" in cfg.exclude_patterns

    def test_notifications_parsed(self, config_file):
        cfg = LinkCheckConfig(config_file)
        assert len(cfg.notifications) == 2
        assert cfg.notifications[0]["type"] == "slack"

    def test_defaults_when_minimal(self, tmp_path):
        f = tmp_path / "linkcheck.yml"
        f.write_text(yaml.dump({"enabled": True}))
        cfg = LinkCheckConfig(str(f))
        assert cfg.interval == 21600
        assert cfg.notifications == []
        assert set(DEFAULT_EXCLUSIONS).issubset(set(cfg.exclude_patterns))
