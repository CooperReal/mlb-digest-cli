import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


def build_message(
    subject: str,
    html_body: str,
    text_body: str,
    sender: str,
    recipients: list[str],
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg


@retry(stop=stop_after_attempt(2), wait=wait_fixed(5), reraise=True)
def _send_gmail_smtp(msg: MIMEMultipart, sender: str, password: str) -> None:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)


def send_email(
    subject: str,
    html_body: str,
    text_body: str,
    sender: str,
    password: str,
    recipients: list[str],
    transport: str = "gmail_smtp",
) -> None:
    if transport != "gmail_smtp":
        raise ValueError(f"Unknown transport: {transport}. Only 'gmail_smtp' is supported.")

    msg = build_message(subject, html_body, text_body, sender, recipients)

    logger.info("Sending email to %s via %s", recipients, transport)
    _send_gmail_smtp(msg, sender, password)
    logger.info("Email sent successfully")
