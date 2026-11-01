#!/usr/bin/env bash
# Safely set the verified public Vercel origin in staged Oracle service environments.
# Never prints or copies secrets outside /etc/aegis; does not start/reload services.
set -Eeuo pipefail
trap 'echo "AEGIS Vercel origin update stopped. No services or Vercel deployments were started." >&2' ERR
[[ "$(id -u)" != "0" ]] || { echo 'Run as ubuntu, not root.' >&2; exit 1; }
sudo python3 - <<'PY'
from pathlib import Path
import os
import stat
import tempfile

folder = Path("/etc/aegis")
roles = ("api", "scanner", "intelligence", "notifier", "scheduler")
old = b"WEB_ORIGIN=https://REPLACE-WITH-YOUR-VERCEL-ORIGIN.invalid"
new = b"WEB_ORIGIN=https://pen-testing-iota.vercel.app"
changes = []
for role in roles:
    path = folder / f"{role}.env"
    data = path.read_bytes()
    st = path.stat()
    if not stat.S_ISREG(st.st_mode):
        raise SystemExit(f"Unsafe or missing environment file for {role}; no changes made.")
    lines = data.splitlines()
    origin_lines = [line for line in lines if line.startswith(b"WEB_ORIGIN=")]
    if origin_lines == [new]:
        continue
    if origin_lines != [old]:
        raise SystemExit(f"Unexpected WEB_ORIGIN for {role}; refusing to overwrite any existing setting.")
    changes.append((path, data, st))

updated = []
for path, data, st in changes:
    fd, tempname = tempfile.mkstemp(dir=folder, prefix=".aegis-origin-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data.replace(old, new, 1))
            f.flush()
            os.fsync(f.fileno())
        os.chown(tempname, st.st_uid, st.st_gid)
        os.chmod(tempname, stat.S_IMODE(st.st_mode))
        os.replace(tempname, path)
        updated.append(path)
    finally:
        if os.path.exists(tempname):
            os.unlink(tempname)
for role in roles:
    path = folder / f"{role}.env"
    if new not in path.read_bytes().splitlines():
        raise SystemExit(f"Origin verification failed for {role}.")
print("AEGIS_VERCEL_ORIGIN_CONFIGURED")
print("All five service environments now point at the verified Vercel project hostname.")
print("This does NOT mean Vercel production is deployed or Firebase/SMTP are configured.")
print("No secrets were printed; no services, migrations or Vercel deployments were started.")
PY
