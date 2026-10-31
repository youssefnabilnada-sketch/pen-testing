#!/usr/bin/env bash
# Verify Firebase Admin API connectivity using only the restricted AEGIS API identity.
# Read-only/non-mutating against Firebase: lookup a random, nonexistent UID.
set -Eeuo pipefail
if [[ "$(id -u)" -eq 0 ]]; then
  echo 'Run as the ubuntu user, not root.' >&2
  exit 1
fi
if ! sudo -u aegis-api test -r /etc/aegis/firebase-identity.json; then
  echo 'FIREBASE_CHECK_FAILED: API service account cannot read the credential.' >&2
  exit 1
fi
sudo -u aegis-api /srv/aegis/.venv/bin/python - <<'PY'
import secrets
import sys
from pathlib import Path

path = Path('/etc/aegis/firebase-identity.json')
try:
    import firebase_admin
    from firebase_admin import auth, credentials
    cred = credentials.Certificate(str(path))
    if getattr(cred, 'project_id', None) != 'aegis-d034c':
        raise ValueError('mismatched_project')
    app = firebase_admin.initialize_app(cred, {'projectId': 'aegis-d034c', 'httpTimeout': 8}, name='aegis-oci-firebase-check')
    try:
        # No actual user is created, modified, or listed.
        auth.get_user('aegis-oci-connection-probe-' + secrets.token_hex(12), app=app)
    except auth.UserNotFoundError:
        print('AEGIS_FIREBASE_CONNECTED: verified real Firebase Auth API access; random user was correctly absent.')
        sys.exit(0)
    except Exception as exc:
        print('FIREBASE_CHECK_FAILED: Firebase Auth lookup was rejected (' + type(exc).__name__ + ').')
        sys.exit(1)
    print('FIREBASE_CHECK_UNEXPECTED: generated probe UID was found; check the test manually.')
    sys.exit(1)
except Exception as exc:
    print('FIREBASE_CHECK_FAILED: project, identity, or connectivity verification failed (' + type(exc).__name__ + ').')
    sys.exit(1)
PY
