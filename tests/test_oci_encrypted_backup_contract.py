"""Static safety checks for the opt-in Oracle backup procedure.

No production database or GPG key is needed by CI; live execution is a separate release gate.
"""
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "oci-encrypted-postgres-backup.sh"

def test_backup_script_valid_bash():
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

def test_backup_script_requires_opt_in_encryption_and_never_restores_live_db():
    text = SCRIPT.read_text()
    assert "--check|--create" in text
    assert "gpg --batch" in text
    assert "pg_dump --format=custom" in text
    assert "set -Eeuo pipefail" in text
    assert "pg_restore " not in text
    assert "dropdb " not in text
    assert "systemctl " not in text
    assert "AEGIS_ENCRYPTED_BACKUP_CREATED" in text
