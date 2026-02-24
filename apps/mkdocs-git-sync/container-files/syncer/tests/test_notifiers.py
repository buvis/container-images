import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from linkcheck.checker import BrokenLink, CheckResult
from linkcheck.notifiers import (
    NotificationDispatcher,
    SlackNotifier,
    DiscordNotifier,
    WebhookNotifier,
    EmailNotifier,
    format_report,
)


@pytest.fixture
def check_result():
    return CheckResult(
        total_checked=100,
        broken_links=[
            BrokenLink(url="https://broken.com/page", source="index.html", status="404 Not Found"),
            BrokenLink(url="https://gone.com", source="about.html", status="410 Gone"),
        ],
    )


@pytest.fixture
def empty_result():
    return CheckResult(total_checked=50, broken_links=[])


class TestFormatReport:
    def test_contains_broken_links(self, check_result):
        report = format_report(check_result)
        assert "https://broken.com/page" in report
        assert "404 Not Found" in report
        assert "2" in report

    def test_truncates_long_list(self):
        links = [BrokenLink(url=f"https://b{i}.com", source="p.html", status="404") for i in range(30)]
        result = CheckResult(total_checked=200, broken_links=links)
        report = format_report(result, max_links=10)
        assert "and 20 more" in report


class TestSlackNotifier:
    @patch("linkcheck.notifiers.requests.post")
    def test_sends_to_webhook(self, mock_post, check_result):
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier({"webhook_url": "https://hooks.slack.com/test"})
        notifier.send(check_result)
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://hooks.slack.com/test"
        assert "text" in call_args[1]["json"]


class TestDiscordNotifier:
    @patch("linkcheck.notifiers.requests.post")
    def test_sends_to_webhook(self, mock_post, check_result):
        mock_post.return_value = MagicMock(status_code=204)
        notifier = DiscordNotifier({"webhook_url": "https://discord.com/api/webhooks/test"})
        notifier.send(check_result)
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "content" in call_args[1]["json"]


class TestWebhookNotifier:
    @patch("linkcheck.notifiers.requests.request")
    def test_sends_post(self, mock_req, check_result):
        mock_req.return_value = MagicMock(status_code=200)
        notifier = WebhookNotifier({"url": "https://example.com/hook"})
        notifier.send(check_result)
        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        assert args[0] == "POST"
        assert args[1] == "https://example.com/hook"

    @patch("linkcheck.notifiers.requests.request")
    def test_custom_method(self, mock_req, check_result):
        mock_req.return_value = MagicMock(status_code=200)
        notifier = WebhookNotifier({"url": "https://example.com/hook", "method": "PUT"})
        notifier.send(check_result)
        args, _ = mock_req.call_args
        assert args[0] == "PUT"


class TestEmailNotifier:
    @patch("linkcheck.notifiers.smtplib.SMTP")
    def test_sends_email(self, mock_smtp_cls, check_result):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        notifier = EmailNotifier({
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "from": "from@test.com",
            "to": "to@test.com",
        })
        notifier.send(check_result)
        mock_smtp.sendmail.assert_called_once()


class TestDispatcher:
    @patch("linkcheck.notifiers.requests.post")
    def test_dispatches_to_all(self, mock_post, check_result):
        mock_post.return_value = MagicMock(status_code=200)
        configs = [
            {"type": "slack", "webhook_url": "https://hooks.slack.com/test"},
            {"type": "discord", "webhook_url": "https://discord.com/api/webhooks/test"},
        ]
        dispatcher = NotificationDispatcher(configs)
        dispatcher.notify(check_result)
        assert mock_post.call_count == 2

    def test_skips_empty_result(self, empty_result):
        configs = [{"type": "slack", "webhook_url": "https://hooks.slack.com/test"}]
        dispatcher = NotificationDispatcher(configs)
        dispatcher.notify(empty_result)
