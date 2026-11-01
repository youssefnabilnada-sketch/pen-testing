#!/usr/bin/env python3
"""One approved real Brevo SMTP delivery probe, with no account/database change.

Run ONLY on user's own Oracle VM, interactively: sudo python3 scripts/oci-brevo-delivery-probe.py
Credentials are read from root-protected API env, never printed or sent to GitHub.
SMTP accepted != delivered to inbox; user must independently verify the inbox.
"""
import json
import os
from pathlib import Path
import re
import secrets
import smtplib
import ssl
import stat
import sys
from email.message import EmailMessage

ENV = Path("/etc/aegis/api.env")
NEEDED = ("AEGIS_ENV", "SMTP_HOST", "SMTP_PORT", "SMTP_TLS",
          "SMTP_USERNAME", "SMTP_PASSWORD", "MAIL_FROM")


class Stop(Exception):
    pass


def read_private_settings():
    try:
        mode = ENV.lstat()
        if (not stat.S_ISREG(mode.st_mode) or mode.st_uid != 0
                or stat.S_IMODE(mode.st_mode) not in (0o600, 0o640)):
            raise Stop("Unexpected API settings file or permissions.")
        settings = {}
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#"):
                continue
            key, equals, value = line.partition("=")
            if not equals or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                raise Stop("Invalid protected settings syntax.")
            if key in settings:
                raise Stop("Duplicate protected setting.")
            settings[key] = json.loads(value) if value.startswith('"') else value
        for key in NEEDED:
            if key not in settings or not isinstance(settings[key], str):
                raise Stop("Required protected SMTP setting missing.")
        if (settings["AEGIS_ENV"] != "production"
                or settings["SMTP_HOST"] != "smtp-relay.brevo.com"
                or settings["SMTP_PORT"] != "587"
                or settings["SMTP_TLS"] != "starttls"):
            raise Stop("Expected production Brevo STARTTLS 587 configuration not found.")
        if not all(settings[k] for k in ("SMTP_USERNAME", "SMTP_PASSWORD", "MAIL_FROM")):
            raise Stop("Brevo login/sender configuration incomplete.")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", settings["MAIL_FROM"]):
            raise Stop("Mail sender is not a valid address.")
        return settings
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise Stop("Cannot validate protected SMTP settings (" + type(exc).__name__ + ").") from None


def main():
    if os.geteuid() != 0 or not sys.stdin.isatty():
        raise Stop("Run interactively with sudo on the owned Oracle VM.")
    settings = read_private_settings()
    print("AEGIS Brevo private delivery acceptance — no user accounts, tokens or scans.")
    inbox = input("Enter a Gmail +aegis-test address you own: ").strip().lower()
    if not re.fullmatch(r"[a-z0-9._%-]+\+aegis-test[a-z0-9_-]*@gmail\.com", inbox):
        raise Stop("Use only an owned Gmail plus-alias containing +aegis-test.")
    confirm = input("Type SEND ONE TEST EMAIL to authorize delivery: ").strip()
    if confirm != "SEND ONE TEST EMAIL":
        raise Stop("Cancelled; no email sent.")
    code = secrets.token_hex(5)
    message = EmailMessage()
    message["From"] = settings["MAIL_FROM"]
    message["To"] = inbox
    message["Subject"] = "AEGIS Security Cloud — mail delivery check"
    message["Message-ID"] = f"<aegis-delivery-{code}@aegis-pentest-eg.com>"
    message.set_content("AEGIS owned-operator Brevo delivery acceptance.\n"
                        "This is a one-time test message. No action is required.\n"
                        "Confirmation reference: " + code + "\n")
    try:
        with smtplib.SMTP("smtp-relay.brevo.com", 587, timeout=20) as smtp:
            smtp.ehlo()
            if not smtp.has_extn("starttls"):
                raise Stop("Brevo did not offer STARTTLS.")
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(settings["SMTP_USERNAME"], settings["SMTP_PASSWORD"])
            refused = smtp.send_message(message)
            if refused:
                raise Stop("Brevo refused the test recipient.")
    except Stop:
        raise
    except (OSError, smtplib.SMTPException, ssl.SSLError) as exc:
        raise Stop("Brevo delivery transport failed (" + type(exc).__name__ + ").") from None
    finally:
        settings.clear()
    print("AEGIS_BREVO_SMTP_ACCEPTED — one email submitted to Brevo.")
    print("Check the owned inbox (including Spam) for subject: AEGIS Security Cloud — mail delivery check")
    print("Delivery/verification/reset workflows are NOT confirmed until the message is actually received and separate account tests pass.")


if __name__ == "__main__":
    try:
        main()
    except (Stop, KeyboardInterrupt, EOFError) as exc:
        msg = str(exc) if isinstance(exc, Stop) else "Interrupted"
        print("AEGIS_BREVO_DELIVERY_STOP: " + msg, file=sys.stderr)
        sys.exit(1)
