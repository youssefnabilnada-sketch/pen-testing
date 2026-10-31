# AEGIS Oracle encrypted backup / recovery acceptance (NOT YET EXECUTED)

This is a production-operator runbook, **not evidence of a completed backup or final launch authorization**. The script creates an encrypted logical PostgreSQL dump of the live AEGIS database without modifying live rows. It is manually invoked; it does not alter Caddy, Vercel, Firebase, workers, the scheduler or billing.

## Prerequisites and custody (separate trusted device)
1. Generate or designate a strong OpenPGP encryption/recovery key on an independent trusted device. **Keep the private key and recovery passphrase OFF Oracle, OFF GitHub, and outside chat.** Retain separate protected recovery copies. Verify the key is usable.
2. Export only its public key and import it into the Oracle VM's **root** GnuPG keyring using secure operator access. Store the public-key full 40-character fingerprint in /etc/aegis/backup-recipient (root:root, 0600).
3. Ensure /var/backups/aegis is root:root, mode 0700. Ensure backup disk has adequate free space.
4. Run from the checked-out reviewed release as the Oracle operator:

    sudo bash scripts/oci-encrypted-postgres-backup.sh --check

   This does not write to the database or create a backup. Correct any reported prerequisites before proceeding.

## Create first encrypted backup (operator action)

    sudo bash scripts/oci-encrypted-postgres-backup.sh --create

The script streams pg_dump through OpenPGP encryption (no unencrypted regular dump file), uses no-overwrite publication, checks the encrypted file SHA-256, and leaves files restricted to root. It reports only the ciphertext filename. It **cannot prove decryption or restoration without the OFF-SERVER private key**.

## Required recovery acceptance before public registration
- Securely copy the .dump.gpg and matching .sha256 from Oracle to an independent backup host/store. Confirm a copied checksum and a documented retention/rotation policy. Protect offsite access, configure a recurring backup and failure alert, and test that it can be restored after the original VM is unavailable.
- On an ISOLATED replacement PostgreSQL environment, decrypt with the separately held private key into a restricted pipe/file and restore into a brand-new disposable database; check pg_restore exit status, Alembic revision, tables, synthetic and actual tenant counts, and read access. Never restore into the production database. Avoid printing customer data.
- Independently exercise the existing Oracle restore drill before release:

    bash scripts/oci-disposable-restore-drill.sh

    bash scripts/oci-disposable-restore-drill.sh --apply

  This drill uses a temporary local dump and separate test database and deletes both afterwards; it is **not** an offsite backup and is **not** a test of decryption of the encrypted archive.
- Keep secret/configuration recovery material (Firebase identity, MFA/GitHub encryption keys, SMTP configuration, systemd/Caddy settings) under separate protected backup and recovery procedures. A database dump alone cannot restore those credentials and service policies.

## Status and abort conditions
As of this runbook addition: **no live encrypted backup, offsite replication, restore drill, deployment change or public registration enablement has been executed by this workstream**. If --check or the drill fails, treat launch as NO-GO. Do not print credential values, backup plaintext, or private keys in logs or issue comments. Never use docker compose down -v, dropdb on aegis, or overwrite existing backup files as part of this procedure.
