import type {Metadata} from 'next';
import AboutExperience from '../about/AboutExperience';

export const metadata:Metadata={
 title:'Explore AEGIS | What It Does, How It Works & Security Features',
 description:'A complete guide to AEGIS Security Cloud: website ownership verification, authorized assessments, reports, guided remediation, FastFix boundaries, monitoring, retesting, mission and vision. English and Arabic.',
 robots:{index:true,follow:true},
 alternates:{canonical:'https://aegis-pentest-eg.vercel.app/platform'},
};
export default function PlatformPage(){return <AboutExperience/>}
