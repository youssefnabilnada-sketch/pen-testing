import type {Metadata} from 'next';
import AboutExperience from './AboutExperience';

export const metadata: Metadata = {
 title: 'About AEGIS | Mission, Vision & Responsible Website Security',
 description: 'Discover the mission and vision behind AEGIS Security Cloud, how authorized website checks work, and how findings become reviewed improvements. English and Arabic.',
 robots: {index:true, follow:true},
 alternates: {canonical:'https://aegis-pentest-eg.vercel.app/about'},
};
export default function AboutPage(){return <AboutExperience/>}
