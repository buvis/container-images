import os
import sys
import importlib
from unittest.mock import patch, MagicMock

# run.py lives inside the syncer/ package dir and uses bare imports
# (from syncer import Syncer). To import it in tests, we need to add its
# directory to sys.path and temporarily shadow the 'syncer' package.
_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

_orig_syncer = sys.modules.get("syncer")
_syncer_mod = importlib.import_module("syncer.syncer")
sys.modules["syncer"] = _syncer_mod

from run import main  # noqa: E402

if _orig_syncer is not None:
    sys.modules["syncer"] = _orig_syncer


class TestMainExitsOnBuildFailure:
    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_exits_when_initial_build_fails(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = False
        mock_syncer_cls.return_value = mock_syncer

        with patch("run.sys") as mock_sys:
            mock_sys.exit.side_effect = SystemExit(1)
            try:
                main()
            except SystemExit:
                pass
            mock_sys.exit.assert_called_with(1)

    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_enters_loop_when_build_succeeds(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config.webhook_enabled = False
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = True
        mock_syncer.update.return_value = False
        mock_syncer_cls.return_value = mock_syncer

        with patch("run.threading") as mock_threading:
            mock_event = MagicMock()
            mock_event.wait.side_effect = [False, KeyboardInterrupt]
            mock_threading.Event.return_value = mock_event

            try:
                main()
            except KeyboardInterrupt:
                pass

        # Confirms we entered the loop with poll source
        mock_syncer.update.assert_called_once_with(source="poll")


class TestWebhookIntegration:
    @patch("run.WebhookServer")
    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_webhook_server_starts_when_configured(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls, mock_ws_cls
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config.webhook_enabled = True
        mock_config.webhook_providers = {"github": "secret"}
        mock_config.webhook_port = 9000
        mock_config.branch = "main"
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = True
        mock_syncer.update.return_value = False
        mock_syncer_cls.return_value = mock_syncer

        # Break out after first iteration via the event.wait
        with patch("run.threading") as mock_threading:
            mock_event = MagicMock()
            mock_event.wait.side_effect = KeyboardInterrupt
            mock_threading.Event.return_value = mock_event

            try:
                main()
            except KeyboardInterrupt:
                pass

            mock_ws_cls.assert_called_once()
            mock_ws_cls.return_value.start.assert_called_once()

    @patch("run.WebhookServer")
    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_webhook_trigger_passes_source(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls, mock_ws_cls
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config.webhook_enabled = True
        mock_config.webhook_providers = {"github": "secret"}
        mock_config.webhook_port = 9000
        mock_config.branch = "main"
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = True
        mock_syncer.update.return_value = False
        mock_syncer_cls.return_value = mock_syncer

        with patch("run.threading") as mock_threading:
            mock_event = MagicMock()
            mock_event.wait.side_effect = [True, KeyboardInterrupt]
            mock_threading.Event.return_value = mock_event

            try:
                main()
            except KeyboardInterrupt:
                pass

        mock_syncer.update.assert_called_once_with(source="webhook")

    @patch("run.WebhookServer")
    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_webhook_server_not_started_when_not_configured(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls, mock_ws_cls
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config.webhook_enabled = False
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = True
        mock_syncer.update.return_value = False
        mock_syncer_cls.return_value = mock_syncer

        with patch("run.threading") as mock_threading:
            mock_event = MagicMock()
            mock_event.wait.side_effect = KeyboardInterrupt
            mock_threading.Event.return_value = mock_event

            try:
                main()
            except KeyboardInterrupt:
                pass

            mock_ws_cls.assert_not_called()
