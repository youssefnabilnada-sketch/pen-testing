"""Bounded, nonexecuting configuration adapters; publication remains separately approved."""
import tomllib

FILES = {'vercel': 'vercel.json', 'netlify': 'netlify.toml'}


def patch_file(patch):
    adapter = patch.test_evidence.get('adapter', 'vercel')
    if adapter not in FILES:
        raise ValueError('Unknown proposal adapter; manual review required.')
    return FILES[adapter]


def propose_netlify_nosniff(content):
    if not isinstance(content, str) or len(content.encode('utf-8')) > 65536:
        raise ValueError('Configuration too large.')
    before = tomllib.loads(content)
    headers = before.get('headers', [])
    if not isinstance(headers, list):
        raise ValueError('Invalid headers configuration.')
    for entry in headers:
        if not isinstance(entry, dict) or not isinstance(entry.get('for'), str) or not isinstance(entry.get('values'), dict):
            raise ValueError('Invalid header rule.')
        if any(k.lower() == 'x-content-type-options' for k in entry['values']):
            raise ValueError('Existing policy requires manual review; no overwrite proposed.')
    # Append without rewriting any original bytes, comments, build commands or precision.
    addition = '\n\n[[headers]]\nfor = "/*"\n[headers.values]\nX-Content-Type-Options = "nosniff"\n'
    result = content + addition
    if len(result.encode('utf-8')) > 65536:
        raise ValueError('Proposed configuration exceeds the safe size limit.')
    after = tomllib.loads(result)
    added = after['headers'].pop()
    if added != {'for': '/*', 'values': {'X-Content-Type-Options': 'nosniff'}}:
        raise ValueError('Unexpected generated header rule.')
    before.setdefault('headers', [])
    if after != before:
        raise ValueError('Configuration preservation test failed.')
    return result
