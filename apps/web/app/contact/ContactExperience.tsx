'use client';
import {useState} from 'react';
import Link from 'next/link';
import {ArrowUpRight,CheckCircle2,Copy,Globe2,HelpCircle,LockKeyhole,Mail,MessageSquare,ShieldCheck} from 'lucide-react';
import {Experience,useExperience} from '../console/Experience';

export const AEGIS_CONTACT_EMAIL='aegis.pentest@gmail.com';
const contactUrl='mailto:'+AEGIS_CONTACT_EMAIL;
function ContactContent(){
 const {t}=useExperience();
 const [copied,setCopied]=useState(false);
 async function copy(){
  try{await navigator.clipboard.writeText(AEGIS_CONTACT_EMAIL);setCopied(true)}
  catch{setCopied(false)}
 }
 return <main className="landing aegis-contact">
  <nav className="landing-nav contact-nav" aria-label={t('Contact navigation','قائمة التواصل')}>
   <Link href="/" className="brand"><ShieldCheck size={22}/> AEGIS <small>SECURITY CLOUD</small></Link>
   <div className="contact-nav-links"><Link href="/platform">{t('Explore platform','تعرف على المنصة')}</Link><Link href="/guides">{t('Help guides','شروحات التحقق')}</Link></div>
   <Link href="/console" className="button ghost">{t('Open workspace','دخول المنصة')}<ArrowUpRight size={16}/></Link>
  </nav>
  <section className="contact-hero">
   <p className="eyebrow"><span className="dot"/>{t('WE ARE HERE TO HELP','معاك في كل خطوة')}</p>
   <h1>{t('Let’s talk about','تواصل مع')} <span>AEGIS.</span></h1>
   <p className="lead">{t('Questions about getting started, verifying your website or exploring a partnership? Reach us through our public contact address.','عندك سؤال عن التسجيل أو إثبات ملكية موقعك أو مهتم بالتعاون معنا؟ تواصل معانا من خلال البريد المخصص للتواصل.')}</p>
   <div className="contact-grid">
    <section className="glass contact-main-card" aria-labelledby="contact-email-title">
     <span className="contact-icon"><Mail size={27} aria-hidden="true"/></span>
     <h2 id="contact-email-title">{t('Contact us by email','تواصل معنا بالبريد')}</h2>
     <p>{t('General questions, onboarding help and partnership inquiries.','للاستفسارات العامة، ومساعدة بدء الاستخدام، وفرص التعاون.')}</p>
     <a className="contact-address" href={contactUrl} dir="ltr">{AEGIS_CONTACT_EMAIL}</a>
     <div className="contact-actions">
      <a className="button primary" href={contactUrl+'?subject=AEGIS%20Security%20Cloud%20-%20Inquiry'}><Mail size={17}/>{t('Write an email','ابعت رسالة')}</a>
      <button type="button" className="contact-copy-button" onClick={()=>void copy()} aria-label={t('Copy contact email','نسخ بريد التواصل')}>{copied?<CheckCircle2 size={17}/>:<Copy size={17}/>} {copied?t('Copied','تم النسخ'):t('Copy address','نسخ البريد')}</button>
     </div>
     <small>{t('This is the public contact address, not the sender for one-time verification codes.','ده بريد التواصل مع الإدارة، مش البريد المستخدم لإرسال أكواد التفعيل.')}</small>
    </section>
    <section className="contact-help-card glass" aria-labelledby="contact-help-title">
     <span className="contact-icon"><HelpCircle size={26} aria-hidden="true"/></span>
     <h2 id="contact-help-title">{t('Need help using AEGIS?','محتاج مساعدة في استخدام AEGIS؟')}</h2>
     <p>{t('Use our guided walkthrough inside the workspace to learn exactly how to add a website, place a verification file and start an authorized assessment.','استخدم المساعد التفاعلي داخل المنصة علشان تعرف تضيف موقعك، وترفع ملف إثبات الملكية في المكان الصحيح، وتبدأ فحصًا بتصريح واضح.')}</p>
     <Link href="/console" className="contact-text-link"><Globe2 size={17}/>{t('Open the guided workspace','افتح مساحة العمل والمساعد')}<ArrowUpRight size={16}/></Link>
     <Link href="/guides" className="contact-text-link"><MessageSquare size={17}/>{t('See verification tutorials','شاهد شروحات إثبات الملكية')}<ArrowUpRight size={16}/></Link>
     <p className="contact-help-note"><LockKeyhole size={15}/>{t('Already signed in? Workspace Support lets you track account-specific tickets.','مسجل دخول بالفعل؟ قسم «الدعم» داخل المنصة مخصص لمتابعة طلبات الدعم الخاصة بحسابك.')}</p>
    </section>
   </div>
   <aside className="contact-security-tip"><ShieldCheck size={19}/><p>{t('For your safety, never email passwords, one-time codes, Firebase credentials, private keys or sensitive scan evidence. Describe the problem without secrets and use workspace Support for account-specific questions.','لحماية حسابك، ما تبعتش كلمات مرور أو أكواد تفعيل أو مفاتيح Firebase أو مفاتيح SSH أو أدلة أمنية حساسة بالبريد. اشرح المشكلة بدون أسرار واستخدم الدعم داخل المنصة للحالات المرتبطة بحسابك.')}</p></aside>
  </section>
  <footer className="contact-footer"><Link href="/" className="brand"><ShieldCheck size={20}/> AEGIS</Link><span>{t('Authorized security, clearer guidance.','أمان مصرح به وإرشاد أوضح.')}</span><div><Link href="/trust">{t('Trust Center','مركز الثقة')}</Link><Link href="/platform">{t('What AEGIS does','ماذا تقدم AEGIS؟')}</Link><Link href="/console">{t('Workspace','مساحة العمل')}</Link></div></footer>
 </main>;
}
export default function ContactExperience(){return <Experience><ContactContent/></Experience>}
