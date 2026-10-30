import type { NextConfig } from 'next';
import {apiOrigin} from './lib/deployment';
// Preserve the fail-closed build guard without publishing a wildcard API rewrite.
apiOrigin(process.env);
const config: NextConfig = {
  output: 'standalone',
  experimental: { cpus: 2 },
  async headers() { return [{source:'/:path*',headers:[{key:'X-Content-Type-Options',value:'nosniff'},{key:'X-Frame-Options',value:'DENY'},{key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},{key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'}]}]; }
};
export default config;
