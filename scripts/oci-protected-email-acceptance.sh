#!/usr/bin/env bash
# ONE opt-in account + real Brevo inbox acceptance on the existing Oracle VM.
# Temporarily permits sign-up ONLY on local FastAPI loopback while BOTH public
# Vercel auth and Caddy no-key auth writes are verified closed.
# Immediately restores the protected production account-registration state.
# Operator must supply an owned Gmail plus-address and its emailed OTP.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" != 0 ]] || { echo "STOP: run as ubuntu." >&2; exit 1; }
[[ -t 0 ]] || { echo "STOP: interactive SSH required." >&2; exit 1; }
envfile=/etc/aegis/api.env
api=http://127.0.0.1:8000
web=https://aegis-pentest-eg.vercel.app
public=https://aegis-pentest-eg-api.duckdns.org
status() { curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 15 "$@"; }
deny() {
 [[ "$(status -X POST "$web/api/auth/register" -H 'Content-Type: application/json' --data-binary '{}')" == 503 ]] &&
 [[ "$(status -X POST "$web/api/auth/login" -H 'Content-Type: application/json' --data-binary '{}')" == 503 ]] &&
 [[ "$(status -X POST "$public/auth/register" -H 'Content-Type: application/json' --data-binary '{}')" == 503 ]] &&
 [[ "$(status -X POST "$public/auth/login" -H 'Content-Type: application/json' --data-binary '{}')" == 503 ]]
}
sudo systemctl is-active --quiet aegis@api || { echo "STOP: AEGIS API inactive." >&2; exit 1; }
[[ "$(sudo systemctl show aegis@api -p WorkingDirectory --value)" == /srv/aegis-release-v1 ]] ||
  { echo 'STOP: API is not running the protected v1 release.' >&2; exit 1; }
sudo test -f "$envfile" && sudo test ! -L "$envfile" ||
  { echo 'STOP: unexpected API EnvironmentFile.' >&2; exit 1; }
deny || { echo 'STOP: public login/registration is not closed at both layers.' >&2; exit 1; }
[[ "$(status "$api/ready")" == 200 ]] ||
  { echo 'STOP: private API is not ready.' >&2; exit 1; }
echo "AEGIS_LOCAL_ACCOUNT_LIVE_PREFLIGHT_PASS; only local registration will be temporarily enabled."
echo "This will send ONE email and create/deactivate ONE temporary account."
read -r -p 'Type AUTHORIZE ONE TEST ACCOUNT to proceed: ' confirm
[[ "$confirm" == 'AUTHORIZE ONE TEST ACCOUNT' ]] ||
  { echo 'STOP: no account operation authorized.' >&2; exit 1; }
unset confirm

backup="$(sudo mktemp /etc/aegis/.api-before-local-acceptance.XXXXXXXX)"
sudo chmod 0600 "$backup"
sudo cp -p "$envfile" "$backup"
modified=0
complete=0
restore() {
 rc="$?"
 trap - EXIT
 if [[ "$modified" == 1 ]]; then
   sudo cp -p "$backup" "$envfile" || rc=1
   sudo systemctl restart aegis@api || rc=1
 fi
 sudo rm -f "$backup" || rc=1
 if ! sudo sh -c '! grep -q "^AEGIS_PUBLIC_REGISTRATION_ENABLED=true$" "$1"' sh "$envfile"; then
   echo 'STOP: local registration opt-in not safely removed.' >&2
   rc=1
 fi
 if ! deny; then
   echo 'STOP: public auth changed unexpectedly; keep Vercel opt-in disabled.' >&2
   rc=1
 fi
 if [[ "$complete" == 1 && "$rc" == 0 ]]; then
   echo 'AEGIS_LOCAL_EMAIL_AND_SESSION_ACCEPTANCE_PASS'
   echo 'Public registration remains CLOSED. One verified temporary account deactivated.'
 fi
 exit "$rc"
}
trap restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
sudo python3 - "$envfile" <<'PY'
import os,stat,sys,tempfile
path=sys.argv[1]
info=os.stat(path)
if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode)!=0o640:
    raise SystemExit("STOP: unexpected API EnvironmentFile file type/mode")
data=open(path,'rb').read()
lines=data.splitlines()
values=[x for x in lines if x.startswith(b'AEGIS_PUBLIC_REGISTRATION_ENABLED=')]
if values not in ([],[b'AEGIS_PUBLIC_REGISTRATION_ENABLED=false']):
    raise SystemExit("STOP: unexpected registration setting; no file edit performed")
if not any(x==b'AEGIS_ENV=production' for x in lines):
    raise SystemExit("STOP: expected production service config missing")
new=b'\n'.join(x for x in lines if not x.startswith(b'AEGIS_PUBLIC_REGISTRATION_ENABLED='))+b'\nAEGIS_PUBLIC_REGISTRATION_ENABLED=true\n'
fd,tmp=tempfile.mkstemp(dir=os.path.dirname(path),prefix='.aegis-local-test-')
try:
    with os.fdopen(fd,'wb') as f:
        f.write(new);f.flush();os.fsync(f.fileno())
    os.chown(tmp,info.st_uid,info.st_gid)
    os.chmod(tmp,stat.S_IMODE(info.st_mode))
    os.replace(tmp,path)
finally:
    if os.path.exists(tmp):os.unlink(tmp)
PY
modified=1
sudo systemctl restart aegis@api
for attempt in $(seq 1 20); do
  [[ "$(status "$api/ready")" == 200 ]] && break
  sleep 1
done
[[ "$(status "$api/ready")" == 200 ]] || { echo 'STOP: local API not ready with temporary flag.' >&2; exit 1; }
deny || { echo 'STOP: public gateway changed while local flag on.' >&2; exit 1; }
python3 "$(dirname "$0")/oci-local-account-acceptance.py"
complete=1
