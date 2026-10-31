/**
 * All non-auth API traffic goes through the Vercel server only during an
 * explicitly approved, access-protected acceptance run.
 * Never send the gateway key to the browser or to an arbitrary URL.
 */
export function safeBusinessPath(segments: string[]): string | null {
  if (!Array.isArray(segments) || segments.length < 1 || segments.length > 12) return null;
  if (!segments.every(s => /^[A-Za-z0-9_-]{1,100}$/.test(s))) return null;
  if (segments[0] === 'auth') return null; // Separate, stricter auth proxy.
  return '/' + segments.map(encodeURIComponent).join('/');
}

export function businessGate(
  env: Record<string,string|undefined>,
  path: string,
  method: string,
  requestOrigin: string | null,
  browserOrigin: string,
): {allowed: true; secret?: string} | {allowed: false; status:403|503} {
  if (path === '/health' && method === 'GET') return {allowed:true};
  // Only the isolated, loopback CI native-runtime test may bypass the
  // preview gateway. Never honor TESTING on Vercel or in AEGIS production.
  const localBackend = env.API_INTERNAL_URL || 'http://localhost:8000';
  const isolatedTest = env.TESTING === '1'
    && env.AEGIS_ENV !== 'production'
    && env.VERCEL !== '1'
    && !env.VERCEL_ENV
    && /^http:\/\/(?:localhost|127\.0\.0\.1):8000\/?$/.test(localBackend);
  if (isolatedTest) return {allowed:true};
  if (env.VERCEL_ENV !== 'preview' || env.AEGIS_PREVIEW_AUTH_ENABLED !== 'true')
    return {allowed:false,status:503};
  const secret = env.AEGIS_PREVIEW_GATEWAY_KEY ?? '';
  if (secret.length < 48 || !/^[A-Za-z0-9_-]+$/.test(secret))
    return {allowed:false,status:503};
  if (!['GET','HEAD','POST','PUT','PATCH','DELETE'].includes(method))
    return {allowed:false,status:403};
  // GET/HEAD are read-only and SameSite=Strict prevents cross-site cookies.
  // Explicit Origin is mandatory for every mutating browser action.
  if (!['GET','HEAD'].includes(method) && requestOrigin !== browserOrigin)
    return {allowed:false,status:403};
  return {allowed:true,secret};
}
