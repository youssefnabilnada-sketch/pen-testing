"""Dependency-light regression tests for bounded, explicitly authorized discovery."""
import math
import unittest
from unittest.mock import patch

from aegis.crawler import run
from aegis.safety import Observation, UnsafeTarget, fetch
from aegis.scope import require_supported_scope


ORIGIN = 'https://example.test'


class Clock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds


class DiscoveryDeadlineTests(unittest.TestCase):
    def test_timeout_budget_reduces_before_followup_request(self):
        clock = Clock()
        timeouts = []

        def fake_fetch(origin, path, *, assessment_scope, discovery):
            self.assertTrue(discovery)
            require_supported_scope(assessment_scope, origin, allow_auxiliary=True)
            timeouts.append(assessment_scope['timeout_seconds'])
            clock.sleep(1.9 if path == '/' else 0.5)
            return Observation(200, [('Content-Type', 'text/html')], b'<a href="/next">Next</a>')

        result = run(ORIGIN, max_pages=3, max_depth=2, max_seconds=3, prefixes=['/'],
                     excluded=[], sitemaps=False, check=lambda: None, fetch=fake_fetch,
                     clock=clock.now, sleep=clock.sleep)
        self.assertEqual(result['paths'], ['/'])
        self.assertTrue(result['timed_out'])
        self.assertTrue(result['budget_exhausted'])
        self.assertEqual(result['requests_performed'], 2)
        self.assertEqual(timeouts[0], 3.0)
        self.assertGreater(timeouts[1], 0)
        self.assertLess(timeouts[1], 0.11)
        self.assertTrue(any(r['status'] == 'time_budget_exhausted' for r in result['records']))

    def test_elapsed_time_blocks_next_request(self):
        clock = Clock()
        paths = []

        def fake_fetch(origin, path, **kwargs):
            paths.append(path)
            clock.sleep(2)
            return Observation(200, [('Content-Type', 'text/html')], b'<a href="/next">Next</a>')

        result = run(ORIGIN, max_pages=3, max_depth=2, max_seconds=1, prefixes=['/'],
                     excluded=[], sitemaps=False, check=lambda: None, fetch=fake_fetch,
                     clock=clock.now, sleep=clock.sleep)
        self.assertEqual(paths, ['/'])
        self.assertTrue(result['timed_out'])
        self.assertEqual(result['paths'], [])
        self.assertEqual(result['requests_performed'], 1)

    def test_short_timeout_is_discovery_only(self):
        scope = {'origin': ORIGIN, 'paths': ['/docs'], 'method': 'GET',
                 'request_limit': 1, 'timeout_seconds': 0.125,
                 'type': 'explicit-path-response', 'purpose': 'link-discovery'}
        require_supported_scope(scope, ORIGIN, allow_auxiliary=True)
        with self.assertRaises(ValueError):
            require_supported_scope({k: v for k, v in scope.items() if k != 'purpose'}, ORIGIN)
        for value in (0, -1, 5.1, math.inf, math.nan, True, '2'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                require_supported_scope({**scope, 'timeout_seconds': value}, ORIGIN, allow_auxiliary=True)

    def test_pinned_discovery_transport_uses_remaining_timeout(self):
        class FakeSocket:
            def close(self):
                pass
            def shutdown(self, *_):
                pass
        class FakeResponse:
            status = 200
            def getheaders(self):
                return [('Content-Type', 'text/html')]
            def read(self, *_):
                return b''
        class FakeConnection:
            def __init__(self, *_, **kwargs):
                self.connection_timeout = kwargs['timeout']
            def request(self, *_args, **_kwargs):
                pass
            def getresponse(self):
                return FakeResponse()
            def close(self):
                pass
        class FakeTimer:
            def __init__(self, seconds, callback):
                self.seconds = seconds
            def start(self):
                pass
            def cancel(self):
                pass

        scope = {'origin': ORIGIN, 'paths': ['/'], 'method': 'GET',
                 'request_limit': 1, 'timeout_seconds': 0.3,
                 'type': 'explicit-path-response', 'purpose': 'link-discovery'}
        with patch('aegis.safety.resolve', return_value=('example.test', 80, '93.184.216.34', 'http')) as resolve, \
             patch('aegis.safety.socket.create_connection', return_value=FakeSocket()) as connect, \
             patch('aegis.safety.http.client.HTTPConnection', FakeConnection), \
             patch('aegis.safety.threading.Timer', FakeTimer):
            observation = fetch(ORIGIN, '/', discovery=True, assessment_scope=scope)
        self.assertEqual(observation.status, 200)
        self.assertEqual(connect.call_args.kwargs['timeout'], 0.3)
        resolve.assert_called_once_with(ORIGIN)


if __name__ == '__main__':
    unittest.main()
