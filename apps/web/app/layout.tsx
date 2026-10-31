import './globals.css';
import './workspace-premium.css';
import './ownership-experience.css';
import type { Metadata } from 'next';
export const metadata: Metadata = {title: 'AEGIS • Security Cloud', description: 'Clarity for your security posture. Authorized configuration assessments and remediation.'};
export default function Layout({children}: {children: React.ReactNode}) {return <html lang="en"><body>{children}</body></html>}
