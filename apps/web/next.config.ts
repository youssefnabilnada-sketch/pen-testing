import type { NextConfig } from 'next';
import {apiOrigin} from './lib/deployment';
// The production branch still requires a live HTTPS API. This temporary PREVIEW
// branch renders the *real* frontend while the external API is being provisioned.
// Adding API_INTERNAL_URL automatically restores the same-origin API proxy.
const hasBackend = Boolean(process.env.API_INTERNAL_URL);
const backend = hasBackend || process.env.VERCEL_ENV === 'production' ? apiOrigin(process.env) : null;
const config: NextConfig = {
  output: 'standalone',
  experimental: { cpus: 2 },
  async rewrites() {
    return backend ? [{source: '/api/:path*', destination: `${backend}/:path*`}] : [];
  },
  async headers() {
    return [{source:'/:path*',headers:[
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'X-Frame-Options',value:'DENY'},
      {key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},
      {key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'}
    ]}];
  }
};
export default config;
