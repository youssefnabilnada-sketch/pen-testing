"""Offline checks for malformed, untrusted HTML encountered during authorized discovery."""
import unittest
from aegis.crawler import PageLinks, run, safe_path
from aegis.safety import Observation


class MalformedHtmlDiscoveryTests(unittest.TestCase):
    def test_missing_link_rel_value_does_not_interrupt_page_discovery(self):
        parser = PageLinks()
        parser.feed('<link rel href="/ignored"><a href="/public">OK</a>')
        self.assertEqual(parser.links, [('/public', 'navigation')])

    def test_canonical_rel_is_case_insensitive_and_does_not_follow_unclear_links(self):
        parser = PageLinks()
        parser.feed('<link rel="CANONICAL alternate" href="/docs">'
                    '<link rel href="/admin">'
                    '<a href="/health">OK</a>')
        self.assertEqual(parser.links, [('/docs', 'canonical'), ('/health', 'navigation')])

    def test_compound_sensitive_actions_are_not_discovery_or_api_paths(self):
        for path in ('/api/logout-v2', '/account_disable', '/billing.refund',
                     '/token-refresh', '/admin/dashboard', '/password/reset'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                safe_path(path)
        self.assertEqual(safe_path('/api/health'), '/api/health')

    def test_repeated_malformed_link_elements_still_obey_bounded_traversal(self):
        calls = []
        def fetch(origin, path, **kwargs):
            calls.append(path)
            if path == '/':
                return Observation(200, [('Content-Type', 'text/html')],
                                   (b'<link rel href="/ignored">' * 200 +
                                    b'<a href="/docs">Docs</a>'))
            return Observation(200, [('Content-Type', 'text/html')], b'<html />')
        result = run('https://example.test', max_pages=2, max_depth=1, max_seconds=30,
                     prefixes=['/'], excluded=[], sitemaps=False,
                     check=lambda: None, fetch=fetch, sleep=lambda _: None)
        self.assertEqual(calls, ['/', '/docs'])
        self.assertEqual(result['requests_performed'], 2)
        self.assertEqual(result['paths'], ['/', '/docs'])


if __name__ == '__main__':
    unittest.main()
