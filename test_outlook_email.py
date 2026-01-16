"""Standalone script to verify Outlook COM sending with a specific account."""
from __future__ import annotations

from pathlib import Path

from utils.email_utils import send_outlook_email

DEFAULT_SENDER = "info@kdeducode.vn"
DEFAULT_RECIPIENTS = ["tranphinho@gmail.com", "phamvankieu92@gmail.com"]


def main() -> None:
    print("Attempting to send a test email via Outlook ...")
    subject = "[Test] Outlook COM connectivity"
    body = "This is a test message triggered from test_outlook_email.py"

    sender, delivered_to = send_outlook_email(
        DEFAULT_RECIPIENTS,
        subject,
        body,
        attachments=None,
        preferred_sender=DEFAULT_SENDER,
    )

    print("Sent successfully!")
    print(f"From: {sender}")
    print(f"To: {delivered_to}")


if __name__ == "__main__":
    main()