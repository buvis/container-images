from abc import ABC, abstractmethod
from email.message import EmailMessage
from smtplib import SMTP

from clara.config import get_settings


class EmailSender(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body_html: str) -> None:
        raise NotImplementedError


class SMTPSender(EmailSender):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str | None,
        sender: str,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    def send(self, to: str, subject: str, body_html: str) -> None:
        if not self.host:
            raise ValueError("SMTP host is not configured")
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content("This message contains an HTML digest.")
        message.add_alternative(body_html, subtype="html")
        with SMTP(self.host, self.port) as smtp:
            smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password or "")
            smtp.send_message(message)


def get_sender() -> EmailSender:
    settings = get_settings()
    smtp_password = (
        settings.smtp_password.get_secret_value()
        if settings.smtp_password
        else None
    )
    return SMTPSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=smtp_password,
        sender=settings.email_from,
    )
