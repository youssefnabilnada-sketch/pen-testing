#!/usr/bin/env bash
# AEGIS v1 protected code-only backend rollout on the EXISTING Oracle VM.
# Prerequisite: a clean local checkout of the tested release/aegis-v1-final.
# No migrations, credentials, Caddy changes, customer writes, billing or scheduler.
# As ubuntu: bash scripts/oci-v1-backend-rollout.sh --check|--apply|--rollback
set -Eeuo pipefail
umask 077
mode="$1"
case "$mode" in --check|--apply|--rollback) ;; *) echo "Use --check, --apply or --rollback" >&2; exit 2;; esac
[[ "$(id -u)" != 0 ]] || { echo "Run as ubuntu, not root" >&2; exit 1; }

src="$(cd "$(dirname "$0")/.." && pwd)"
old_release=/srv/aegis-release-9e5f1e7
new_release=/srv/aegis-release-v1
runtime_python=/srv/aegis/.venv/bin/python
dropin=96-aegis-v1-final.conf
api=https://aegis-pentest-eg-api.duckdns.org
override_file() { echo "/etc/systemd/system/aegis@$1.service.d/$dropin"; }
override_content() {
  printf '[Service]\nWorkingDirectory=%s\nExecStart=\nExecStart=%s %s/scripts/server-process.py %s\n' "$new_release" "$runtime_python" "$new_release" "$1"
}
http_status() { curl -sS -o /dev/null -w '%{http_code}' --max-time 12 "$@"; }
services_ready() {
  for service in postgresql redis-server caddy aegis@api aegis@scanner aegis@intelligence aegis@notifier; do
    sudo systemctl is-active --quiet "$service" || { echo "STOP: $service inactive" >&2; return 1; }
  done
  ! sudo systemctl is-active --quiet aegis@scheduler ||
    { echo "STOP: scheduler unexpectedly active" >&2; return 1; }
  [[ "$(http_status "$api/health")" == 200 ]] ||
    { echo "STOP: public health failed" >&2; return 1; }
  [[ "$(http_status -X POST "$api/auth/login")" == 503 ]] ||
    { echo "STOP: public account POST not blocked" >&2; return 1; }
  [[ "$(http_status http://127.0.0.1:8000/ready)" == 200 ]] ||
    { echo "STOP: private API not ready" >&2; return 1; }
}
rollback_v1() {
  local count=0 role f failed=0
  for role in api scanner intelligence notifier; do
    f="$(override_file "$role")"
    if sudo test -e "$f"; then
      if ! diff -q <(override_content "$role") <(sudo cat "$f") >/dev/null; then
        echo "STOP: custom $role drop-in changed; manual review required" >&2
        return 1
      fi
      count=$((count+1))
    fi
  done
  if [[ "$count" == 0 ]]; then echo "AEGIS_V1_NO_NEW_ROLLOUT"; return 0; fi
  for role in api scanner intelligence notifier; do
    sudo rm -f "$(override_file "$role")" || failed=1
  done
  sudo systemctl daemon-reload || failed=1
  for role in api scanner intelligence notifier; do
    sudo systemctl restart "aegis@$role" || failed=1
  done
  services_ready || failed=1
  for role in api scanner intelligence notifier; do
    sudo systemctl show "aegis@$role" -p WorkingDirectory --value |
      grep -Fxq "$old_release" || failed=1
  done
  [[ "$failed" == 0 ]] || { echo "AEGIS_V1_ROLLBACK_NEEDS_OPERATOR_REVIEW" >&2; return 1; }
  echo "AEGIS_V1_BACKEND_ROLLBACK_PASS — original staged release restored"
}
if [[ "$mode" == --rollback ]]; then rollback_v1; exit; fi

command -v git >/dev/null
command -v tar >/dev/null
[[ -x "$runtime_python" ]] ||
  { echo "STOP: current Python runtime missing" >&2; exit 1; }
[[ -f "$old_release/scripts/server-process.py" ]] ||
  { echo "STOP: previous approved release missing" >&2; exit 1; }
[[ "$(git -C "$src" branch --show-current)" == release/aegis-v1-final ]] ||
  { echo "STOP: use the final release branch only" >&2; exit 1; }
[[ -z "$(git -C "$src" status --porcelain --untracked-files=no)" ]] ||
  { echo "STOP: tracked working tree has local modifications" >&2; exit 1; }
sha="$(git -C "$src" rev-parse HEAD)"
remote_sha="$(git -C "$src" rev-parse refs/remotes/origin/release/aegis-v1-final)"
[[ "$sha" == "$remote_sha" ]] ||
  { echo "STOP: local release SHA differs from the fetched GitHub release" >&2; exit 1; }
[[ ! -e "$new_release" ]] ||
  { echo "STOP: v1 release directory exists; never overwrite a staged release" >&2; exit 1; }
# Only code was changed. A schema or dependency change requires a separate approved migration plan.
sudo cmp -s "$old_release/apps/api/requirements-lock.txt" "$src/apps/api/requirements-lock.txt" ||
  { echo "STOP: dependency lock changed" >&2; exit 1; }
sudo diff -qr "$old_release/apps/api/migrations/versions" "$src/apps/api/migrations/versions" >/dev/null ||
  { echo "STOP: migration history changed" >&2; exit 1; }
for role in api scanner intelligence notifier; do
  [[ ! -e "$(override_file "$role")" ]] ||
    { echo "STOP: v1 $role drop-in already exists" >&2; exit 1; }
  sudo systemctl show "aegis@$role" -p WorkingDirectory --value |
    grep -Fxq "$old_release" ||
    { echo "STOP: $role does not run the previous staged release" >&2; exit 1; }
done
services_ready
printf 'AEGIS_V1_PRECHECK_PASS: source %s; old release intact; no migrations needed.\n' "$sha"
if [[ "$mode" == --check ]]; then exit 0; fi

# Stage only tracked Git data into a never-before-used, root-owned immutable directory.
sudo install -d -o root -g root -m 0755 "$new_release"
git -C "$src" archive "$sha" | sudo tar -x -C "$new_release"
sudo cmp -s "$new_release/apps/api/requirements-lock.txt" "$old_release/apps/api/requirements-lock.txt" ||
  { echo "STOP: staged lock mismatch" >&2; exit 1; }
sudo diff -qr "$new_release/apps/api/migrations/versions" "$old_release/apps/api/migrations/versions" >/dev/null ||
  { echo "STOP: staged migrations mismatch" >&2; exit 1; }

# Smoke imports without production secrets, database writes or external scans.
env -i PATH=/usr/bin:/bin HOME=/tmp PYTHONPATH="$new_release/apps/api" AEGIS_ENV=staging DATABASE_URL=sqlite:///:memory: \
  "$runtime_python" -B - <<'PY'
from fastapi.testclient import TestClient
from aegis.main import app
with TestClient(app) as client:
    assert client.get("/auth/firebase/config").status_code == 200
print("AEGIS_V1_ISOLATED_API_IMPORT_PASS")
PY

complete=0
rollback_on_failure() {
  local rc="$?"
  trap - EXIT
  if [[ "$complete" != 1 ]]; then rollback_v1 || true; fi
  exit "$rc"
}
trap rollback_on_failure EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
for role in api scanner intelligence notifier; do
  directory="/etc/systemd/system/aegis@$role.service.d"
  sudo install -d -m 0755 "$directory"
  override_content "$role" | sudo tee "$(override_file "$role")" >/dev/null
  sudo chown root:root "$(override_file "$role")"
  sudo chmod 0644 "$(override_file "$role")"
done
sudo systemctl daemon-reload
for role in api scanner intelligence notifier; do sudo systemctl restart "aegis@$role"; done
services_ready
for role in api scanner intelligence notifier; do
  sudo systemctl show "aegis@$role" -p WorkingDirectory --value |
    grep -Fxq "$new_release" ||
    { echo "STOP: $role is not running the approved v1 code" >&2; exit 1; }
done
complete=1
echo "AEGIS_V1_BACKEND_PROTECTED_ROLLOUT_PASS"
echo "Caddy public writes remain blocked, scheduler off, no migration, billing or secret change."
echo "Rollback: bash scripts/oci-v1-backend-rollout.sh --rollback"
