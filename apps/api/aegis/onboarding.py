"""Ownership helpers. A GitHub URL is convenience, never proof of ownership."""
import re
from urllib.parse import urlencode, urlsplit
from fastapi import HTTPException

def instructions(origin, challenge):
    token = challenge.token
    path = f'.well-known/aegis-{token}.txt'
    return {'id': challenge.id, 'token': token, 'expires': challenge.expires,
            'wordpress': {'origin':origin,'token':token,'expires':challenge.expires} if challenge.method=='meta' else None,
            'method': challenge.method, 'filename': path, 'content': token,
            'instruction': {
                'dns': f'_aegis.{urlsplit(origin).hostname} TXT aegis={token}',
                'file': f'{origin}/{path} containing only: {token}',
                'meta': f'<meta name="aegis-verification" content="{token}">'
            }[challenge.method]}

def github_link(repository, branch, directory, challenge):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}', repository):
        raise HTTPException(422, 'Enter owner/repository, not a URL.')
    if not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]{0,99}', branch) or '..' in branch:
        raise HTTPException(422, 'Use a simple branch name such as main.')
    if directory not in ('', 'public'):
        raise HTTPException(422, 'Choose repository root or public.')
    filename = (directory+'/' if directory else '') + f'.well-known/aegis-{challenge.token}.txt'
    return 'https://github.com/'+repository+'/new/'+branch+'?'+urlencode({
        'filename': filename, 'value': challenge.token, 'message': 'Add AEGIS ownership verification'})
