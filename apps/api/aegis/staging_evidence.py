"""Conservative evaluation of bounded, historical staging assessment evidence.

This does not prove a repository commit was deployed to staging, application
behavior is correct, or a remote rollback works. It only evaluates recorded
supported safe checks for the explicitly linked staging report.
"""


def evaluate_staging(snapshot, expected_paths, required_rules):
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get('profile'), dict):
        raise ValueError('Staging report is incomplete.')
    profile = snapshot['profile']
    executed = profile.get('executed')
    observed_paths = profile.get('paths')
    not_performed = profile.get('not_performed')
    findings = snapshot.get('findings')
    if (not isinstance(expected_paths, list) or not expected_paths
        or len(expected_paths) > 20 or any(not isinstance(p, str) or not p.startswith('/') for p in expected_paths)
        or len(set(expected_paths)) != len(expected_paths)
        or not isinstance(observed_paths, list) or observed_paths != expected_paths
        or not isinstance(executed, list) or len(executed) > 300
        or any(not isinstance(rule, str) or not rule for rule in executed)
        or not isinstance(not_performed, dict) or len(not_performed) > 300
        or any(not isinstance(rule, str) or not isinstance(reason, str)
                   for rule, reason in not_performed.items())
        or not isinstance(findings, list) or len(findings) > 1000
        or any(not isinstance(f, dict) or not isinstance(f.get('rule'), str) for f in findings)):
        raise ValueError('Staging report contains missing, mismatched or malformed observations.')
    required = set(required_rules)
    if not required or any(not isinstance(rule, str) or not rule for rule in required):
        raise ValueError('Staging must have supported checks to compare.')
    done = set(executed)
    present = {f['rule'] for f in findings}
    if done.intersection(not_performed):
        raise ValueError('Staging evidence contradicts itself about executed checks.')
    # A rule cannot be treated as passed when a finding is reported, or when
    # that detector was never executed for an expected path.
    return required.issubset(done) and not required.intersection(present)
