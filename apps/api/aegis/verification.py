import secrets
from html.parser import HTMLParser
from urllib.parse import urlsplit
import dns.resolver
from .safety import fetch, resolve

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tokens = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == 'meta' and attrs.get('name') == 'aegis-verification':
            self.tokens.append(attrs.get('content', ''))

def verify(origin, challenge):
    resolve(origin)  # DNS TXT ownership never authorizes a blocked network target.
    if challenge.method == 'dns':
        records = dns.resolver.resolve('_aegis.'+urlsplit(origin).hostname, 'TXT', lifetime=5)
        return any(secrets.compare_digest(b''.join(r.strings).decode(), 'aegis='+challenge.token) for r in records)
    path = f'/.well-known/aegis-{challenge.token}.txt' if challenge.method == 'file' else '/'
    response = fetch(origin, path, verification=True)
    if response.status != 200:
        return False
    body = response.body.decode('utf-8', errors='replace')
    if challenge.method == 'file':
        return secrets.compare_digest(body.strip(), challenge.token)
    parser = Meta()
    parser.feed(body)
    return any(secrets.compare_digest(x, challenge.token) for x in parser.tokens)
