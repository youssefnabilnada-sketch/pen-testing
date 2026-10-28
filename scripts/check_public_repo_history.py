"""Offline, conservative public-release history guard. NOT a complete secret audit."""
import argparse
import re
import subprocess
import sys
from pathlib import PurePosixPath

MAX_BLOB_BYTES=2*1024*1024
PATTERNS={
    'private-key':re.compile(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    'github-token':re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    'aws-access-key':re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    'openai-key':re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    'slack-token':re.compile(rb"xox[baprs]-[A-Za-z0-9-]{25,}"),
    'service-account-private-key':re.compile(rb'"type"\s*:\s*"service_account"[\s\S]{0,12000}"private_key"\s*:'),
}

def is_sensitive_path(path):
    name=PurePosixPath(path.replace('\\','/').lower()).name
    if name.endswith(('.example','.sample')):return False
    return (
        name=='.env' or name.startswith('.env.')
        or name in {'id_rsa','id_ed25519','.npmrc','credentials.json','firebase-identity.json'}
        or name.endswith(('.p12','.pfx','-firebase-adminsdk.json'))
        or ('service-account' in name and name.endswith('.json'))
    )

def analyze_blob(path,data):
    problems=['sensitive-filename'] if is_sensitive_path(path) else []
    if len(data)>MAX_BLOB_BYTES:return problems+['oversized-object-requires-manual-review']
    return problems+[name for name,pattern in PATTERNS.items() if pattern.search(data)]

def git(*args,cwd='.'):
    return subprocess.run(['git',*args],cwd=cwd,check=True,capture_output=True).stdout

def audit_history(cwd='.'):
    records=git('rev-list','--objects','--all',cwd=cwd).splitlines()
    seen=set()
    findings=[]
    # Include historical filenames even when the same blob had multiple names.
    names=git('log','--all','--format=','--name-only','-z',cwd=cwd)
    for raw in set(names.split(b'\x00')):
        name=raw.decode('utf-8',errors='replace').strip('\n')
        if name and is_sensitive_path(name):
            findings.append(('history',name,'historical-sensitive-filename'))
    examined=0
    for record in records:
        sha_raw,_,path_raw=record.partition(b' ')
        sha=sha_raw.decode('ascii')
        if sha in seen:continue
        seen.add(sha)
        if git('cat-file','-t',sha,cwd=cwd).strip()!=b'blob':continue
        size=int(git('cat-file','-s',sha,cwd=cwd).strip())
        path=path_raw.decode('utf-8',errors='replace')
        data=b'' if size>MAX_BLOB_BYTES else git('cat-file','blob',sha,cwd=cwd)
        issues=(['oversized-object-requires-manual-review'] if size>MAX_BLOB_BYTES
                else [issue for issue in analyze_blob(path,data) if issue!='sensitive-filename'])
        examined+=1
        for issue in issues:findings.append((sha[:12],path,issue))
    return len(records),examined,findings

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',default='.')
    args=parser.parse_args(argv)
    try:records,checked,findings=audit_history(args.repo)
    except (OSError,ValueError,subprocess.CalledProcessError) as e:
        print('NO-GO: full history inaccessible ('+type(e).__name__+').')
        return 2
    print('Checked '+str(checked)+' Git history blobs across '+str(records)+' reachable objects.')
    for sha,path,issue in findings:
        # Never print matched secret values or file contents.
        print('BLOCKER: object='+sha+' file='+path+' category='+issue)
    if findings:
        print('NO-GO: '+str(len(findings))+' history indicators require manual review and remediation.')
        return 1
    print('Narrow signature check passed; full history/privacy/security review is still required.')
    return 0

if __name__=='__main__':sys.exit(main())
