import type { NextConfig } from 'next';
// Temporary public marketing preview while the production API is not deployed.
// No backend proxy and no live customer console in this branch.
const config: NextConfig = {
  output: 'standalone',
  experimental: { cpus: 2 },
  async redirects() { return [{ source: '/console', destination: '/#preview', permanent: false }]; },
  async headers() {
    return [{source:'/:path*',headers:[
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'X-Frame-Options',value:'DENY'},
      {key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},
      {key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'},
    ]}];
  },
};
export default config;
