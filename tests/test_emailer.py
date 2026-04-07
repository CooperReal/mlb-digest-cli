from unittest.mock import MagicMock, patch

import pytest

from mlb_digest.emailer import build_message, send_email


def test_build_message_creates_multipart_email():
    msg = build_message(
        subject="Braves Daily - Mar 14, 2026",
        html_body="<html><body>Hello</body></html>",
        text_body="Hello",
        sender="sender@gmail.com",
        recipients=["user@example.com"],
    )

    assert msg["Subject"] == "Braves Daily - Mar 14, 2026"
    assert msg["From"] == "sender@gmail.com"
    assert msg["To"] == "user@example.com"
    assert msg.is_multipart()

    payloads = msg.get_payload()
    content_types = [p.get_content_type() for p in payloads]
    assert "text/plain" in content_types
    assert "text/html" in content_types


def test_build_message_handles_multiple_recipients():
    msg = build_message(
        subject="Test",
        html_body="<html>Hi</html>",
        text_body="Hi",
        sender="sender@gmail.com",
        recipients=["a@example.com", "b@example.com"],
    )

    assert "a@example.com" in msg["To"]
    assert "b@example.com" in msg["To"]


def test_send_email_calls_smtp():
    mock_smtp_instance = MagicMock()
    mock_smtp_class = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)

    with patch("mlb_digest.emailer.smtplib.SMTP_SSL", mock_smtp_class):
        send_email(
            subject="Test Subject",
            html_body="<html>Hello</html>",
            text_body="Hello",
            sender="sender@gmail.com",
            password="app-password",
            recipients=["user@example.com"],
            transport="gmail_smtp",
        )

    mock_smtp_instance.login.assert_called_once_with("sender@gmail.com", "app-password")
    mock_smtp_instance.send_message.assert_called_once()


def test_send_email_raises_on_unknown_transport():
    with pytest.raises(ValueError, match="carrier_pigeon"):
        send_email(
            subject="Test",
            html_body="<html>Hi</html>",
            text_body="Hi",
            sender="sender@gmail.com",
            password="pw",
            recipients=["user@example.com"],
            transport="carrier_pigeon",
        )


def test_send_email_raises_on_smtp_auth_failure():
    from smtplib import SMTPAuthenticationError

    mock_smtp_instance = MagicMock()
    mock_smtp_class = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)
    mock_smtp_instance.login.side_effect = SMTPAuthenticationError(535, b"Auth failed")

    with (
        patch("mlb_digest.emailer.smtplib.SMTP_SSL", mock_smtp_class),
        pytest.raises(SMTPAuthenticationError),
    ):
        send_email(
            subject="Test",
            html_body="<html>Hi</html>",
            text_body="Hi",
            sender="sender@gmail.com",
            password="bad-password",
            recipients=["user@example.com"],
            transport="gmail_smtp",
        )
