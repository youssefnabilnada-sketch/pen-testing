import {NextResponse} from 'next/server';
export const dynamic='force-dynamic';
export const runtime='nodejs';
export function GET(){
 const isPreview=process.env.VERCEL_ENV==='preview';
 const key=process.env.AEGIS_PREVIEW_GATEWAY_KEY||'';
 const previewConfigured=process.env.AEGIS_PREVIEW_AUTH_ENABLED==='true' &&
  key.length>=48 && /^[A-Za-z0-9_-]+$/.test(key);
 // Configuration-only signal, not a claim that live upstream login will succeed.
 return NextResponse.json({
  preview:isPreview,
  signInConfigured: !isPreview||previewConfigured,
 },{headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
}
