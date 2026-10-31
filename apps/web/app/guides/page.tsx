import type {Metadata} from 'next';
import GuidesExplorer from './GuidesExplorer';

export const metadata:Metadata={
 title:'SmartVerify Tutorials | AEGIS Security Cloud',
 description:'Free step-by-step animated website ownership verification tutorials in Arabic and English. WordPress, Shopify, Wix, DNS TXT, HTML File, Meta Tag and more.',
 robots:{index:true,follow:true},
};

export default function GuidesPage(){return <GuidesExplorer/>}
