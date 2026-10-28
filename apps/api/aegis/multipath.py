"""Exact-path response assessment; no crawling or redirect traversal."""
import hashlib
from .crawler import MAX_PAGES, safe_path

def validate_paths(paths):
    if not isinstance(paths,list) or not 1<=len(paths)<=MAX_PAGES or any(not isinstance(p,str) for p in paths) or len(set(paths))!=len(paths):raise ValueError(f'Choose one to {MAX_PAGES} distinct paths.')
    for path in paths:safe_path(path)
    return paths

def qualify(rule,path):
    return rule if path=='/' else rule+'@'+hashlib.sha256(path.encode()).hexdigest()[:16]

def combine(results):
    observations=[];executed=[];missing={};versions={}
    for path,found,manifest in results:
        for finding in found:observations.append({**finding,'rule':qualify(finding['rule'],path),'evidence':'Authorized path '+path+': '+finding['evidence']})
        executed.extend(qualify(rule,path) for rule in manifest['executed'])
        missing.update({qualify(rule,path):reason for rule,reason in manifest['not_performed'].items()})
        versions.update({qualify(rule,path):version for rule,version in manifest['rule_versions'].items()})
    return observations,{'version':'explicit-path-response-v1','paths':[r[0] for r in results],'executed':executed,'not_performed':missing,'rule_versions':versions}
