import pytest
from aegis.crawler import run, normalize
from aegis.safety import Observation
from aegis.db import Session
from aegis.models import Authorization
from test_assessment import authorized


def crawl(fetch, **changes):
    return run('https://example.test', max_pages=changes.pop('max_pages', 20),
               max_depth=changes.pop('max_depth', 4), max_seconds=30,
               prefixes=['/'], excluded=['/private'], sitemaps=changes.pop('sitemaps', False),
               check=changes.pop('check', lambda: None), fetch=fetch, sleep=lambda _: None, **changes)


def test_nested_navigation_sitemap_and_exact_budgets():
    pages = {'/': '<a href="/docs/">Docs</a><a href="/private/data">Private</a>',
             '/docs/': '<a href="guide">Guide</a><a href="/docs/guide#intro">Duplicate</a>',
             '/docs/guide': '<a href="/last">Last</a><a href="https://other.test/">Outside</a>',
             '/last': '', '/from-map': ''}
    calls = []
    def fetch(origin, path, **kw):
        calls.append(path)
        assert kw['assessment_scope']['paths'] == [path]
        if path == '/sitemap.xml':
            return Observation(200, [('Content-Type', 'text/xml')], b'<urlset><url><loc>https://example.test/from-map</loc></url></urlset>')
        return Observation(200, [('Content-Type', 'text/html')], pages[path].encode())
    result = crawl(fetch, sitemaps=True)
    assert set(result['paths']) == set(pages)
    assert len(calls) == 6 and len(set(calls)) == 6
    assert any(row['status'] == 'excluded' for row in result['records'])
    calls.clear()
    result = crawl(fetch, max_pages=2)
    assert calls == ['/', '/docs/'] and result['budget_exhausted']


@pytest.mark.parametrize('href', ['https://evil.test/x', '//evil.test/x', '/%2e%2e/x',
                                  '/logout', '/admin/users', '/x?token=secret', '/a\\b'])
def test_unsafe_links_fail_closed(href):
    with pytest.raises(ValueError): normalize('https://example.test', '/', href)


def test_scope_revocation_stops_before_next_fetch():
    calls = []
    def check():
        if calls: raise RuntimeError('revoked')
    def fetch(origin, path, **kw):
        calls.append(path)
        return Observation(200, [('Content-Type', 'text/html')], b'<a href="/next">Next</a>')
    with pytest.raises(RuntimeError): crawl(fetch, check=check)
    assert calls == ['/']


def test_depth_limit_and_query_loops():
    calls = []
    def fetch(origin, path, **kw):
        calls.append(path)
        return Observation(200, [('Content-Type', 'text/html')], b'<a href="/next">Next</a><a href="/?page=2">Loop</a>')
    result = crawl(fetch, max_depth=0)
    assert calls == ['/'] and result['paths'] == ['/']


def test_recursive_api_consent_separate_from_assessment(client, mail, monkeypatch):
    from aegis import safety
    org, asset, _ = authorized(client, mail, monkeypatch)
    monkeypatch.setattr(safety, 'fetch', lambda *a, **kw: Observation(200, [('Content-Type', 'text/html')], b''))
    assert client.post(f'/assets/{asset}/discover-recursive', json={'accepted': False}).status_code == 403
    result = client.post(f'/assets/{asset}/discover-recursive', json={'accepted': True, 'max_pages': 1})
    assert result.status_code == 200 and result.json()['paths'] == ['/']
    with Session() as db:
        auth = db.get(Authorization, result.json()['authorization_id'])
        assert auth.revoked and auth.scope['purpose'] == 'recursive-discovery'
    assert client.post(f'/assets/{asset}/assessments', json={'authorization_id': result.json()['authorization_id']}).status_code == 403
    history = client.get(f'/assets/{asset}/discovery-history').json()
    assert history[0]['scope']['result']['paths'] == ['/'] and history[0]['active'] is False


def test_more_than_three_assessment_paths_are_explicitly_authorized(client, mail, monkeypatch):
    org, asset, _ = authorized(client, mail, monkeypatch)
    paths = [f'/page{i}' for i in range(20)]
    result = client.post(f'/assets/{asset}/authorize', json={'accepted': True, 'paths': paths})
    assert result.status_code == 200 and result.json()['scope']['request_limit'] == 20
    assert client.post(f'/assets/{asset}/authorize', json={'accepted': True, 'paths': paths + ['/overflow']}).status_code == 422
