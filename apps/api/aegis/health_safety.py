"""Idempotent worker cleanup when an owned health monitor is withdrawn/deleted."""
import logging
from .models import HealthMonitor


def mark_blocked_if_present(db, monitor_id):
    """Do not re-create a monitor after customer removal; never persist a sample."""
    monitor = db.get(HealthMonitor, monitor_id)
    if monitor is not None:
        monitor.last_status = 'blocked'
    db.commit()


def dispatch_due_monitors(ids, enqueue):
    """Keep other due monitors eligible if one broker dispatch fails.

    The worker alone claims and advances next_due, so failed dispatches stay
    eligible for a future scheduler tick. No false delivery acknowledgement.
    """
    failed = 0
    for mid in ids:
        try:
            enqueue(mid)
        except Exception as exc:
            failed += 1
            logging.getLogger(__name__).warning(
                'Health dispatch deferred for %s (%s)', mid, type(exc).__name__
            )
    return failed
