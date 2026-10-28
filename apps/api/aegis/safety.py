"""Small bounded HTTP transport. DNS is validated once, then IP pinned for connect.
No environment proxies, redirects, URL credentials, custom ports or caller headers.
"""
import http.client
import ipaddress
import os
import socket
import ssl
import re
import threading
from contextvars import ContextVar
from contextlib import contextmanager
from urllib.parse import urlsplit
from dataclasses import dataclass

class UnsafeTarget(ValueError):
    pass

FIXTURE_ORIGIN = 'http://fixture'
FIXTURE_IP = '172.29.0.10'
MAX_BODY = 65536
_authorization_guard=ContextVar('assessment_authorization_guard',default=None)

@contextmanager
def authorization_guard(check):
    token=_authorization_guard.set(check)
    try:yield
    finally:_authorization_guard.reset(token)

def recheck_authorization():
    check=_authorization_guard.get()
    if check is not None:check()


def canonical_origin(value):
    if any(c.isspace() or ord(c) < 32 for c in value) or '\\' in value or '%' in value:
        raise UnsafeTarget('Ambiguous URL rejected.')
    try:
        p = urlsplit(value)
        if p.scheme not in ('http', 'https') or p.username or p.password or not p.hostname:
            raise UnsafeTarget('Only HTTP(S) origins without credentials are allowed.')
        host = p.hostname.encode('idna').decode('ascii').lower()
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', host) or '..' in host:
            raise UnsafeTarget('Use a canonical DNS hostname.')
        if p.port not in (None, 443 if p.scheme == 'https' else 80):
            raise UnsafeTarget('Custom ports are not supported.')
        if p.path not in ('', '/') or p.query or p.fragment:
            raise UnsafeTarget('Enter the origin only; choose assessment paths separately.')
        return f'{p.scheme}://{host}'
    except (ValueError, UnicodeError) as exc:
        raise UnsafeTarget(str(exc)) from exc


def resolve(origin):
    p = urlsplit(canonical_origin(origin))
    port = 443 if p.scheme == 'https' else 80
    try:
        addresses = {x[4][0] for x in socket.getaddrinfo(p.hostname, port, type=socket.SOCK_STREAM)}
    except OSError as exc:
        raise UnsafeTarget('Hostname resolution failed.') from exc
    if not addresses:
        raise UnsafeTarget('No destination addresses.')
    fixture_allowed = os.getenv('LOCAL_FIXTURE_MODE') == 'true' and origin == FIXTURE_ORIGIN
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if fixture_allowed and str(ip) == FIXTURE_IP:
            continue
        # IPv4-mapped, transition, non-global, multicast, metadata and private addresses fail closed.
        if not ip.is_global or ip.is_multicast or (ip.version == 6 and (ip.ipv4_mapped or ip.sixtofour or ip.teredo)):
            raise UnsafeTarget('Private, special-use or internal destinations are blocked.')
        if fixture_allowed:
            raise UnsafeTarget('Fixture resolved outside its isolated test address.')
    return p.hostname, port, sorted(addresses)[0], p.scheme

@dataclass
class Observation:
    status: int
    headers: list[tuple[str, str]]
    body: bytes
    tls: dict | None = None


def fetch(origin, path='/', *, verification=False, assessment_scope=None, discovery=False):
    if discovery and (assessment_scope is None or assessment_scope.get('purpose')!='link-discovery'):
        raise UnsafeTarget('Explicit discovery authorization required.')
    # Challenge paths are server-generated; arbitrary endpoint/path selection is intentionally absent.
    if assessment_scope is not None:
        from .scope import require_supported_scope
        require_supported_scope(assessment_scope,origin,allow_auxiliary=True)
        if path not in assessment_scope['paths']:raise UnsafeTarget('Path not authorized.')
    if assessment_scope is None and path != '/' and not (verification and re.fullmatch(r'/\.well-known/aegis-[A-Za-z0-9_-]{20,100}\.txt', path)):
        raise UnsafeTarget('Path is outside the supported assessment scope.')
    recheck_authorization()
    host, port, ip, scheme = resolve(origin)
    recheck_authorization()
    # Every authorized transport observes its approved request timeout.
    # For ordinary assessments this is five seconds; discovery may use a
    # strictly shorter value when its remaining customer-approved budget shrinks.
    timeout = assessment_scope['timeout_seconds'] if assessment_scope is not None else 5
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    sock = socket.create_connection((ip, port), timeout=timeout)
    tls = None
    def abort_socket():
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
    deadline = threading.Timer(timeout, abort_socket)
    deadline.daemon = True
    deadline.start()
    try:
        if scheme == 'https':
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
            cert = sock.getpeercert()
            tls = {'version': sock.version(), 'expires': ssl.cert_time_to_seconds(cert['notAfter'])}
        conn.sock = sock
        recheck_authorization()
        conn.request('GET', path, headers={'Host': host, 'User-Agent': 'AEGIS-Authorized-Configuration-Assessment/0.1', 'Accept-Encoding': 'identity', 'Connection': 'close'})
        response = conn.getresponse()
        if 300 <= response.status < 400:
            raise UnsafeTarget('Redirect not followed: a separately authorized origin is required.')
        headers = response.getheaders()
        # Application does not persist body or cookie values. Only verification reads the bounded body.
        body = response.read(MAX_BODY+1) if verification or discovery else b''
        if len(body) > MAX_BODY:
            raise UnsafeTarget('Response exceeds size limit.')
        return Observation(response.status, headers, body, tls)
    finally:
        deadline.cancel()
        conn.close()
        sock.close()
