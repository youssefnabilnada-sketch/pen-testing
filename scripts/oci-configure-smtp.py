#!/usr/bin/env python3
"""Configure transactional SMTP for AEGIS on OCI without exposing credentials.
Run interactively on Oracle with: sudo python3 scripts/oci-configure-smtp.py
Only encrypted STARTTLS via vetted provider endpoints; tests login, sends no mail.
"""
import getpass
import json
import os
import re
import smtplib
import ssl
import stat
import sys
import tempfile
from pathlib import Path

PATHS = (Path("/etc/aegis/api.env"), Path("/etc/aegis/notifier.env"))
CHOICES = {"1": "smtp-relay.brevo.com", "2": "smtp.gmail.com"}
REQUIRED = {
    "SMTP_HOST": "REPLACE-WITH-REAL-SMTP.invalid",
    "SMTP_PORT": "587",
    "SMTP_TLS": "starttls",
    "SMTP_USERNAME": "REPLACE_ME",
    "SMTP_PASSWORD": "REPLACE_ME",
    "MAIL_FROM": "REPLACE_ME",
}

def fail(message):
    print("SMTP_SETUP_STOPPED: " + message, file=sys.stderr)
    raise SystemExit(1)

def read_env(path):
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or (st.st_mode & 0o077) != 0o040 or st.st_uid != 0:
        fail("Unexpected permissions for " + path.name + "; inspect without printing secrets.")
    data = path.read_text("utf-8")
    lines = data.splitlines()
    for key, value in REQUIRED.items():
        matches = [line for line in lines if line.startswith(key + "=")]
        if len(matches) != 1 or matches[0] != key + "=" + value:
            fail("Already configured or unexpected SMTP environment: " + path.name + ". No changes made.")
    return data, st

def prompt():
    print("AEGIS SMTP SETUP — choose 1 (Brevo) or 2 (Gmail testing only).")
    print("Do NOT paste SMTP credentials into a chat or GitHub.")
    choice = input("Provider [1/2]: ").strip()
    if choice not in CHOICES:
        fail("Choose provider 1 or 2.")
    host = CHOICES[choice]
    username = input("SMTP login / username: ").strip()
    sender = input("Verified From email address: ").strip()
    password = getpass.getpass("SMTP key / app password (hidden input): ").strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", username):
        fail("SMTP login must be an email-format username.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", sender):
        fail("Sender must be a valid verified email address.")
    if choice == "2" and username.lower() != sender.lower():
        fail("For Gmail testing, From address must match the authenticated Gmail address.")
    if not 8 <= len(password) <= 512 or any(ord(c) < 33 or ord(c) > 126 for c in password):
        fail("SMTP key must contain 8–512 printable non-space ASCII characters.")
    return host, username, sender, password

def test_login(host, username, password):
    try:
        with smtplib.SMTP(host, 587, timeout=18) as server:
            server.ehlo()
            if not server.has_extn("starttls"):
                fail("SMTP provider did not advertise STARTTLS.")
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(username, password)
            code, _ = server.noop()
            if code != 250:
                fail("SMTP server did not accept NOOP after login.")
    except (OSError, smtplib.SMTPException, ssl.SSLError) as exc:
        fail("Encrypted SMTP connection or login failed (" + type(exc).__name__ + "). No settings were saved.")

def write_changes(data, st, host, username, sender, password):
    replacements = {
        "SMTP_HOST": host,
        "SMTP_PORT": "587",
        "SMTP_TLS": "starttls",
        "SMTP_USERNAME": username,
        "SMTP_PASSWORD": password,
        "MAIL_FROM": sender,
    }
    for name, old in REQUIRED.items():
        encoded = json.dumps(replacements[name], ensure_ascii=True)
        data = data.replace(name + "=" + old, name + "=" + encoded, 1)
    return data, st

def atomic_write(path, content, original_stat):
    fd, tempname = tempfile.mkstemp(prefix=".smtp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as dest:
            dest.write(content)
            dest.flush()
            os.fsync(dest.fileno())
        os.chown(tempname, original_stat.st_uid, original_stat.st_gid)
        os.chmod(tempname, stat.S_IMODE(original_stat.st_mode))
        os.replace(tempname, path)
    finally:
        if os.path.exists(tempname):
            os.unlink(tempname)

def main():
    if os.geteuid() != 0:
        fail("Run with sudo on the Oracle SSH shell.")
    if not sys.stdin.isatty():
        fail("An interactive SSH terminal is required.")
    originals = [read_env(path) for path in PATHS]
    host, username, sender, password = prompt()
    print("Checking SMTP TLS and authentication without sending any email...")
    test_login(host, username, password)
    for path, (data, st) in zip(PATHS, originals):
        new_data, metadata = write_changes(data, st, host, username, sender, password)
        atomic_write(path, new_data, metadata)
    print("AEGIS_SMTP_AUTH_CONFIGURED")
    print("Encrypted SMTP login succeeded; API/notifier settings saved with original restrictive permissions.")
    print("No customer email was sent. Inbox deliverability, Firebase UI login, migrations, API and Vercel still require testing.")

if __name__ == "__main__":
    main()
