/**
 * Suggests only plain public GET path candidates from a user-pasted OpenAPI 3 document.
 * This never sends a request or authorizes a scan; server scope checks still apply.
 */
const SENSITIVE_SEGMENTS = new Set([
  'logout', 'signout', 'delete', 'remove', 'unsubscribe', 'checkout',
  'purchase', 'pay', 'admin', 'wp-admin', 'login', 'signin', 'account',
  'reset', 'restart', 'reboot', 'shutdown', 'flush', 'purge', 'revoke',
  'disable', 'enable', 'activate', 'deactivate', 'suspend', 'terminate',
  'password', 'token', 'session', 'billing', 'payment', 'refund'
]);
const PLAIN_PATH = /^\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_.-]*$/;
const record = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

export function isSafeCandidatePath(path: string): boolean {
  return path.length <= 200 && PLAIN_PATH.test(path) &&
    path.split('/').every(part => part !== '.' && part !== '..' &&
      !part.toLowerCase().split(/[-_.]/).some(word => SENSITIVE_SEGMENTS.has(word)));
}

/**
 * We never send custom headers, cookies, query strings, or request bodies.
 * Reject endpoints that need them; unresolved parameters cannot be proven safe.
 */
function hasUnsupportedParameters(value: unknown): boolean {
  if (value === undefined) return false;
  if (!Array.isArray(value)) return true;
  return value.some(param => !record(param) || Object.hasOwn(param, '$ref') ||
    param.in !== 'query' || param.required !== false ||
    typeof param.name !== 'string' || !param.name ||
    Object.hasOwn(param, 'content'));
}

/** Root OpenAPI server definitions are advisory, not authorization. A pasted
 * document must not silently propose requests for a different host or an
 * API mounted under a base path which this importer cannot reproduce. */
function supportedDocumentServer(value: Record<string, unknown>, approvedOrigin?: string): boolean {
  if (!Object.hasOwn(value, 'servers')) return true;
  const servers = value.servers;
  if (!approvedOrigin || !Array.isArray(servers) || servers.length !== 1 || !record(servers[0]) ||
      typeof servers[0].url !== 'string' || Object.hasOwn(servers[0], 'variables')) return false;
  if (servers[0].url === '/') return true;
  try {
    const target = new URL(servers[0].url);
    const approved = new URL(approvedOrigin);
    return ['http:', 'https:'].includes(target.protocol) &&
      target.origin === approved.origin && target.username === '' && target.password === '' &&
      (target.pathname === '/' || target.pathname === '') && !target.search && !target.hash;
  } catch {
    return false;
  }
}

export function getOpenApiCandidates(value: unknown, approvedOrigin?: string): string[] {
  if (!record(value) || typeof value.openapi !== 'string' || !/^3\.\d+\.\d+$/.test(value.openapi)
    || !record(value.paths)) {
    throw new Error('Use an OpenAPI 3 JSON document containing a paths object.');
  }
  if (!supportedDocumentServer(value, approvedOrigin)) {
    throw new Error('OpenAPI server must match the selected verified API origin and have no base path.');
  }
  const paths = Object.entries(value.paths);
  if (paths.length > 1000) {
    throw new Error('OpenAPI document contains too many paths for a bounded import.');
  }
  const candidates: string[] = [];
  for (const [path, entry] of paths) {
    if (!isSafeCandidatePath(path) || !record(entry) || Object.hasOwn(entry, '$ref')
      || Object.hasOwn(entry, 'servers') || hasUnsupportedParameters(entry.parameters)
      || !Object.hasOwn(entry, 'get') || !record(entry.get)) continue;
    // Protected endpoints cannot be assessed by the unauthenticated API response profile.
    const operation = entry.get;
    const security = Object.hasOwn(operation, 'security') ? operation.security : value.security;
    if (security !== undefined && (!Array.isArray(security) || security.length > 0)) continue;
    if (Object.hasOwn(operation, 'requestBody') || Object.hasOwn(operation, '$ref')
      || Object.hasOwn(operation, 'servers') || hasUnsupportedParameters(operation.parameters)) continue;
    candidates.push(path);
  }
  if (!candidates.length || candidates.length > 20) {
    throw new Error('Choose a document containing 1–20 public, plain GET paths. Templates, protected paths and external references are excluded.');
  }
  return candidates;
}
