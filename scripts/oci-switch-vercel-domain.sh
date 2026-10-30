#!/usr/bin/env bash
# Safely switch AEGIS Oracle WEB_ORIGIN to the new Vercel domain.
# No deployment, service start, secret disclosure, network changes, or database migration.
set -Eeuo pipefail
trap 'echo "AEGIS origin change stopped. Review the configuration before retrying." >&2' ERR

if [[ "$(id -u)" == 0 ]]; then
  echo 'Run as the ubuntu user, not root.' >&2
  exit 1
fi
sudo python3 - <<'PY'
from pathlib import Path
import os
import stat
import tempfile
old = b"WEB_ORIGIN=https://pen-testing-iota.vercel.app"
new = b"WEB_ORIGIN=https://aegis-pentest-eg.vercel.app"
directory = Path("/etc/aegis")
roles = ("api", "scanner", "intelligence", "notifier", "scheduler")
updates = []
for role in roles:
    file = directory / f"{role}.env"
    info = file.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o640:
        raise SystemExit(f"Unexpected service env permissions for {role}; no changes applied.")
    data = file.read_bytes()
    values = [x for x in data.splitlines() if x.startswith(b"WEB_ORIGIN=")]
    if values == [new]:
        continue
    if values != [old]:
        raise SystemExit(f"Unexpected WEB_ORIGIN in {role}; no changes applied.")
    updates.append((file, data, info))
for file, data, info in updates:
    fd, temporary = tempfile.mkstemp(prefix=".aegis-origin-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data.replace(old, new, 1))
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(temporary, info.st_uid, info.st_gid)
        os.chmod(temporary, stat.S_IMODE(info.st_mode))
        os.replace(temporary, file)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
if any(new not in (directory / f"{role}.env").read_bytes().splitlines() for role in roles):
    raise SystemExit("AEGIS origin verification failed.")
print("AEGIS_VERCEL_DOMAIN_UPDATED")
print("All service WEB_ORIGIN values now use https://aegis-pentest-eg.vercel.app")
print("Existing secrets preserved. No API, workers, Firebase, Vercel or Caddy deployment was started.")
PY
