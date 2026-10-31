"""Fail-closed pre-deployment CI status aggregator.

GitHub Actions `needs` evidence is provided by the workflow runner, not by
user-supplied HTTP input. Passing CI is necessary but not sufficient for live
production approval; DNS, identity, SMTP, backups, security and cloud smoke
checks require independent evidence after deployment.
"""
import json
import os
import sys

REQUIRED = frozenset({
    'backend', 'web', 'postgres-migrations',
    'integrated-postgres-redis', 'browser-health', 'browser-smoke', 'native-runtime', 'wordpress-runtime', 'public-repository-history',
})


def evaluate(results):
    if not isinstance(results, dict):
        return False, ['CI dependency results must be an object.']
    issues = []
    for name in sorted(REQUIRED):
        entry = results.get(name)
        result = entry.get('result') if isinstance(entry, dict) else None
        if result != 'success':
            issues.append(f'{name}: {result if result is not None else "missing"}')
    return not issues, issues


def main():
    try:
        contents = os.environ['AEGIS_CI_NEEDS_JSON']
        data = json.loads(contents)
        approved, issues = evaluate(data)
    except (KeyError, json.JSONDecodeError) as exc:
        print(f'CI evidence missing or invalid: {type(exc).__name__}', file=sys.stderr)
        return 1
    if not approved:
        print('PRE-DEPLOYMENT CI GATE FAILED: ' + '; '.join(issues), file=sys.stderr)
        return 1
    print('Pre-deployment CI evidence: nine required jobs succeeded.')
    print('This is NOT production certification. Live cloud, identity, mail,')
    print('backups, privacy/security and recovery acceptance remain separate.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
