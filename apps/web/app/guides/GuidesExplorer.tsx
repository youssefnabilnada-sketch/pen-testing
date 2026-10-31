'use client';
import {useState} from 'react';
import Link from 'next/link';
import {ArrowRight,BookOpen,CheckCircle2,FileCode2,FileText,Globe2,PlayCircle,ShieldCheck} from 'lucide-react';
import SmartVerifyVideoGuide from '../console/SmartVerifyVideoGuide';
import {Experience,useExperience} from '../console/Experience';

type Method='file'|'dns'|'meta';
type Entry={id:string;en:string;ar:string;method:Method};
const providers:Entry[]=[
 {id:'unsure',en:'Any website / I am not sure',ar:'أي موقع / مش عارف المنصة',method:'dns'},
 {id:'wordpress',en:'WordPress',ar:'ووردبريس',method:'meta'},
 {id:'shopify',en:'Shopify',ar:'شوبيفاي',method:'meta'},
 {id:'wix',en:'Wix',ar:'ويكس',method:'dns'},
 {id:'squarespace',en:'Squarespace',ar:'سكوير سبيس',method:'dns'},
 {id:'cloudflare',en:'Cloudflare',ar:'كلاودفلير',method:'dns'},
 {id:'vercel',en:'Vercel',ar:'فيرسل',method:'file'},
 {id:'netlify',en:'Netlify',ar:'نتليفاي',method:'file'},
 {id:'github',en:'GitHub Pages / Git',ar:'GitHub Pages / Git',method:'file'},
 {id:'cpanel',en:'cPanel / Plesk',ar:'cPanel / Plesk',method:'file'},
 {id:'google',en:'Google Search Console',ar:'جوجل سيرش كونسول',method:'dns'}
];
const methods: {id:Method;en:string;ar:string;Icon:typeof FileText}[]=[
 {id:'file',en:'HTML verification file',ar:'ملف تحقق HTML',Icon:FileText},
 {id:'meta',en:'HTML meta tag',ar:'وسم Meta Tag',Icon:FileCode2},
 {id:'dns',en:'DNS TXT record',ar:'سجل DNS TXT',Icon:Globe2}
];
function GuidesContent(){
 const {t}=useExperience();
 const [provider,setProvider]=useState('unsure');
 const [method,setMethod]=useState<Method>('dns');
 const [videoId,setVideoId]=useState('unsure');
 return <main className="guides-public">
  <nav className="guides-nav">
   <Link href="/" className="brand"><ShieldCheck size={24}/> AEGIS <small>SECURITY CLOUD</small></Link>
   <Link href="/console" className="guides-nav-cta">{t('Open workspace','افتح لوحة التحكم')}<ArrowRight size={16}/></Link>
  </nav>
  <header className="guides-hero">
   <span className="guides-kicker"><BookOpen size={16}/>{t('SMARTVERIFY LEARNING CENTER','مركز شرح إثبات الملكية')}</span>
   <h1>{t('Verify your website.','أثبت ملكية موقعك.')} <span>{t('Without the guesswork.','بكل سهولة.')}</span></h1>
   <p>{t('Choose your website platform and watch a short animated walkthrough of the steps. You can see every tutorial before creating an account.','اختار منصة موقعك وشوف شرح متحرك قصير لكل خطوة. تقدر تشوف كل الشروحات بدون إنشاء حساب أو تسجيل دخول.')}</p>
   <div className="guides-points"><span><CheckCircle2 size={15}/>{t('Arabic & English','عربي وإنجليزي')}</span><span><CheckCircle2 size={15}/>{t('No account required to watch','بدون تسجيل دخول')}</span><span><CheckCircle2 size={15}/>{t('Non-destructive verification','إثبات ملكية آمن')}</span></div>
  </header>
  <div className="guides-layout">
   <section className="guides-selector" aria-label={t('Tutorial library','مكتبة الشروحات')}>
    <h2>{t('Choose your platform','اختار منصة موقعك')}</h2>
    <p>{t('Not sure? Choose “Any website”. You can switch methods at any time.','مش عارف المنصة؟ اختار «أي موقع». وتقدر تغير الطريقة في أي وقت.')}</p>
    <div className="guides-provider-grid">
     {providers.map(item=><button key={item.id} type="button" aria-pressed={provider===item.id} onClick={()=>{setProvider(item.id);setMethod(item.method);setVideoId(item.id)}} className={provider===item.id?'chosen':''}>
      <Globe2 size={17}/><span>{t(item.en,item.ar)}</span>{provider===item.id&&<CheckCircle2 size={15}/>}
     </button>)}
    </div>
    <h3>{t('Or explore a universal method','أو اختار طريقة إثبات عامة')}</h3>
    <div className="guides-method-grid">
     {methods.map(({id,en,ar,Icon})=><button key={id} type="button" aria-pressed={method===id} onClick={()=>{setMethod(id);setVideoId(id)}} className={method===id?'chosen':''}><Icon size={19}/><span>{t(en,ar)}</span></button>)}
    </div>
   </section>
   <section className="guides-player-col" aria-label={t('Animated tutorial player','مشغل الشرح المتحرك')}>
    <div className="guides-player-top"><PlayCircle size={19}/><strong>{t('Watch the interactive lesson','شاهد الشرح التفاعلي')}</strong><span>{t('3 short steps','3 خطوات سريعة')}</span></div>
    <div className="guides-mp4">
     <video key={videoId} controls playsInline preload="metadata" aria-label={t('MP4 tutorial video','فيديو شرح MP4')}>
      <source src={'/guides/videos/'+videoId+'.mp4'} type="video/mp4"/>
      {t('Your browser does not support MP4 playback.','متصفحك لا يدعم تشغيل فيديو MP4.')}
     </video>
     <div className="guides-video-meta"><span>{t('Silent bilingual MP4 explainer · 3 steps','فيديو MP4 توضيحي صامت بالعربي والإنجليزي · 3 خطوات')}</span>
     <a href={'/guides/videos/'+videoId+'.mp4'} download={videoId+'.mp4'}>{t('Download MP4','تحميل الفيديو')}</a></div>
    </div>
    <div className="guides-interactive-heading">{t('Or follow the interactive walkthrough','أو استخدم الشرح التفاعلي خطوة بخطوة')}</div>
    <SmartVerifyVideoGuide key={provider+'-'+method} platform={provider} method={method} initiallyOpen/>
    <p className="guides-note">{t('These are original illustrative MP4 and interactive lessons, not real screen recordings of hosting providers. Actual verification tokens are generated only after you sign in to your workspace.','دي فيديوهات MP4 توضيحية أصلية وشروحات تفاعلية، مش تسجيلات حقيقية من حسابات المنصات. رمز الإثبات الحقيقي بيتولد داخل حسابك بعد تسجيل الدخول.')}</p>
    <Link href="/console" className="guides-next">{t('Ready? Open your AEGIS workspace','جاهز؟ افتح لوحة AEGIS')}<ArrowRight size={17}/></Link>
   </section>
  </div>
  <footer className="guides-footer"><ShieldCheck size={16}/>{t('Verification of site control is separate from authorization to scan or change the website.','إثبات التحكم بالموقع منفصل تمامًا عن السماح بفحصه أو تعديله.')}</footer>
 </main>;
}
export default function GuidesExplorer(){return <Experience><GuidesContent/></Experience>}
