import logging
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum, auto
from typing import Iterable, Optional, Type

from .monitor import CommandOutput
from .render import TemplateType, render_template

MAIL_SUBJECT_WITH_DESCRIPTION = "{description:s}: change detected"
MAIL_SUBJECT_WITHOUT_DESCRIPTION = "Change detected on watched command output"

logger = logging.getLogger(__name__)


class MailBackend(Enum):
    SENDMAIL = auto()
    SMTPLIB = auto()


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
    mail_backend: MailBackend,
    from_address: str,
    to_addresses: Iterable[str],
    mail_server_url: str,
    encryption: MailEncryption,
    login_user: Optional[str] = None,
    login_password: Optional[str] = None,
    command_description: Optional[str] = None,
) -> None:
    def use_sendmail(message: MIMEMultipart) -> None:
        logging.debug("Send mail with sendmail")
        try:
            subprocess.run(["/usr/sbin/sendmail", "-t", "-oi"], input=message.as_bytes(), check=True)
        except subprocess.CalledProcessError as e:
            raise MailError("Could not send mail.") from e

    def use_smtplib(message: MIMEMultipart) -> None:
        logging.debug('Send mail with Python\'s builtin smtplib, encryption: "%s"', encryption.name)
        if encryption is MailEncryption.SSL:
            smtp_class: Type[smtplib.SMTP] = smtplib.SMTP_SSL
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

    backend_to_func = {
        MailBackend.SENDMAIL: use_sendmail,
        MailBackend.SMTPLIB: use_smtplib,
    }

    message = MIMEMultipart("alternative")
    message["From"] = from_address
    message["To"] = ", ".join(to_addresses)
    if command_description is None:
        message["Subject"] = MAIL_SUBJECT_WITHOUT_DESCRIPTION
    else:
        message["Subject"] = MAIL_SUBJECT_WITH_DESCRIPTION.format(description=command_description)
    content_plain = render_template(TemplateType.PLAIN, command, original_text, compare_text, command_description)
    content_html = render_template(TemplateType.HTML, command, original_text, compare_text, command_description)
    message_part_plain = MIMEText(content_plain, "plain", _charset="utf-8")
    message_part_html = MIMEText(content_html, "html", _charset="utf-8")
    message.attach(message_part_plain)
    message.attach(message_part_html)

    backend_to_func[mail_backend](message)
