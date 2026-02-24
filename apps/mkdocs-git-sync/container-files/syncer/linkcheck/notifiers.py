import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import List, Dict, Any

import requests

from linkcheck.checker import CheckResult

logger = logging.getLogger(__name__)


def format_report(result: CheckResult, max_links: int = 20) -> str:
    lines = [
        f"Link Check Report — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Checked: {result.total_checked} | Broken: {len(result.broken_links)}",
        "",
    ]
    shown = result.broken_links[:max_links]
    for link in shown:
        lines.append(f"- {link.url} (from {link.source}): {link.status}")
    remaining = len(result.broken_links) - max_links
    if remaining > 0:
        lines.append(f"... and {remaining} more")
    return "\n".join(lines)


class SlackNotifier:
    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config["webhook_url"]

    def send(self, result: CheckResult) -> None:
        report = format_report(result)
        try:
            resp = requests.post(self.webhook_url, json={"text": report}, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")


class DiscordNotifier:
    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config["webhook_url"]

    def send(self, result: CheckResult) -> None:
        report = format_report(result)
        try:
            resp = requests.post(self.webhook_url, json={"content": report}, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")


class WebhookNotifier:
    def __init__(self, config: Dict[str, Any]):
        self.url = config["url"]
        self.method = config.get("method", "POST")

    def send(self, result: CheckResult) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_checked": result.total_checked,
            "broken_count": len(result.broken_links),
            "broken_links": [
                {"url": l.url, "source": l.source, "status": l.status}
                for l in result.broken_links
            ],
        }
        try:
            resp = requests.request(self.method, self.url, json=payload, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")


class EmailNotifier:
    def __init__(self, config: Dict[str, Any]):
        self.smtp_host = config["smtp_host"]
        self.smtp_port = config.get("smtp_port", 587)
        self.from_addr = config["from"]
        self.to_addr = config["to"]
        self.username = config.get("username")
        self.password = config.get("password")

    def send(self, result: CheckResult) -> None:
        report = format_report(result)
        msg = EmailMessage()
        msg["Subject"] = f"Link Check: {len(result.broken_links)} broken link(s) found"
        msg["From"] = self.from_addr
        msg["To"] = self.to_addr
        msg.set_content(report)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.starttls()
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.sendmail(self.from_addr, self.to_addr, msg.as_string())
        except Exception as e:
            logger.error(f"Email notification failed: {e}")


NOTIFIER_MAP = {
    "slack": SlackNotifier,
    "discord": DiscordNotifier,
    "webhook": WebhookNotifier,
    "email": EmailNotifier,
}


class NotificationDispatcher:
    def __init__(self, configs: List[Dict[str, Any]]):
        self.notifiers = []
        for cfg in configs:
            notifier_type = cfg.get("type")
            cls = NOTIFIER_MAP.get(notifier_type)
            if cls:
                self.notifiers.append(cls(cfg))
            else:
                logger.warning(f"Unknown notifier type: {notifier_type}")

    def notify(self, result: CheckResult) -> None:
        if not result.broken_links:
            logger.info("No broken links, skipping notifications")
            return
        for notifier in self.notifiers:
            try:
                notifier.send(result)
            except Exception as e:
                logger.error(f"Notification failed: {e}")
