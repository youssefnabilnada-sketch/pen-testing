#!/usr/bin/env python3
"""One opt-in, local-only registration/email/session acceptance test.

WARNING: Unlike the read-only probe, this creates a temporary test account
and sends one actual verification email to the explicitly supplied inbox.
The script attempts to deactivate the test account after successful verification.
It never opens Caddy, starts scans, enables scheduling, or prints secrets.
"""
import getpass
import http.client
import json
import re
import secrets
import sys
from http.cookies import SimpleCookie
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

INTERNAL = "http://127.0.0.1:8000"
PUBLIC = "https://aegis-pentest-eg-api.duckdns.org"
MAX_BODY = 4096


class Stop(Exception):
    pass


def call(base, method, path, data=None, headers=None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    h = {"Accept": "application/json"}
    if body is not None:
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    req = Request(base + path, data=body, headers=h, method=method)
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.status, resp.read(MAX_BODY), resp.headers
    except HTTPError as e:
        return e.code, e.read(MAX_BODY), e.headers
    except (OSError, URLError) as e:
        raise Stop(f"{method} {path} transport failed ({type(e).__name__})") from None


def expect(got, wanted, action):
    if got != wanted:
        raise Stop(f"{action}: HTTP {got}, expected {wanted}")


def read_json(data, action):
    try:
        return json.loads(data)
    except (TypeError, ValueError):
        raise Stop(f"{action}: malformed JSON (not printing response)") from None


def active_session(email, password):
    status, data, headers = call(INTERNAL, "POST", "/auth/login",
                                 {"email": email, "password": password})
    expect(status, 200, "Local login")
    csrf = read_json(data, "Local login").get("csrf")
    cookie = SimpleCookie()
    try:
        cookie.load(headers.get("Set-Cookie", ""))
        session = cookie["aegis_session"].value
    except (KeyError, ValueError):
        raise Stop("Local login: secure session cookie missing") from None
    if not isinstance(csrf, str) or len(csrf) < 20 or len(session) < 20:
        raise Stop("Local login: session/csrf malformed")
    # An HttpOnly/Secure browser cookie will not travel over HTTP normally.
    # Sending it explicitly *only over 127.0.0.1* verifies application
    # semantics, NOT real browser cookie transport or Vercel proxying.
    return {"Cookie": "aegis_session=" + session, "x-csrf-token": csrf}


def main():
    if sys.stdin.isatty() is False:
        raise Stop("Run interactively in the Ubuntu SSH terminal.")
    if sys.version_info < (3, 10):
        raise Stop("Python 3.10+ required.")
    print("AEGIS LOCAL-ONLY ACCOUNT ACCEPTANCE")
    print("This will create ONE temporary account in the current AEGIS database,")
    print("send ONE verification email to an inbox you own, then test session")
    print("and account deactivation. It will NOT open any public account route.")
    print("Never paste your token, password, or API keys into ChatGPT/GitHub.")
    # Confirm the external gateway is still blocking all account mutations.
    for route in ("/auth/register", "/auth/login", "/auth/firebase/login"):
        status, _, _ = call(PUBLIC, "POST", route, {})
        expect(status, 503, f"External gateway {route} must remain closed")
    status, data, _ = call(INTERNAL, "GET", "/ready")
    expect(status, 200, "Internal readiness")
    if read_json(data, "Internal readiness").get("ready") is not True:
        raise Stop("Internal API is not ready.")
    print("PASS: External writes blocked, local API ready")
    print("Use a *new* Gmail plus-alias (example: yourname+aegis-test1@gmail.com).")
    print("Do NOT use the primary inbox address without +aegis-test.")
    email = input("Test email you personally control: ").strip().lower()
    if not re.fullmatch(r"[a-z0-9._%+-]+\+aegis-test[a-z0-9_-]*@gmail\.com", email):
        raise Stop("Use a Gmail plus-address ending in +aegis-test...@gmail.com")
    if input("Type CREATE TEST ACCOUNT to authorize 1 DB account + 1 email: ").strip() != "CREATE TEST ACCOUNT":
        raise Stop("Cancelled; no test account created.")
    password = secrets.token_urlsafe(32)
    print("Registering test account locally...")
    status, _, _ = call(INTERNAL, "POST", "/auth/register",
                        {"email": email, "password": password})
    expect(status, 201, "Register local test account")
    print("PASS: Test account registered. Check your inbox / spam.")
    print("Copy ONLY the 'Alternative one-time token' from the AEGIS verify email.")
    print("Email links may point to the currently inactive production UI;")
    print("do not click the link. Paste the token into this SSH terminal instead.")
    token = getpass.getpass("One-time verification token (hidden): ").strip()
    if not (20 <= len(token) <= 150):
        raise Stop("Invalid verification token length; account remains unverified.")
    status, _, _ = call(INTERNAL, "POST", "/auth/verify", {"token": token})
    expect(status, 200, "Email token verification")
    token = ""
    print("PASS: Verified real inbox delivery and token")
    session = active_session(email, password)
    print("PASS: Local sign-in and session cookie generated")
    status, data, _ = call(INTERNAL, "GET", "/auth/me", headers=session)
    expect(status, 200, "Authenticated account lookup")
    account = read_json(data, "Account lookup")
    if (account.get("email") != email or account.get("verified") is not True
        or account.get("superadmin") is not False
        or account.get("organizations") != []):
        raise Stop("Test account has unexpected privileges or state. Stop and review.")
    print("PASS: Session identifies verified non-admin account with zero workspaces")
    status, _, _ = call(INTERNAL, "GET", "/admin/overview", headers=session)
    expect(status, 403, "Admin privilege isolation")
    print("PASS: Ordinary account denied admin overview")
    status, _, _ = call(INTERNAL, "POST", "/auth/logout", {}, headers={"Cookie": session["Cookie"]})
    expect(status, 403, "CSRF rejection")
    print("PASS: Logout without CSRF denied")
    status, _, _ = call(INTERNAL, "POST", "/auth/logout", {}, headers=session)
    expect(status, 200, "Authorized logout")
    status, _, _ = call(INTERNAL, "GET", "/auth/me", headers=session)
    expect(status, 401, "Session revocation after logout")
    print("PASS: Logout revoked session")
    session = active_session(email, password)
    status, _, _ = call(INTERNAL, "POST", "/auth/account/deactivate",
                        {"current_password": password, "confirm_deactivation": True},
                        headers=session)
    expect(status, 200, "Deactivate temporary account")
    status, _, _ = call(INTERNAL, "GET", "/auth/me", headers=session)
    expect(status, 401, "Deactivated session rejection")
    print("PASS: Temporary account deactivated; session revoked")
    print("AEGIS_LOCAL_ACCOUNT_ACCEPTANCE_PASS")
    print("NOTE: Account audit records are retained; no external browser auth")
    print("or Vercel session cookie behavior has been validated.")


if __name__ == "__main__":
    try:
        main()
    except (Stop, KeyboardInterrupt, EOFError) as e:
        print("AEGIS_LOCAL_ACCOUNT_ACCEPTANCE_STOPPED: " + (str(e) if isinstance(e, Stop) else "Interrupted"))
        print("If registration succeeded, the test account may need manual review.")
        sys.exit(1)
