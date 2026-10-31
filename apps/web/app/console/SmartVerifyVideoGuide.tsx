'use client';
import {useEffect,useState} from 'react';
import {ArrowLeft,ArrowRight,CheckCircle2,FileCode2,FileText,Globe2,Pause,Play,RotateCcw,ShieldCheck,Sparkles} from 'lucide-react';
import {useExperience} from './Experience';
import {guides} from './SmartVerifyPlatformGuide';

type TextPair=[string,string];
const lessonSeconds=5;
const proofLessons:Record<string,{title:TextPair;steps:[TextPair,TextPair,TextPair]}> = {
 file:{title:['Verify with an HTML file','إثبات الملكية بملف HTML'],steps:[
  ['Download your unique file from AEGIS.','نزّل ملف التحقق المخصص لموقعك من AEGIS.'],
  ['Upload it unchanged to the exact public .well-known path on your website.','ارفع الملف بدون تعديل داخل مسار .well-known المحدد على موقعك.'],
  ['Open the file URL, then choose Check ownership.','تأكد من فتح رابط الملف، ثم اضغط تحقق من الملكية.']
 ]},
 dns:{title:['Verify with a DNS TXT record','إثبات الملكية بسجل DNS TXT'],steps:[
  ['Copy the AEGIS TXT record name and value.','انسخ اسم وقيمة سجل TXT المخصص من AEGIS.'],
  ['Add it to the DNS settings of the exact domain you control.','أضفه في إعدادات DNS لنفس الدومين الذي تتحكم فيه.'],
  ['Allow time for propagation, then choose Check ownership.','انتظر انتشار السجل، ثم اضغط تحقق من الملكية.']
 ]},
 meta:{title:['Verify with an HTML meta tag','إثبات الملكية بوسم Meta Tag'],steps:[
  ['Copy the unique meta tag from AEGIS.','انسخ وسم Meta Tag المخصص من AEGIS.'],
  ['Paste it in the public homepage HTML head or trusted site settings.','ضعه في رأس الصفحة الرئيسية أو إعدادات الموقع الموثوقة.'],
  ['Publish, clear cache and choose Check ownership.','انشر التغيير وامسح الكاش واضغط تحقق من الملكية.']
 ]}
};
const platformNames:Record<string,TextPair> = {
 github:['GitHub / GitHub Pages','GitHub / GitHub Pages'],vercel:['Vercel','فيرسل'],
 wordpress:['WordPress','ووردبريس'],shopify:['Shopify','شوبيفاي'],
 wix:['Wix','ويكس'],squarespace:['Squarespace','سكوير سبيس'],
 cloudflare:['Cloudflare','كلاودفلير'],cpanel:['cPanel / Plesk','سي بانل / بليسك'],
 netlify:['Netlify','نتليفاي'],google:['Google Search Console','جوجل سيرش كونسول'],
 unsure:['Any website','أي موقع']
};
export default function SmartVerifyVideoGuide({platform,method,initiallyOpen=false}:{platform:string;method:string;initiallyOpen?:boolean}){
 const {t}=useExperience();
 const [open,setOpen]=useState(initiallyOpen);
 const [mode,setMode]=useState<'platform'|'proof'>('platform');
 const [step,setStep]=useState(0);
 const [playing,setPlaying]=useState(false);
 const selectedPlatform=guides[platform]||guides.unsure;
 const selectedProof=proofLessons[method]||proofLessons.dns;
 const steps=mode==='platform'?selectedPlatform.steps:selectedProof.steps;
 const title=mode==='platform'?(platformNames[platform]||platformNames.unsure):selectedProof.title;
 useEffect(()=>{setStep(0);setPlaying(false)},[platform,method,mode]);
 useEffect(()=>{
  if(!open||!playing)return;
  const timer=window.setTimeout(()=>{
   if(step===steps.length-1)setPlaying(false);
   else setStep(s=>s+1);
  },lessonSeconds*1000);
  return()=>window.clearTimeout(timer);
 },[open,playing,step,steps.length]);
 function navigate(next:number){setPlaying(false);setStep(Math.max(0,Math.min(steps.length-1,next)))}
 function toggle(){
  if(!open){setOpen(true);setPlaying(!(typeof window.matchMedia==='function'&&window.matchMedia('(prefers-reduced-motion: reduce)').matches));setStep(0)}
  else setOpen(false);
 }
 const Icon=mode==='platform'?Globe2:method==='file'?FileText:method==='meta'?FileCode2:Globe2;
 return <section className="sv-video-lessons" aria-label={t('Video-style ownership tutorials','شروحات إثبات الملكية المتحركة')}>
  <div className="sv-video-intro">
   <div><span className="sv-video-eyebrow"><Sparkles size={13}/>{t('SMARTVERIFY VISUAL LESSONS','شروحات SMARTVERIFY المصورة')}</span>
    <h4>{t('Watch the steps before you begin','شوف الخطوات قبل ما تبدأ')}</h4>
    <p>{t('Short animated walkthroughs in English and Arabic. No provider login, installation, or account password is needed to watch.','شروحات متحركة قصيرة بالعربي والإنجليزي، بدون تسجيل دخول لأي منصة أو إدخال كلمة مرور.')}</p>
   </div>
   <button type="button" className="sv-video-open" aria-expanded={open} onClick={toggle}><Play size={16}/>{open?t('Hide lesson','إغلاق الشرح'):t('Watch animated guide','شاهد الشرح المتحرك')}</button>
  </div>
  {open&&<div className="sv-video-screen">
   <div className="sv-video-modes" role="group" aria-label={t('Choose tutorial','اختر الشرح')}>
    <button type="button" aria-pressed={mode==='platform'} onClick={()=>setMode('platform')}>{t('My website platform','منصة موقعي')}</button>
    <button type="button" aria-pressed={mode==='proof'} onClick={()=>setMode('proof')}>{t('Verification method','طريقة الإثبات')}</button>
   </div>
   <div className="sv-video-stage" aria-live="off">
    <span className="sv-video-step-label">{t('STEP','الخطوة')} {step+1} / {steps.length}</span>
    <div className="sv-video-illustration" aria-hidden="true">
     <span className="sv-video-orb"><Icon size={38} strokeWidth={1.7}/></span>
     <span className="sv-video-connect"><span/></span>
     <span className="sv-video-orb secondary"><CheckCircle2 size={38} strokeWidth={1.7}/></span>
    </div>
    <h5>{t(...title)}</h5>
    <p key={mode+'-'+platform+'-'+method+'-'+step} className="sv-video-scene-copy">{t(...steps[step])}</p>
    <span className="sv-video-demo-label">{t('Illustration · use your actual AEGIS verification token','رسم توضيحي · استخدم رمز التحقق الحقيقي من AEGIS')}</span>
   </div>
   <div className="sv-video-timeline" aria-label={t('Lesson progress','تقدم الشرح')}>
    {steps.map((_,i)=><button type="button" key={i} aria-label={t('Show step '+(i+1),'عرض الخطوة '+(i+1))} onClick={()=>navigate(i)} aria-current={step===i?'step':undefined}>
     <span className={i<step?'done':i===step?'current':''} key={i+'-'+step+'-'+playing}>
      {i<step?<i/>:i===step&&playing?<b/>:null}
     </span>
    </button>)}
   </div>
   <div className="sv-video-controls">
    <button type="button" onClick={()=>navigate(step-1)} disabled={step===0}><ArrowLeft size={15}/>{t('Previous','السابق')}</button>
    <button type="button" onClick={()=>{if(step===steps.length-1){setStep(0);setPlaying(true)}else setPlaying(v=>!v)}}>
     {playing?<><Pause size={15}/>{t('Pause','إيقاف مؤقت')}</>:step===steps.length-1?<><RotateCcw size={15}/>{t('Replay','إعادة')}</>:<><Play size={15}/>{t('Play','تشغيل')}</>}
    </button>
    <button type="button" onClick={()=>navigate(step+1)} disabled={step===steps.length-1}>{t('Next','التالي')}<ArrowRight size={15}/></button>
   </div>
   <p className="sv-video-safety"><ShieldCheck size={15}/>{t('This animation is a guide, not a recording of a live provider account. Only the real AEGIS verification check confirms ownership; it never starts a scan.','الشرح رسم متحرك وليس تسجيلًا من حساب منصة حقيقي. إثبات الملكية يتم فقط بالتحقق الفعلي في AEGIS، ولا يبدأ الفحص تلقائيًا.')}</p>
  </div>}
 </section>;
}
