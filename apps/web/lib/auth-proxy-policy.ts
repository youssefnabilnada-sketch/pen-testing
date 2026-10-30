/** Shared validation for server-only AEGIS auth proxy.
 * Keep every preview gateway secret out of NEXT_PUBLIC_* and browser bundles.
 */
export function authPath(segments: string[]): string | null {
  if (!Array.isArray(segments) || segments.length < 1 || segments.length > 6) return null;
  if (!segments.every(s => /^[A-Za-z0-9_-]{1,80}$/.test(s))) return null;
  return '/auth/' + segments.map(encodeURIComponent).join('/');
}

type Config = Record<string, string | undefined>;

export function previewProxyGate(
  env: Config,
  requestOrigin: string | null,
  actualOrigin: string,
  method: string,
): { allowed: true; secret?: string } | { allowed: false; status: 403 | 503 } {
  const enabled = env.AEGIS_PREVIEW_AUTH_ENABLED === 'true';
  if (!enabled) return { allowed: true };
  // Never enable the preview-only shared gate in a production deployment.
  if (env.VERCEL_ENV !== 'preview') return { allowed: false, status: 503 };
  const secret = env.AEGIS_PREVIEW_GATEWAY_KEY ?? '';
  // Setup error: never send an empty/placeholder token to the API gateway.
  if (secret.length < 48 || !/^[A-Za-z0-9_-]+$/.test(secret)) {
    return { allowed: false, status: 503 };
  }
  // Read operations carry no browser Origin; state-changing actions must.
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase()) &&
      (!requestOrigin || requestOrigin !== actualOrigin)) {
    return { allowed: false, status: 403 };
  }
  return { allowed: true, secret };
}

/** Strip unrelated Vercel/session cookies before forwarding to the private API. */
export function aegisSessionCookie(raw: string | null): string | null {
  if (!raw) return null;
  for (const item of raw.split(';')) {
    const part = item.trim();
    if (/^aegis_session=[A-Za-z0-9_-]{32,256}$/.test(part)) return part;
  }
  return null;
}
