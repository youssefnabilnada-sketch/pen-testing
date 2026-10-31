#!/usr/bin/env bash
# OCI Ubuntu 24.04 ARM64 preparation. NO public deployment or database migration.
set -Eeuo pipefail
trap 'echo "AEGIS host preparation stopped at line ${LINENO}; inspect the error before retrying." >&2' ERR

if [[ "$(id -u)" -eq 0 ]]; then echo "Run as the ubuntu login user, not root." >&2; exit 1; fi
if [[ "$(uname -m)" != "aarch64" ]]; then echo "Expected Oracle Ampere A1 ARM64." >&2; exit 1; fi
. /etc/os-release
if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then echo "Expected Ubuntu 24.04." >&2; exit 1; fi
cd "$(dirname "$0")/.."
test -f apps/api/requirements.txt
test -f infrastructure/deployment/production.env.example
echo "1/3: Installing trusted packages (no public listeners configured)..."
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y git python3.12 python3.12-venv python3-pip postgresql redis-server
sudo systemctl enable --now postgresql redis-server
echo "2/3: Building Python backend as non-root (no migrations or service startup)..."
bash scripts/build-oci-backend.sh
echo "3/3: Verifying PostgreSQL/Redis listeners..."
for port in 5432 6379; do
  count=0
  while read -r proto recvq sendq address peer rest; do
    case "$address" in
      *:"$port") ;;
      *) continue ;;
    esac
    count=$((count+1))
    if [[ "$address" != "127.0.0.1:$port" && "$address" != "[::1]:$port" && "$address" != "::1:$port" ]]; then
      echo "STOP: port $port is exposed on $address; configure loopback only." >&2
      exit 1
    fi
  done < <(sudo ss -lntH)
  if ((count==0)); then echo "WARNING: no TCP listener found on port $port" >&2; fi
done
echo "OCI_PREPARED: Python API environment, PostgreSQL and Redis packages are installed."
echo "NO secret, database schema, background service, internet API port, Caddy TLS or Vercel configuration has been changed."
