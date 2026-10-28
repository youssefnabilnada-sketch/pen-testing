"""Bounded, unauthenticated same-origin discovery. Every request uses pinned transport."""
import re
import time
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree
from . import safety

MAX_PAGES = 20
MAX_CANDIDATES = 200
UNSAFE_SEGMENTS = {'logout', 'signout', 'delete', 'remove', 'unsubscribe', 'checkout',
                   'purchase', 'pay', 'admin', 'wp-admin', 'login', 'signin', 'account',
                   'reset', 'restart', 'reboot', 'shutdown', 'flush', 'purge', 'revoke',
                   'disable', 'enable', 'activate', 'deactivate', 'suspend', 'terminate',
                   'password', 'token', 'session', 'billing', 'payment', 'refund'}


def safe_path(path):
    if not isinstance(path, str) or len(path) > 200:
        raise ValueError('Invalid path.')
    if not re.fullmatch(r'/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_.-]*', path):
        raise ValueError('Only plain absolute paths without queries or escapes are supported.')
    if any(p in ('.', '..') or any(word in UNSAFE_SEGMENTS for word in re.split(r'[-_.]', p.lower()))
           for p in path.split('/')):
        raise ValueError('Sensitive or ambiguous path excluded.')
    return path


def normalize(origin, base, href):
    if not isinstance(href, str) or any(c.isspace() or ord(c) < 32 for c in href) or '%' in href or '\\' in href:
        raise ValueError('Ambiguous URL.')
    parsed = urlsplit(urljoin(origin + base, href))
    if parsed.query or parsed.username or parsed.password:
        raise ValueError('Queries and credentials are excluded.')
    if safety.canonical_origin(f'{parsed.scheme}://{parsed.netloc}') != origin:
        raise ValueError('Outside the authorized origin.')
    return safe_path(parsed.path or '/')


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if len(self.links) >= MAX_CANDIDATES:
            return
        if tag == 'a' or (tag == 'link' and 'canonical' in (attrs.get('rel') or '').lower().split()):
            if attrs.get('href'):
                self.links.append((attrs['href'], 'canonical' if tag == 'link' else 'navigation'))


def run(origin, *, max_pages, max_depth, max_seconds, prefixes, excluded, sitemaps,
        check, fetch=None, clock=time.monotonic, sleep=time.sleep):
    """Sequential traversal: one request/sec; redirects, query variants and JS are excluded.

    Results are discovery evidence only and never authorize an assessment.
    The caller persists and rechecks the customer's immutable scope.
    """
    fetch = fetch or safety.fetch
    if type(max_pages) is not int or not 1 <= max_pages <= MAX_PAGES:
        raise ValueError('Page budget out of range.')
    if type(max_depth) is not int or not 0 <= max_depth <= 5:
        raise ValueError('Depth budget out of range.')
    if type(max_seconds) is not int or not 1 <= max_seconds <= 30:
        raise ValueError('Time budget out of range.')
    if not prefixes or len(prefixes) > 20 or len(excluded) > 20:
        raise ValueError('Invalid scope.')
    for path in prefixes + excluded:
        safe_path(path)
    def contains(prefix, path):
        return prefix == '/' or path == prefix or path.startswith(prefix.rstrip('/') + '/')
    def allowed(path):
        return any(contains(p, path) for p in prefixes) and not any(contains(p, path) for p in excluded)
    queue = deque((p, 0, 'seed') for p in prefixes)
    if sitemaps and allowed('/sitemap.xml'):
        queue.append(('/sitemap.xml', 0, 'sitemap'))
    queued = {row[0] for row in queue}
    records = []
    pages = []
    started = clock()
    requests = 0
    timed_out = False
    def record(path, depth, source, status):
        if len(records) < MAX_CANDIDATES:
            records.append({'path': path, 'depth': depth, 'source': source, 'status': status})
    while queue and requests < max_pages:
        check()
        if clock() - started >= max_seconds:
            timed_out = True
            break
        path, depth, source = queue.popleft()
        if not allowed(path):
            record(path, depth, source, 'excluded'); continue
        # Never sleep beyond the customer-approved wall-clock budget.
        if requests:
            remaining = max_seconds - (clock() - started)
            if remaining <= 0:
                timed_out = True
                break
            sleep(min(1, remaining))
        check()
        remaining = max_seconds - (clock() - started)
        if remaining <= 0:
            timed_out = True
            break
        scope = {'origin': origin, 'paths': [path], 'method': 'GET', 'request_limit': 1,
                 'timeout_seconds': min(5, remaining),
                 'type': 'explicit-path-response', 'purpose': 'link-discovery'}
        requests += 1
        try:
            with safety.authorization_guard(check):
                response = fetch(origin, path, assessment_scope=scope, discovery=True)
            check()
        except (OSError, safety.UnsafeTarget):
            check()  # Revocation is never swallowed as a per-page transport error.
            record(path, depth, source, 'request_failed'); continue
        # A slow fetch may finish at the deadline; discard its unapproved
        # follow-up candidates rather than extending the discovery run.
        if clock() - started >= max_seconds:
            timed_out = True
            record(path, depth, source, 'time_budget_exhausted')
            break
        media = next((v.split(';')[0].strip().lower() for k, v in response.headers if k.lower() == 'content-type'), '')
        if response.status != 200:
            record(path, depth, source, 'non_success'); continue
        links = []
        if media in ('text/html', 'application/xhtml+xml'):
            pages.append(path)
            parser = PageLinks(); parser.feed(response.body.decode('utf-8', errors='replace'))
            links = parser.links
        elif sitemaps and media in ('application/xml', 'text/xml'):
            # Never expand declarations/entities, including UTF-16 encoded documents.
            raw = response.body
            if b'\x00' in raw or b'<!' in raw:
                record(path, depth, source, 'unsafe_xml'); continue
            try:
                root = ElementTree.fromstring(raw)
                if root.tag.split('}')[-1] not in ('urlset', 'sitemapindex'):
                    raise ValueError('Unsupported sitemap')
                links = [(node.text or '', 'sitemap') for node in root.iter()
                         if node.tag.split('}')[-1] == 'loc'][:MAX_CANDIDATES]
            except (ElementTree.ParseError, ValueError):
                record(path, depth, source, 'invalid_xml'); continue
        else:
            record(path, depth, source, 'unsupported_content'); continue
        record(path, depth, source, 'discovered')
        if depth >= max_depth:
            continue
        for href, link_source in links:
            try:
                candidate = normalize(origin, path, href)
            except ValueError:
                # Do not retain raw links: they can contain credentials or private query data.
                record('[omitted]', depth + 1, link_source, 'unsafe_or_out_of_scope'); continue
            if not allowed(candidate):
                record(candidate, depth + 1, link_source, 'excluded'); continue
            if candidate in queued or len(queued) >= MAX_CANDIDATES:
                continue
            queued.add(candidate)
            queue.append((candidate, depth + 1, link_source))
    check()
    return {'paths': pages, 'records': records, 'requests_performed': requests,
            'remaining_candidates': len(queue), 'timed_out': timed_out,
            'budget_exhausted': bool(queue) or timed_out,
            'limitations': 'Unauthenticated sequential GET only. No redirects, queries, forms or JavaScript. Separate assessment approval required.'}
