import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum, auto
from typing import Iterable, Optional, Type

from .monitor import CommandOutput
from .render import TemplateType, render_template

MAIL_SUBJECT = "Change detected on watched command output"

logger = logging.getLogger(__name__)


class MailEncryption(Enum):
    NONE = auto()
    STARTTLS = auto()
    SSL = auto()


class MailPorts:
    PLAIN = 25
    STARTTLS = 587
    SSL = 465


class MailError(Exception):
    pass


def send_mail(
    command: str,
    original_text: CommandOutput,
    compare_text: CommandOutput,
    from_address: str,
    to_addresses: Iterable[str],
    mail_server_url: str,
    encryption: MailEncryption,
    login_user: Optional[str] = None,
    login_password: Optional[str] = None,
) -> None:
    message = MIMEMultipart("alternative")
    message["From"] = from_address
    message["To"] = ", ".join(to_addresses)
    message["Subject"] = MAIL_SUBJECT
    content_plain = render_template(TemplateType.PLAIN, command, original_text, compare_text)
    content_html = render_template(TemplateType.HTML, command, original_text, compare_text)
    message_part_plain = MIMEText(content_plain, "plain", _charset="utf-8")
    message_part_html = MIMEText(content_html, "html", _charset="utf-8")
    message.attach(message_part_plain)
    message.attach(message_part_html)
    if encryption is MailEncryption.SSL:
        smtp_class = smtplib.SMTP_SSL  # type: Type[smtplib.SMTP]
        port = MailPorts.SSL
    elif encryption is MailEncryption.STARTTLS:
        smtp_class = smtplib.SMTP
        port = MailPorts.STARTTLS
    else:
        smtp_class = smtplib.SMTP
        port = MailPorts.PLAIN
    server = smtp_class(mail_server_url, port)
    try:
        if encryption is MailEncryption.STARTTLS:
            server.starttls()
        # Do not send credentials without encryption
        if encryption is not MailEncryption.NONE and login_user and login_password:
            server.login(login_user, login_password)
        else:
            logging.warning(
                "No encryption is used for mail transfer. "
                "In this mode, no credentials are sent for security reasons."
            )
        server.send_message(message)
        server.close()
    except smtplib.SMTPException as e:
        raise MailError("Could not send mail.") from e
