#!/usr/bin/env bash
# AEGIS Oracle PostgreSQL: encrypted, atomic, manual backup.
# Does not change the database, install software, modify systemd or enable the public site.
# Run as root only after configuring an OFF-SERVER OpenPGP recovery key.
set -Eeuo pipefail
umask 077

stop() { printf 'AEGIS_BACKUP_STOP: %s\n' "$1" >&2; exit 1; }
[ "$#" -eq 1 ] || stop 'Use --check or --create.'
mode="$1"
case "$mode" in --check|--create) ;; *) stop 'Use --check or --create.';; esac
[ "$(id -u)" -eq 0 ] || stop 'Run with sudo on the owned Oracle VM.'
for tool in psql pg_dump gpg sha256sum stat df awk mktemp sudo; do
  command -v "$tool" >/dev/null || stop "Missing required command: $tool"
done

base='/var/backups/aegis'
destination_dir="$base/postgresql"
recipient_file='/etc/aegis/backup-recipient'
[ -d "$base" ] && [ ! -L "$base" ] || stop 'Private /var/backups/aegis directory is missing or unsafe.'
[ "$(stat -c '%u:%a' "$base")" = '0:700' ] || stop 'Backup root must be owned by root, mode 0700.'
[ -f "$recipient_file" ] && [ ! -L "$recipient_file" ] || stop 'Install a root-owned /etc/aegis/backup-recipient file containing a complete offline public-key fingerprint.'
[ "$(stat -c '%u:%a' "$recipient_file")" = '0:600' ] || stop 'Backup recipient file must be root-owned, mode 0600.'
recipient="$(tr -d '[:space:]' < "$recipient_file" | tr 'abcdef' 'ABCDEF')"
[[ "$recipient" =~ ^[A-F0-9]{40}$ ]] || stop 'Backup recipient must be a full 40-character OpenPGP fingerprint.'
gpg --batch --list-keys "$recipient" >/dev/null 2>&1 || stop 'Recipient public key is not imported in the root GnuPG keyring.'
db_bytes="$(sudo -n -u postgres psql -X -Atq -d aegis -c 'SELECT pg_database_size(current_database());')" || stop 'Cannot read AEGIS PostgreSQL size.'
[[ "$db_bytes" =~ ^[0-9]+$ ]] || stop 'Database size check returned an unexpected value.'
free_kb="$(df -Pk "$base" | awk 'NR==2 {print $4}')"
[[ "$free_kb" =~ ^[0-9]+$ ]] || stop 'Cannot check backup disk space.'
[ "$(( free_kb * 1024 ))" -gt "$(( db_bytes + 1073741824 ))" ] || stop 'Insufficient estimated disk space for a safe encrypted dump.'
if [ -e "$destination_dir" ]; then
  [ -d "$destination_dir" ] && [ ! -L "$destination_dir" ] || stop 'Unexpected backup destination type.'
  [ "$(stat -c '%u:%a' "$destination_dir")" = '0:700' ] || stop 'Destination must be root-owned, mode 0700.'
fi
if [ "$mode" = '--check' ]; then
  echo 'AEGIS_ENCRYPTED_BACKUP_PREFLIGHT_PASS'
  echo 'No database writes, backup files, key changes, or production configuration changes were made.'
  echo 'A backup is NOT created. Use --create after confirming separate recovery-key custody.'
  exit 0
fi

install -d -o root -g root -m 0700 "$destination_dir"
temporary="$(mktemp "$destination_dir/.incomplete-XXXXXXXX")"
finished=0
cleanup() {
  if [ "$finished" != 1 ] && [ -n "$temporary" ]; then rm -f -- "$temporary"; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Pipeline propagates pg_dump failure. Unencrypted customer data is never written
# to a regular file: it is streamed directly to OpenPGP encryption.
sudo -n -u postgres pg_dump --format=custom --no-owner --no-acl --dbname=aegis |
  gpg --batch --no-tty --yes --trust-model always --recipient "$recipient" --encrypt --output "$temporary"
[ "$(stat -c '%s' "$temporary")" -gt 1024 ] || stop 'Encrypted dump is unexpectedly small.'
name="aegis-postgres-$(date -u +%Y%m%dT%H%M%SZ)-$RANDOM.dump.gpg"
target="$destination_dir/$name"
# Hard link is an atomic no-overwrite publish within the backup filesystem.
ln -- "$temporary" "$target" || stop 'Cannot publish backup without overwrite.'
rm -f -- "$temporary"
temporary=''
chmod 0600 "$target"
digest="$(sha256sum -- "$target" | awk '{print $1}')"
printf '%s  %s\n' "$digest" "$name" > "$target.sha256"
chmod 0600 "$target.sha256"
(cd "$destination_dir" && sha256sum -c -- "$name.sha256" >/dev/null) || stop 'Encrypted backup checksum verification failed.'
sync -f "$target"
sync -f "$target.sha256"
finished=1
echo "AEGIS_ENCRYPTED_BACKUP_CREATED: $name"
echo 'Checksum verified on Oracle. No plaintext dump was retained.'
echo 'RELEASE GATE STILL OPEN: transfer ciphertext and checksum OFF this server, preserve the private key separately, and decrypt/restore on an isolated host to prove recovery.'
