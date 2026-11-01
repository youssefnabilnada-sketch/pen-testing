import type { NextConfig } from 'next';
import {apiOrigin} from './lib/deployment';
// Preserve the fail-closed build guard without publishing a wildcard API rewrite.
apiOrigin(process.env);
const config: NextConfig = {
  output: 'standalone',
  experimental: { cpus: 2 },
  async headers() { return [
   {source:'/:path*',headers:[{key:'X-Content-Type-Options',value:'nosniff'},{key:'X-Frame-Options',value:'DENY'},{key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},{key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'}]},
   // Only the explicit first-party Firebase auth helper may be framed by AEGIS.
   {source:'/__/auth/:path*',headers:[{key:'X-Frame-Options',value:'SAMEORIGIN'},{key:'Cache-Control',value:'no-store'}]},
  ]; }
};
export default config;
