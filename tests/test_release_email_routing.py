"""Celery alert tasks must never land on the scanner queue."""
from aegis.worker import celery

def test_notifications_are_isolated_from_scanner_queue():
    routes=celery.conf.task_routes
    assert routes['aegis.send_alert']['queue']=='notifications'
    assert routes['aegis.email_tick']['queue']=='notifications'
    assert 'aegis.assess' not in routes
