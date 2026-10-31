#!/usr/bin/env python3
"""Read-only Oracle production acceptance probe for AEGIS.
Run interactively with: sudo python3 scripts/oci-acceptance-readonly.py
No database writes, external scans, customer email, migrations or service starts.
"""
import json
import os
import pwd
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

API_URL = "http://127.0.0.1:8000"
PUBLIC_URL = "https://aegis-pentest-eg-api.duckdns.org"
ENV_PATH = Path("/etc/aegis/api.env")
PYTHON = "/srv/aegis/.venv/bin/python"
MODULE = "aegis.connections"

def out(label, ok, detail=""):
    print(("PASS " if ok else "CHECK") + " " + label + (": "+detail if detail else ""))
    return bool(ok)

def status(url):
    try:
        with urlopen(url, timeout=9) as response:
            return response.status, response.read(4096)
    except HTTPError as exc:
        return exc.code, exc.read(4096)

def main():
    if os.geteuid() != 0:
        print("STOP: run with sudo; this probe must read the protected API env.")
        return 1
    if not ENV_PATH.is_file() or not Path(PYTHON).is_file():
        print("STOP: protected API configuration/runtime missing.")
        return 1
    if ENV_PATH.is_symlink():
        print("STOP: unexpected environment symlink.")
        return 1

    print("AEGIS OCI READ-ONLY ACCEPTANCE PROBE")
    checks = []
    for service in ("postgresql", "redis-server", "caddy",
                    "aegis@api", "aegis@scanner",
                    "aegis@intelligence", "aegis@notifier"):
        proc = subprocess.run(["systemctl", "is-active", "--quiet", service],
                              capture_output=True, timeout=8)
        checks.append(out(service, proc.returncode == 0))

    try:
        code, data = status(API_URL+"/ready")
        ready = json.loads(data)
        checks.append(out("Internal API readiness", code == 200 and ready.get("ready") is True))
    except (ValueError, URLError, OSError, TimeoutError) as exc:
        checks.append(out("Internal API readiness", False, type(exc).__name__))

    # HTTPS checks restricted to AEGIS's own domain and explicitly selected routes.
    expected = {
        "/health": 200,
        "/auth/me": 503,
        "/auth/firebase/login": 503,
        "/openapi.json": 503,
    }
    for path, wanted in expected.items():
        try:
            got, data = status(PUBLIC_URL+path)
            ok = got == wanted
            if path == "/health" and got == 200:
                ok = ok and json.loads(data).get("database") == "reachable"
            checks.append(out("Public HTTPS "+path, ok, f"HTTP {got} (expected {wanted})"))
        except (ValueError, URLError, OSError, TimeoutError) as exc:
            checks.append(out("Public HTTPS "+path, False, type(exc).__name__))

    # Avoid "source" or shell evaluation of secrets. Parse the existing systemd
    # EnvironmentFile values as raw or JSON-quoted strings, never echo contents.
    env = {"PATH":"/usr/bin:/bin", "LANG":"C.UTF-8",
           "PYTHONPATH":"/srv/aegis/apps/api", "AEGIS_SERVICE_ROLE":"api"}
    try:
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#"):
                continue
            name, sep, value = line.partition("=")
            if not sep or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
                raise ValueError("Invalid environment line")
            if name in env:
                raise ValueError("Duplicate/restricted environment variable")
            env[name] = json.loads(value) if value.startswith('"') else value
        if env.get("AEGIS_ENV") != "production":
            raise ValueError("Not production env")
    except (OSError, UnicodeError, ValueError):
        print("CHECK Protected API environment: unreadable or unrecognized syntax")
        return 1

    # Drop privileges for the subprocess. The complete environment is passed
    # directly (never through argv, a shell, logs or GitHub).
    svc = pwd.getpwnam("aegis-api")
    env["HOME"] = svc.pw_dir
    try:
        task = subprocess.run(
            [PYTHON, "-m", MODULE], cwd="/srv/aegis",
            env=env, user=svc.pw_uid, group=svc.pw_gid, extra_groups=[],
            capture_output=True, text=True, timeout=35, check=False
        )
        # Do not dump stderr or unparsed stdout: they may contain secrets.
        report = json.loads(task.stdout)
        checkset = [
            ("Database/schema", report.get("database", {}).get("status") == "ready"),
            ("Redis queue", report.get("queue", {}).get("status") == "ready"),
            ("Firebase Admin", report.get("firebase", {}).get("status") == "ready"),
            ("Brevo SMTP auth (no email sent)", report.get("email", {}).get("status") == "ready"),
            ("Scanner worker", report.get("workers", {}).get("scanner_available") is True),
            ("Intelligence worker", report.get("workers", {}).get("intelligence_available") is True),
            ("Notifier worker", report.get("workers", {}).get("notifier_available") is True),
            ("Combined integration", report.get("ready") is True),
        ]
        for label, ok in checkset:
            checks.append(out(label, ok))
        checks.append(out("Diagnostic subprocess", task.returncode == 0))
    except (ValueError, OSError, subprocess.TimeoutExpired, KeyError) as exc:
        checks.append(out("Protected connection diagnostics", False, type(exc).__name__))

    scheduler=subprocess.run(["systemctl", "is-active", "--quiet", "aegis@scheduler"],
                            capture_output=True, timeout=8)
    print("INFO Recurring scheduler: " + ("running" if scheduler.returncode==0 else "not running"))
    print("INFO NOT TESTED: actual email delivery, Firebase customer login, authorization,")
    print("INFO live customer journey, independent security audit, backups or restore.")
    print("INFO No services, deployment, environment or customer records were changed.")
    print("AEGIS_ACCEPTANCE_READONLY_PASS" if all(checks) else "AEGIS_ACCEPTANCE_NEEDS_REVIEW")
    return 0 if all(checks) else 1

if __name__=="__main__":
    sys.exit(main())
