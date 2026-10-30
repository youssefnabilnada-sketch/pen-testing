import type {NextRequest} from 'next/server';
import {apiOrigin} from '../../../../lib/deployment';
import {authPath, previewProxyGate, aegisSessionCookie} from '../../../../lib/auth-proxy-policy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
type Context = {params: Promise<{path: string[]}>};

async function proxyAuth(request: NextRequest, context: Context): Promise<Response> {
  const segments = (await context.params).path;
  const path = authPath(segments);
  if (!path) return new Response('Not found.', {status:404});

  const gate = previewProxyGate(
    process.env,
    request.headers.get('origin'),
    request.nextUrl.origin,
    request.method,
  );
  if (!gate.allowed) return new Response('Protected acceptance mode.', {status: gate.status});

  const backend = apiOrigin(process.env);
  const target = backend + path + request.nextUrl.search;
  // Never pass X-Forwarded-For or arbitrary browser-supplied headers to an API
  // privileged by a server-side preview secret.
  const headers = new Headers({Accept:'application/json'});
  for (const key of ['content-type','origin','x-csrf-token']) {
    const val = request.headers.get(key);
    if (val) headers.set(key,val);
  }
  const session = aegisSessionCookie(request.headers.get('cookie'));
  if (session) headers.set('Cookie',session);
  if (gate.secret) headers.set('X-AEGIS-Preview-Gateway',gate.secret);

  let body: Uint8Array | undefined;
  if (!['GET','HEAD'].includes(request.method)) {
    if (request.headers.get('content-type')?.split(';')[0]?.toLowerCase() !== 'application/json')
      return new Response('JSON content required.', {status:415});
    const length = Number(request.headers.get('content-length') || 0);
    if (!Number.isSafeInteger(length) || length > 65536 || length < 0)
      return new Response('Request too large.', {status:413});
    const data = await request.arrayBuffer();
    if (data.byteLength > 65536)
      return new Response('Request too large.', {status:413});
    body = new Uint8Array(data);
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method:request.method,
      headers,
      body,
      redirect:'manual',
      cache:'no-store',
      signal:AbortSignal.timeout(15000),
    });
  } catch {
    return new Response('Account service temporarily unavailable.', {
      status:503,headers:{'Cache-Control':'no-store'},
    });
  }
  // Account endpoints never need redirects: avoid proxying a provider/location
  // response with untrusted Set-Cookie or Location.
  if (upstream.status >= 300 && upstream.status < 400)
    return new Response('Unexpected upstream redirect.', {status:502});
  const outgoing = new Headers({
    'Cache-Control':'no-store',
    'X-Content-Type-Options':'nosniff',
  });
  const contentType = upstream.headers.get('content-type');
  if (contentType) outgoing.set('Content-Type', contentType);
  const cookies = upstream.headers.getSetCookie?.() ?? [];
  if (cookies.length) {
    for (const cookie of cookies) outgoing.append('Set-Cookie',cookie);
  } else {
    const cookie = upstream.headers.get('set-cookie');
    if (cookie) outgoing.append('Set-Cookie',cookie);
  }
  return new Response(upstream.status===204?null:await upstream.arrayBuffer(),{
    status:upstream.status,headers:outgoing,
  });
}

export const GET = proxyAuth;
export const POST = proxyAuth;
export const PATCH = proxyAuth;
export const DELETE = proxyAuth;
export const PUT = proxyAuth;
