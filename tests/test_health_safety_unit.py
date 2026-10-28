"""Dependency-light checks for removal-safe monitor claim cleanup."""
import unittest
from types import SimpleNamespace as Row
from unittest.mock import Mock
from aegis.health_safety import mark_blocked_if_present, dispatch_due_monitors
from aegis.models import HealthMonitor


class HealthCleanupTests(unittest.TestCase):
    def test_withdrawn_grant_blocks_existing_monitor(self):
        row = Row(last_status='up')
        db = Mock()
        db.get.return_value = row
        mark_blocked_if_present(db, 'monitor-id')
        db.get.assert_called_once_with(HealthMonitor, 'monitor-id')
        db.commit.assert_called_once()
        self.assertEqual(row.last_status, 'blocked')

    def test_deleted_monitor_does_not_raise_or_recreate(self):
        db = Mock()
        db.get.return_value = None
        mark_blocked_if_present(db, 'deleted-id')
        db.commit.assert_called_once()
        db.add.assert_not_called()

    def test_broker_failure_does_not_block_other_due_monitors(self):
        sent = []
        def enqueue(mid):
            if mid == 'broken':
                raise ConnectionError('fixture broker unavailable')
            sent.append(mid)
        with self.assertLogs('aegis.health_safety', level='WARNING'):
            failures = dispatch_due_monitors(['a','broken','b'], enqueue)
        self.assertEqual(failures, 1)
        self.assertEqual(sent, ['a','b'])


if __name__ == '__main__':
    unittest.main()
