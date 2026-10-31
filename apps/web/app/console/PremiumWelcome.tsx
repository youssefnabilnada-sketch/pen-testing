'use client';
import {useState,type FormEvent,type ReactNode} from 'react';
import {ArrowRight,CheckCircle2,CircleHelp,FileCheck2,Globe2,LockKeyhole,ScanLine,Settings2,ShieldCheck,Sparkles} from 'lucide-react';
import {useExperience} from './Experience';

type Props={
 name:string;setName:(value:string)=>void;busy:boolean;verified:boolean;
 onCreate:(event:FormEvent<HTMLFormElement>)=>void|Promise<void>;
 onVerify:(token:string)=>Promise<void>;
 accountTools:ReactNode;
};

export default function PremiumWelcome({name,setName,busy,verified,onCreate,onVerify,accountTools}:Props){
 const {t}=useExperience();
 const [toolsOpen,setToolsOpen]=useState(false);
 const [verifyToken,setVerifyToken]=useState('');
 const [verifying,setVerifying]=useState(false);
 const [verifyError,setVerifyError]=useState('');
 async function verify(e:FormEvent<HTMLFormElement>){
  e.preventDefault();setVerifyError('');setVerifying(true);
  try{await onVerify(verifyToken.trim());setVerifyToken('')}
  catch(err){setVerifyError(err instanceof Error?err.message:t('Verification failed. Try the newest email token.','فشل التحقق، جرب أحدث رمز وصلك بالبريد.'))}
  finally{setVerifying(false)}
 }
 return <div className="premium-welcome">
  <section className="premium-welcome-hero" aria-label={t('Welcome to AEGIS','مرحبًا بك في AEGIS')}>
   <div className="premium-welcome-copy">
    <span className="premium-welcome-overline"><span className="premium-pulse"/>{t('WELCOME TO YOUR SECURITY WORKSPACE','مرحبًا بك في مساحة الأمان الخاصة بك')}</span>
    <h1>{t('A clearer view of','رؤية أوضح')}<span>{t('your security.','لأمان موقعك.')}</span></h1>
    <p>{t('Your websites, security findings and approved fixes. All in one focused workspace. Start with your company — we’ll guide you through the rest.','مواقعك ونتائج الفحص والإصلاحات المعتمدة، كلها في مكان واحد. ابدأ باسم مؤسستك وسنرشدك لباقي الخطوات.')}</p>
    <div className="premium-hero-trust">
     <span><LockKeyhole size={16} aria-hidden="true"/>{t('Private by default','خاص ومحمي')}</span>
     <span><CheckCircle2 size={16} aria-hidden="true"/>{t('You approve every scan','كل فحص بموافقتك')}</span>
    </div>
   </div>
   <div className="premium-welcome-art" aria-hidden="true">
    <div className="premium-orbit premium-orbit-outer"/>
    <div className="premium-orbit premium-orbit-middle"/>
    <div className="premium-orbit premium-orbit-inner"/>
    <div className="premium-core"><ShieldCheck size={83} strokeWidth={1.1}/></div>
    <span className="premium-orbit-node premium-node-one"><Globe2 size={19}/></span>
    <span className="premium-orbit-node premium-node-two"><FileCheck2 size={19}/></span>
    <span className="premium-orbit-node premium-node-three"><ScanLine size={19}/></span>
   </div>
  </section>
  <section className="premium-onboarding-grid" aria-label={t('Set up your workspace','تجهيز مساحة عملك')}>
   <div className="glass premium-onboarding-main">
    <div className="premium-card-heading"><span className="premium-step-chip">01 / 04</span><span className="premium-card-state">{t('READY WHEN YOU ARE','جاهز للبدء')}</span></div>
    <h2>{t('Create your workspace','أنشئ مساحة عملك')}</h2>
    <p>{t('Give your company a name to organize your websites, people and security reports.','اكتب اسم مؤسستك لتنظيم مواقعك وفريقك وتقارير الأمان.')}</p>
    {!verified&&<div className="premium-verification">
      <div className="premium-warning" role="status"><LockKeyhole size={18} aria-hidden="true"/>{t('One step before setup: verify your email. Paste the one-time token from your AEGIS message below.','خطوة واحدة قبل البدء: فعّل بريدك. الصق رمز التفعيل من رسالة AEGIS أدناه.')}</div>
      <form className="premium-inline-verify" onSubmit={verify}>
       <label>{t('Email verification token','رمز تفعيل البريد')}
        <input required type="password" minLength={20} maxLength={150} autoComplete="off" value={verifyToken} onChange={e=>setVerifyToken(e.target.value)} placeholder={t('Paste one-time token','الصق الرمز المرسل')}/>
       </label>
       <button type="submit" disabled={verifying||verifyToken.trim().length<20}>{verifying?t('Verifying…','جارٍ التحقق…'):t('Verify email','تفعيل البريد')}</button>
      </form>
      {verifyError&&<p role="alert" className="error">{verifyError}</p>}
     </div>}
    <form onSubmit={onCreate} className="form premium-onboarding-form">
     <label>{t('Company / workspace name','اسم المؤسسة أو مساحة العمل')}
      <input required type="text" minLength={2} maxLength={120} value={name} onChange={e=>setName(e.target.value)} placeholder={t('e.g. Acme Digital','مثال: شركتي الرقمية')} autoComplete="organization"/>
     </label>
     <button className="primary premium-create-button" disabled={busy||!verified} type="submit">
      {busy?t('Creating workspace…','جارٍ الإنشاء…'):t('Create my workspace','إنشاء مساحة العمل')}<ArrowRight size={18} aria-hidden="true"/>
     </button>
    </form>
    <div className="premium-form-footnote"><ShieldCheck size={16} aria-hidden="true"/>{t('No payment required. Nothing will be scanned or changed automatically.','لا تحتاج إلى دفع. لن يتم فحص أي موقع أو تعديله تلقائيًا.')}</div>
   </div>
   <aside className="glass premium-next-steps">
    <div className="premium-next-heading"><Sparkles size={19} aria-hidden="true"/><span>{t('WHAT HAPPENS NEXT','ماذا بعد؟')}</span></div>
    <div className="premium-next-step"><span className="premium-step-icon"><Globe2 size={21}/></span><div><strong>{t('Add your website','أضف موقعك')}</strong><p>{t('Start with a website you control.','ابدأ بموقع تملكه وتتحكم فيه.')}</p></div></div>
    <div className="premium-next-step"><span className="premium-step-icon"><ShieldCheck size={21}/></span><div><strong>{t('Verify ownership','أثبت الملكية')}</strong><p>{t('Simple instructions, no guessing.','تعليمات واضحة بدون تعقيد.')}</p></div></div>
    <div className="premium-next-step"><span className="premium-step-icon"><ScanLine size={21}/></span><div><strong>{t('Approve your first assessment','وافق على أول فحص')}</strong><p>{t('Review scope before any read-only checks.','راجع نطاق الفحص الآمن أولًا.')}</p></div></div>
    <div className="premium-next-step"><span className="premium-step-icon"><FileCheck2 size={21}/></span><div><strong>{t('Understand and improve','افهم النتائج وحسّن موقعك')}</strong><p>{t('Clear findings, reports and approved fixes.','نتائج واضحة وتقارير وإصلاحات بموافقتك.')}</p></div></div>
   </aside>
  </section>
  <details className="premium-account-details" onToggle={e=>setToolsOpen(e.currentTarget.open)}>
   <summary><span><Settings2 size={18} aria-hidden="true"/>{t('Account, security and invitations','الحساب والأمان والدعوات')}</span><span><CircleHelp size={16} aria-hidden="true"/>{t('Optional settings','إعدادات اختيارية')}</span></summary>
   <p>{t('Manage profile details, authentication settings and existing invitations. These are optional before creating your workspace.','أدِر معلومات الحساب وإعدادات الأمان والدعوات. هذه الخطوات اختيارية قبل إنشاء مساحة العمل.')}</p>
   {toolsOpen&&<div className="premium-account-tools">{accountTools}</div>}
  </details>
 </div>;
}
