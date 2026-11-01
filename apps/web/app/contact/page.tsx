import type {Metadata} from 'next';
import ContactExperience from './ContactExperience';

export const metadata:Metadata={
 title:'Contact AEGIS Security Cloud | Support & Business Inquiries',
 description:'Contact AEGIS Security Cloud for website security platform questions, workspace guidance and business partnerships. Arabic and English support information.',
 alternates:{canonical:'https://aegis-pentest-eg.vercel.app/contact'},
 robots:{index:true,follow:true},
};
export default function ContactPage(){return <ContactExperience/>}
