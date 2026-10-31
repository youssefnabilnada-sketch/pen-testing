/** Human-readable authentication errors without leaking secrets or internal URLs.
 * A non-JSON Caddy/Vercel 502/503 must never look like a password error.
 */
export function accountErrorMessage(status:number,path:string,backendDetail?:string):string{
 if(path==='/auth/login'&&status===401)
  return 'Invalid email or password. Check the exact AEGIS account address (including any +alias) and password. Leave the authenticator code empty unless MFA is enabled.';
 if(status===429)return 'Too many sign-in attempts (HTTP 429). Please try again later.';
 if(status===503)return 'Account service temporarily unavailable (HTTP 503). The secure gateway or backend may not be ready. Your password was not identified as incorrect.';
 if(status===502||status===504)return 'AEGIS cannot reach the account service (HTTP '+status+'). Please try again later. This is not a password error.';
 if(status===403)return 'Account request blocked by access policy (HTTP 403). Confirm you are using the official website address.';
 if(status>=500)return 'AEGIS account service error (HTTP '+status+'). Please retry later.';
 if(backendDetail && backendDetail.length<=240)return backendDetail;
 return 'Account request failed (HTTP '+status+'). Please check your details or try again.';
}
export const ACCOUNT_NETWORK_ERROR='Could not connect to AEGIS. Check your connection and retry. If this persists, the account service may be unavailable.';
