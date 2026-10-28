import type { NextConfig } from 'next';
import {apiOrigin} from './lib/deployment';
const backend=apiOrigin(process.env);
const config: NextConfig = {
  output: 'standalone',
  experimental: { cpus: 2 },
  async rewrites() { return [{source: '/api/:path*', destination: `${backend}/:path*`}]; },
  async headers() { return [{source:'/:path*',headers:[{key:'X-Content-Type-Options',value:'nosniff'},{key:'X-Frame-Options',value:'DENY'},{key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},{key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'}]}]; }
};
export default config;
