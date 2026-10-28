"""Export committed source plus self-contained Git history; verifies clone and bytes.
Usage: python scripts/export-recovery.py /absolute/output/directory
Never exports ignored runtime credentials, databases or dependencies.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

root = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)

def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])

if git('status', '--porcelain').strip():
    raise SystemExit('Commit or explicitly resolve outstanding changes before export.')
commit = git('rev-parse', 'HEAD').decode().strip()
names = git('ls-files', '-z').decode().strip('\0').split('\0')
blocked = {'.env', 'api.env', 'scanner.env', 'firebase-identity.json', 'firebase-debug.log'}
if any(Path(n).name in blocked or Path(n).name.startswith('service-account') for n in names):
    raise SystemExit('Sensitive filename in tracked source; review before export.')
bundle = out / 'AEGIS_SECURITY_CLOUD_TRANSFER_HISTORY.bundle'
subprocess.run(['git', '-C', str(root), 'bundle', 'create', str(bundle), '--all'], check=True)
subprocess.run(['git', '-C', str(root), 'bundle', 'verify', str(bundle)], check=True, capture_output=True)
with tempfile.TemporaryDirectory(prefix='aegis-restore-') as work:
    restored = Path(work) / 'repo'
    subprocess.run(['git', 'clone', '-q', str(bundle), str(restored)], check=True)
    assert subprocess.check_output(['git', '-C', str(restored), 'rev-parse', 'HEAD']).decode().strip() == commit
    hashes = {}
    for name in names:
        data = (root / name).read_bytes()
        assert (restored / name).read_bytes() == data, name
        hashes[name] = hashlib.sha256(data).hexdigest()
    archive = out / 'AEGIS_SECURITY_CLOUD_LATEST_TRANSFER.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.write(root / name, 'AEGIS-Security-Cloud/' + name)
        z.write(bundle, bundle.name)
        z.writestr('RECOVERY_VERIFICATION.json', json.dumps({
            'commit': commit, 'state': 'development_not_final',
            'bundle_clone_and_source_bytes': 'PASS', 'files': hashes,
            'note': 'Original HANDOFF_METADATA/SOURCE-MANIFEST describe the incoming transfer only.'
        }, indent=2))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        destination = Path(work) / 'extracted'
        z.extractall(destination)
        for name, digest in hashes.items():
            assert hashlib.sha256((destination / 'AEGIS-Security-Cloud' / name).read_bytes()).hexdigest() == digest
checksums = out / 'RECOVERY_SHA256SUMS.txt'
checksums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in (archive, bundle)))
print(json.dumps({'archive': str(archive), 'commit': commit, 'source_files': len(names), 'restore': 'PASS'}))
