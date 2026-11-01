#!/usr/bin/env python3
"""Provision ONE operator-controlled pilot identity, without enabling public signup.

On the EXISTING Oracle VM, as ubuntu:
  sudo /srv/aegis/.venv/bin/python scripts/oci-provision-pilot-account.py

Operator must explicitly authorize ONE account creation and one verification
email. No production feature flags, Caddy, Vercel, schema, workers or scans
are changed. This is NOT an admin or customer-account bypass.

Public registration must remain disabled; never print secrets/passwords/tokens.
"""
import getpass
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import stat
import sys

ENV_FILE = Path("/etc/aegis/api.env")
RELEASE = Path("/srv/aegis-release-v1")
PILOT = re.compile(r"[a-z0-9._%-]+\+aegis-pilot[a-z0-9_-]*@gmail\.com\Z")
SAFE_ENV = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class Stop(Exception):
    pass


def read_environment():
    st = ENV_FILE.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != 0:
        raise Stop("Protected API settings file is not a root-owned regular file.")
    if stat.S_IMODE(st.st_mode) not in (0o600, 0o640):
        raise Stop("Unexpected production API config file permissions.")
    config = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or not SAFE_ENV.fullmatch(key) or key in config:
            raise Stop("Unrecognized/duplicate protected environment entry.")
        config[key] = json.loads(value) if value.startswith('"') else value
        if not isinstance(config[key], str):
            raise Stop("Unexpected environment entry type.")
    if config.get("AEGIS_ENV") != "production":
        raise Stop("Expected production API config was not found.")
    if config.get("AEGIS_PUBLIC_REGISTRATION_ENABLED", "false") != "false":
        raise Stop("Public signup must remain explicitly disabled.")
    if config.get("WEB_ORIGIN") != "https://aegis-pentest-eg.vercel.app":
        raise Stop("Unexpected user-facing production origin.")
    if config.get("SMTP_TLS") not in ("starttls", "implicit"):
        raise Stop("Encrypted SMTP is required.")
    if not config.get("DATABASE_URL") and not config.get("DATABASE_HOST"):
        raise Stop("Database credentials not configured.")
    return config


def main():
    if os.geteuid() != 0 or not sys.stdin.isatty():
        raise Stop("Run only via sudo in an interactive Oracle SSH shell.")
    if not (RELEASE / "apps/api/aegis/main.py").is_file():
        raise Stop("Live guarded v1 backend release not found.")
    config = read_environment()
    print("AEGIS ONE PILOT ACCOUNT — protected operator-only registration.")
    print("Public registration will remain DISABLED; one unverified user is created")
    print("only after explicit approval. No organization, admin role or scan is granted.")
    email = input("Your OWN Gmail +aegis-pilot address: ").strip().lower()
    if not PILOT.fullmatch(email) or len(email) > 254:
        raise Stop("Only an owned Gmail +aegis-pilot address is allowed.")
    print("Enter a NEW 12–128-character password for this pilot only.")
    password = getpass.getpass("Pilot account password (hidden): ")
    confirmation = getpass.getpass("Repeat pilot password (hidden): ")
    if password != confirmation or not 12 <= len(password) <= 128:
        raise Stop("Password confirmation mismatch or invalid length.")
    if password.lower() == email or len(set(password)) < 6:
        raise Stop("Choose a stronger unique password.")
    confirmation = ""
    print("One user record + one Brevo verification email will be created.")
    authorization = input("Type CREATE ONE PILOT ACCOUNT to authorize: ").strip()
    if authorization != "CREATE ONE PILOT ACCOUNT":
        raise Stop("Cancelled before any account/database changes.")
    authorization = ""

    # After collecting interactive input, drop root privileges *before*
    # establishing any database or email connection.
    os.chdir(RELEASE)
    runtime = pwd.getpwnam("aegis-api")
    os.environ.clear()
    os.environ.update(config)
    os.environ["PATH"] = "/usr/bin:/bin"
    os.environ["HOME"] = runtime.pw_dir
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.setgroups([])
    os.setgid(runtime.pw_gid)
    os.setuid(runtime.pw_uid)
    sys.path.insert(0, str(RELEASE / "apps/api"))
    from sqlalchemy import select
    from aegis.auth import hasher, audit
    from aegis.db import Session, engine
    from aegis.main import email_token
    from aegis.models import User

    if engine.dialect.name != "postgresql":
        raise Stop("Refusing pilot creation outside PostgreSQL.")
    with Session() as db:
        if db.scalar(select(User.id).where(User.email == email)) is not None:
            raise Stop("Pilot address already has an account. No duplicate created.")
        user = User(email=email, password=hasher.hash(password),
                    verified=False, active=True, superadmin=False)
        db.add(user)
        db.flush()
        try:
            # The existing AEGIS token routine emails a token to this verified
            # operator-controlled mailbox; only its SHA-256 digest is stored.
            email_token(db, user, "verify")
            audit(db, user, "account.operator_pilot_created", user.id)
            db.commit()
        except Exception:
            db.rollback()
            raise Stop("Pilot email/database transaction failed. No account committed.") from None
    password = ""
    config.clear()
    print("AEGIS_ONE_PILOT_ACCOUNT_CREATED")
    print("A verification email was submitted for the one pilot user.")
    print("Check Inbox/Spam, open the deployed AEGIS Console, use Verify email")
    print("with the ONE-TIME TOKEN, then sign in with the pilot email/password.")
    print("Firebase identity is separate: first authorize the production website")
    print("domain in Firebase, then link Google from Account Security.")
    print("Public account registration has NOT been enabled.")


if __name__ == "__main__":
    try:
        main()
    except (Stop, OSError, ValueError, EOFError, KeyboardInterrupt) as exc:
        if isinstance(exc, Stop):
            print("AEGIS_PILOT_SETUP_STOP: " + str(exc), file=sys.stderr)
        else:
            print("AEGIS_PILOT_SETUP_STOP: interrupted or invalid local setup.", file=sys.stderr)
        sys.exit(1)
