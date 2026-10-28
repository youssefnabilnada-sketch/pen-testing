import './globals.css';
import type { Metadata } from 'next';
export const metadata: Metadata = {title: 'AEGIS • Security Cloud', description: 'Clarity for your security posture. Authorized configuration assessments and remediation.'};
export default function Layout({children}: {children: React.ReactNode}) {
 const awaitingApi = process.env.VERCEL === '1' && !process.env.API_INTERNAL_URL;
 return <html lang="en"><body>
  {awaitingApi&&<div role="status" style={{padding:'13px 22px',background:'#172234',borderBottom:'1px solid #ffffff24',textAlign:'center',color:'#dbe7f5',fontSize:13}}>
    AEGIS frontend preview is online. Backend services are not connected yet. Sign-in, assessments, monitoring, and reports require the live API.
  </div>}
  {children}
 </body></html>;
}
