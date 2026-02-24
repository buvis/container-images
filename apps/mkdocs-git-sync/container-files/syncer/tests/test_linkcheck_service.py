import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from linkcheck.service import LinkCheckService
from linkcheck.checker import CheckResult, BrokenLink


class TestLinkCheckService:
    @patch("linkcheck.service.LinkChecker")
    @patch("linkcheck.service.NotificationDispatcher")
    @patch("linkcheck.service.LinkCheckConfig")
    def test_run_check_invokes_checker_and_dispatcher(self, mock_cfg_cls, mock_disp_cls, mock_checker_cls):
        mock_cfg = MagicMock()
        mock_cfg.enabled = True
        mock_cfg.exclude_patterns = []
        mock_cfg.notifications = []
        mock_cfg.interval = 3600
        mock_cfg_cls.return_value = mock_cfg

        result = CheckResult(total_checked=10, broken_links=[
            BrokenLink(url="https://broken.com", source="index.html", status="404")
        ])
        mock_checker_cls.return_value.run.return_value = result

        svc = LinkCheckService("/app/config/linkcheck.yml", "/app/site")
        svc.run_check()

        mock_checker_cls.return_value.run.assert_called_once()
        mock_disp_cls.return_value.notify.assert_called_once_with(result)

    @patch("linkcheck.service.LinkCheckConfig")
    def test_disabled_skips_everything(self, mock_cfg_cls):
        mock_cfg = MagicMock()
        mock_cfg.enabled = False
        mock_cfg_cls.return_value = mock_cfg

        svc = LinkCheckService("/app/config/linkcheck.yml", "/app/site")
        svc.run_check()  # should not raise

    @patch("linkcheck.service.LinkChecker")
    @patch("linkcheck.service.NotificationDispatcher")
    @patch("linkcheck.service.LinkCheckConfig")
    def test_should_run_respects_interval(self, mock_cfg_cls, mock_disp_cls, mock_checker_cls):
        mock_cfg = MagicMock()
        mock_cfg.enabled = True
        mock_cfg.exclude_patterns = []
        mock_cfg.notifications = []
        mock_cfg.interval = 3600
        mock_cfg_cls.return_value = mock_cfg

        mock_checker_cls.return_value.run.return_value = CheckResult(total_checked=0, broken_links=[])

        svc = LinkCheckService("/app/config/linkcheck.yml", "/app/site")
        assert svc.should_run() is True
        svc.run_check()
        assert svc.should_run() is False  # just ran

    @patch("linkcheck.service.LinkChecker")
    @patch("linkcheck.service.NotificationDispatcher")
    @patch("linkcheck.service.LinkCheckConfig")
    def test_run_check_after_build_ignores_interval(self, mock_cfg_cls, mock_disp_cls, mock_checker_cls):
        mock_cfg = MagicMock()
        mock_cfg.enabled = True
        mock_cfg.exclude_patterns = []
        mock_cfg.notifications = []
        mock_cfg.interval = 3600
        mock_cfg_cls.return_value = mock_cfg

        mock_checker_cls.return_value.run.return_value = CheckResult(total_checked=0, broken_links=[])

        svc = LinkCheckService("/app/config/linkcheck.yml", "/app/site")
        svc.run_check()  # sets last_run
        svc.run_check(after_build=True)  # should still run
        assert mock_checker_cls.return_value.run.call_count == 2
