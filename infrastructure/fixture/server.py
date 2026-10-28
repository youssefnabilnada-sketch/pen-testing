"""Intentionally configurable, isolated authorized test target. No public port."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        config=json.loads(Path('/fixture/config.json').read_text())
        token=config.get('verification_token','')
        if self.path.startswith('/.well-known/aegis-'):
            if token and self.path==f'/.well-known/aegis-{token}.txt':
                self.send_response(200);self.end_headers();self.wfile.write(token.encode())
            else:self.send_error(404)
            return
        if self.path!='/':self.send_error(404);return
        self.send_response(200)
        self.send_header('Content-Type','text/html')
        if config.get('hardened'):
            self.send_header('Content-Security-Policy',"default-src 'self'; frame-ancestors 'none'")
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Set-Cookie','fixture=sample; Secure; HttpOnly; SameSite=Strict')
        else:self.send_header('Set-Cookie','fixture=sample')
        self.end_headers()
        self.wfile.write(f'<html><head><meta name="aegis-verification" content="{token}"></head><body><h1>Authorized local fixture</h1></body></html>'.encode())
HTTPServer(('0.0.0.0',80),Handler).serve_forever()
