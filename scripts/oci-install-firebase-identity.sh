#!/usr/bin/env bash
# Install a Firebase Admin credential privately from an operator-staged file.
# No credential contents printed, no external network, no services started.
set -Eeuo pipefail
trap 'echo "Firebase credential setup failed; inspect errors without showing key contents." >&2' ERR
if [[ "$(id -u)" == 0 ]]; then echo "Run as the ubuntu SSH user, not root." >&2; exit 1; fi
staging="$HOME/aegis-firebase-admin.json"
target="/etc/aegis/firebase-identity.json"
if [[ ! -f "$staging" || -L "$staging" ]]; then
  echo "Upload the JSON credential first to ~/aegis-firebase-admin.json (regular file)." >&2
  exit 1
fi
if [[ "$(stat -c %u "$staging")" != "$(id -u)" ]]; then
  echo "Staged credential must be owned by the SSH user." >&2; exit 1
fi
if sudo test -e "$target"; then
  echo "A Firebase credential is already installed; refusing to overwrite or rotate it." >&2
  exit 1
fi
if ! getent group aegis-api >/dev/null; then
  echo "Missing AEGIS API service group; stage the runtime first." >&2; exit 1
fi
# Parse and validate only safe identity metadata; never output the private key.
python3 - "$staging" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
try:
    data=json.loads(p.read_text())
except (ValueError,UnicodeError):
    raise SystemExit("The supplied credential is not valid JSON.")
if (data.get("type")!="service_account" or
    data.get("project_id")!="aegis-d034c" or
    not str(data.get("client_email","")).endswith("@aegis-d034c.iam.gserviceaccount.com") or
    "BEGIN PRIVATE KEY" not in str(data.get("private_key",""))):
    raise SystemExit("Credential does not match the expected Firebase Admin service account and project.")
print("Firebase project and credential file structure validated (not a live Auth connectivity test).")
PY
chmod 0600 "$staging"
sudo install -d -m 0711 -o root -g root /etc/aegis
sudo install -o root -g aegis-api -m 0640 "$staging" "$target"
if ! sudo -u aegis-api test -r "$target"; then echo "API cannot read the credential." >&2; exit 1; fi
if sudo -u aegis-scanner test -r "$target"; then echo "Scanner can read private Firebase identity: stop and inspect." >&2; exit 1; fi
rm -f -- "$staging"
echo "AEGIS_FIREBASE_CREDENTIAL_INSTALLED"
echo "Key secured under /etc/aegis/firebase-identity.json, readable only by root and the API service group."
echo "NOT DONE: live Firebase Admin API probe, SMTP, migrations, API/workers or Vercel deployment."
