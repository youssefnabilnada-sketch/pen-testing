'use client';
import {useEffect,useId,useState} from 'react';
import Link from 'next/link';
import {ArrowLeft,ArrowRight,BookOpen,CheckCircle2,ChevronRight,CircleHelp,ExternalLink,FileCheck2,Globe2,LockKeyhole,Mail,ShieldCheck,Sparkles,X} from 'lucide-react';
import {useExperience} from './Experience';

type Pair={en:string;ar:string};
type Host='vercel'|'github'|'wordpress'|'shopify'|'cloudflare'|'cpanel'|'netlify'|'wix'|'other';
type Step={title:Pair;explain:Pair;tasks:Pair[];target?:'Assets'|'Assessments'|'Findings'};
const steps:Step[]=[
 {title:{en:'Create an AEGIS account',ar:'أنشئ حساب AEGIS'},
  explain:{en:'Start with your email and a strong password. Google sign-in is optional; email registration is available independently.',ar:'ابدأ ببريدك الإلكتروني وكلمة مرور قوية. تسجيل Google اختياري، والتسجيل بالبريد يعمل بشكل مستقل.'},
  tasks:[{en:'Open Register, enter your email and set a password of at least 12 characters.',ar:'افتح تسجيل حساب جديد، واكتب بريدك وكلمة مرور من 12 حرفًا على الأقل.'},{en:'Submit registration, then look for the AEGIS verification message.',ar:'أكمل التسجيل ثم ابحث عن رسالة التفعيل من AEGIS.'}]},
 {title:{en:'Verify your email',ar:'فعّل بريدك الإلكتروني'},
  explain:{en:'Verification confirms access to your email, not ownership of a website.',ar:'تفعيل البريد يثبت وصولك لبريد الحساب، لكنه لا يثبت ملكية الموقع.'},
  tasks:[{en:'Find the latest AEGIS message in Inbox or Spam, and open the verification link or copy its one-time token.',ar:'ابحث عن أحدث رسالة AEGIS في الوارد أو Spam، وافتح رابط التفعيل أو انسخ الرمز المؤقت.'},{en:'Open Verify email in AEGIS, paste the token and submit.',ar:'افتح «تحقق من البريد» داخل AEGIS، والصق الرمز واضغط تفعيل.'},{en:'If the token expired, use Resend verification email. A new email is conditional and rate-limited; avoid repeated requests.',ar:'لو انتهت صلاحية الكود، استخدم «إعادة إرسال تفعيل البريد». إرسال رسالة جديدة مشروط وبحد للطلبات؛ ما تكررّش الضغط بسرعة.'}]},
 {title:{en:'Set up your workspace',ar:'جهّز مساحة العمل'},
  explain:{en:'Your workspace keeps your owned websites, assessments and reports together.',ar:'مساحة العمل بتنظم مواقعك والفحوص والتقارير في مكان واحد.'},
  tasks:[{en:'After signing in, enter a company or workspace name and select Create my workspace.',ar:'بعد الدخول، اكتب اسم الشركة أو مساحة العمل واضغط «إنشاء مساحة العمل».'},{en:'You can add teammates later; creating a workspace does not start a scan.',ar:'تقدر تضيف فريقك لاحقًا؛ إنشاء مساحة العمل لا يبدأ أي فحص.'}]},
 {title:{en:'Add your website',ar:'أضف موقعك'},
  explain:{en:'Only add a website you own or have explicit permission to manage.',ar:'أضف فقط موقعًا تملكه أو لديك تصريح واضح لإدارته.'},
  tasks:[{en:'Open My websites and enter the exact public HTTPS URL, including the correct domain or subdomain.',ar:'افتح «مواقعي» واكتب رابط HTTPS العام كاملًا بالدومين أو النطاق الفرعي الصحيح.'},{en:'Select Add website, then choose Continue on the website you want to verify.',ar:'اضغط «أضف الموقع»، ثم «متابعة» عند الموقع الذي تريد إثبات ملكيته.'}],target:'Assets'},
 {title:{en:'Prove website ownership',ar:'أثبت ملكية الموقع'},
  explain:{en:'AEGIS checks a unique proof on the live website. Choose your hosting platform below to see exactly where the proof goes.',ar:'AEGIS بتتحقق من إثبات فريد على موقعك المنشور. اختار منصة الاستضافة تحت علشان تعرف تحط الإثبات فين بالضبط.'},
  tasks:[{en:'Open My websites, select your website and choose the platform hosting it.',ar:'افتح «مواقعي»، وحدد موقعك واختار منصة الاستضافة.'},{en:'Select Get verification instructions. Use only the exact generated proof and path shown for your website.',ar:'اضغط «عرض خطوات التحقق». استخدم فقط رمز الإثبات والمسار الفعلي اللي AEGIS بتعرضه لموقعك.'},{en:'Publish your change, then press Check ownership. Ownership proof never starts a scan.',ar:'انشر التعديل، ثم اضغط «تحقق من الملكية». إثبات الملكية لا يبدأ فحصًا.'}],target:'Assets'},
 {title:{en:'Approve and start a safe assessment',ar:'وافق وابدأ فحصًا آمنًا'},
  explain:{en:'A verified website still needs a separate, explicit authorization before AEGIS runs bounded non-destructive checks.',ar:'حتى بعد إثبات ملكية الموقع، لازم توافق بشكل منفصل وواضح قبل تشغيل فحوص محدودة وغير تخريبية.'},
  tasks:[{en:'In My websites, select your verified website and read the exact assessment scope.',ar:'في «مواقعي»، اختار موقعًا تم إثبات ملكيته واقرأ نطاق الفحص المحدد.'},{en:'Confirm you own or control the site and approve the read-only assessment.',ar:'أكد إنك تملك أو تدير الموقع ووافق على الفحص الذي لا يعدل المحتوى.'},{en:'Select Start authorized assessment. Open Security assessments to follow progress. Failed jobs are not clean results.',ar:'اضغط «بدء الفحص بموافقتي»، ثم افتح «الفحوص الأمنية» لمتابعة التنفيذ. الفحص الفاشل مش نتيجة سليمة.'}],target:'Assets'},
 {title:{en:'Understand the results and next steps',ar:'افهم النتائج والخطوة التالية'},
  explain:{en:'Use real findings and reports to plan improvements. A proposed fix does not mean the website was changed.',ar:'اعتمد على النتائج والتقارير الفعلية لتخطيط التحسينات. اقتراح الإصلاح لا يعني إنه اتطبق على الموقع.'},
  tasks:[{en:'Open Findings & fixes to review supported observations, evidence and recommendations.',ar:'افتح «النتائج والإصلاحات» لمراجعة الملاحظات المدعومة والأدلة والتوصيات.'},{en:'Use Reports for completed assessments; discuss changes with your developer or request remediation assistance.',ar:'استخدم «التقارير» للفحوص المكتملة، وناقش التعديلات مع مطورك أو اطلب مساعدة الإصلاح.'},{en:'After approved changes are applied, run a separately authorized retest to verify improvement.',ar:'بعد تنفيذ التغييرات المعتمدة، ابدأ إعادة فحص بتصريح منفصل للتأكد من التحسن.'}],target:'Findings'}
];
const hosts:Record<Host,{label:Pair;method:Pair;tasks:Pair[];path?:string;methodId:'file'|'meta'|'dns';guideId:string}>={
 vercel:{label:{en:'Vercel / Next.js',ar:'Vercel / Next.js'},method:{en:'Verification file',ar:'ملف إثبات ملكية'},methodId:'file',guideId:'vercel',path:'public/.well-known/',
  tasks:[{en:'In AEGIS, choose Vercel and Get verification instructions; download the generated file.',ar:'في AEGIS اختار Vercel ثم «عرض خطوات التحقق» ونزّل الملف المُنشأ.'},{en:'In your website code repository, put the unchanged downloaded file inside public/.well-known/ (create .well-known if needed). Do not rename it.',ar:'في ملفات مشروع الموقع، ارفع الملف كما هو داخل public/.well-known/ (أنشئ مجلد .well-known لو مش موجود). ما تغيّرش الاسم.'},{en:'Commit and deploy the website. Confirm the exact .well-known URL shown in AEGIS opens publicly, then select Check ownership.',ar:'احفظ التعديل وانشر الموقع. تأكد أن رابط .well-known المحدد داخل AEGIS بيفتح للعامة، ثم اضغط «تحقق من الملكية».']}]},
 github:{label:{en:'GitHub Pages / Git',ar:'GitHub Pages / Git'},method:{en:'Verification file',ar:'ملف إثبات ملكية'},methodId:'file',guideId:'github',path:'.well-known/ (in the deployed public root)',
  tasks:[{en:'Download the file in AEGIS, or use Prepare file on GitHub inside the ownership guide.',ar:'نزّل ملف الإثبات من AEGIS، أو اختار «جهّز الملف على GitHub» داخل دليل الملكية.'},{en:'Place the unchanged proof under .well-known/ in the branch or public output that actually publishes your website.',ar:'ضع الملف كما هو داخل .well-known/ في الفرع أو ملفات النشر الفعلية لموقعك.'},{en:'Commit, wait for the published site, open the exact proof URL, then check ownership. Repository access alone is not proof.',ar:'احفظ وانشر، وافتح رابط الإثبات على الموقع الفعلي، ثم تحقق من الملكية. امتلاك المستودع وحده مش كفاية.'}]},
 wordpress:{label:{en:'WordPress',ar:'ووردبريس'},method:{en:'HTML meta tag',ar:'وسم HTML Meta'},methodId:'meta',guideId:'wordpress',
  tasks:[{en:'In AEGIS select WordPress, then Get verification instructions and copy the complete meta tag.',ar:'في AEGIS اختار WordPress ثم «عرض خطوات التحقق» وانسخ وسم Meta كاملًا.'},{en:'In the WordPress admin, use a trusted header/SEO plugin that adds custom tags inside the public homepage <head>. Paste the exact tag.',ar:'من لوحة WordPress استخدم إضافة موثوقة لإضافة كود رأس الصفحة داخل <head> للصفحة الرئيسية العامة، والصق الوسم كاملًا.'},{en:'Save, clear caches and verify the tag is present on the published homepage before pressing Check ownership.',ar:'احفظ وامسح الكاش، وتأكد إن الوسم ظهر في الصفحة المنشورة قبل الضغط على «تحقق من الملكية».']}]},
 shopify:{label:{en:'Shopify',ar:'شوبيفاي'},method:{en:'HTML meta tag (if permitted)',ar:'وسم Meta لو الصلاحيات تسمح'},methodId:'meta',guideId:'shopify',
  tasks:[{en:'In AEGIS choose the meta-tag method and copy the complete unique tag.',ar:'في AEGIS اختار طريقة Meta وانسخ الوسم الفريد كاملًا.'},{en:'In Shopify Online Store, edit the published theme only if you have permission, and add the tag in its HTML head.',ar:'في متجر Shopify، عدّل القالب المنشور فقط إذا عندك الصلاحية وضع الوسم داخل رأس HTML.'},{en:'Save and check the live storefront; otherwise use a domain DNS TXT proof if you control its DNS. Then verify in AEGIS.',ar:'احفظ وافتح المتجر العام للتأكد. ولو تعديل القالب غير متاح استخدم DNS TXT لو تتحكم في الدومين، ثم تحقق في AEGIS.'}]},
 cloudflare:{label:{en:'Cloudflare / DNS',ar:'Cloudflare / DNS'},method:{en:'DNS TXT record',ar:'سجل DNS TXT'},methodId:'dns',guideId:'cloudflare',
  tasks:[{en:'In AEGIS choose Cloudflare / DNS, generate the TXT challenge and copy the exact name and value.',ar:'في AEGIS اختار Cloudflare / DNS واعرض سجل TXT وانسخ الاسم والقيمة كما ظهرا.'},{en:'Open your domain in Cloudflare → DNS → Records → Add record → TXT. Paste the supplied host/name and content exactly.',ar:'افتح الدومين في Cloudflare ثم DNS ثم Records ثم Add record ثم TXT، والصق الاسم والمحتوى كما هما.'},{en:'Save, allow DNS propagation and select Check ownership in AEGIS. DNS verification does not approve a scan.',ar:'احفظ وانتظر انتشار DNS ثم اضغط «تحقق من الملكية» في AEGIS. التحقق من DNS لا يمنح إذن الفحص.'}]},
 cpanel:{label:{en:'cPanel / Plesk',ar:'cPanel / Plesk'},method:{en:'Verification file',ar:'ملف إثبات ملكية'},methodId:'file',guideId:'cpanel',path:'public_html/.well-known/ (or this domain’s configured document root)',
  tasks:[{en:'Download the exact generated proof file from the AEGIS ownership guide.',ar:'نزّل ملف الإثبات الذي أنشأته AEGIS من دليل إثبات الملكية.'},{en:'Open cPanel File Manager (or Plesk Files) for the target domain. In its public document root, create .well-known and upload the unchanged file.',ar:'افتح File Manager في cPanel أو Files في Plesk للدومين المطلوب. داخل مجلد الموقع العام أنشئ .well-known وارفع الملف كما هو.'},{en:'Open the exact public proof URL AEGIS provides, then press Check ownership. The document root may not be public_html for additional domains.',ar:'افتح رابط الإثبات العام الذي تعرضه AEGIS ثم اضغط «تحقق من الملكية». بعض الدومينات مجلدها العام مش public_html.'}]},
 netlify:{label:{en:'Netlify',ar:'Netlify'},method:{en:'Verification file',ar:'ملف إثبات ملكية'},methodId:'file',guideId:'netlify',path:'.well-known/ inside your site’s published output',
  tasks:[{en:'Generate and download the AEGIS proof file.',ar:'أنشئ ملف التحقق من AEGIS ونزّله.'},{en:'Put it unchanged under .well-known/ in the folder Netlify actually deploys (the public/build output).',ar:'ضعه دون أي تغيير داخل .well-known/ في المجلد الذي تنشره Netlify بالفعل (المجلد العام أو ناتج البناء).'} ,{en:'Deploy, test the public proof URL on the registered Netlify hostname and check ownership.',ar:'انشر الموقع، وافتح رابط الملف العام على نفس نطاق Netlify المسجل، ثم تحقق من الملكية.'}]},
 wix:{label:{en:'Wix / Squarespace',ar:'Wix / Squarespace'},method:{en:'DNS TXT on your own domain',ar:'DNS TXT على دومين تملكه'},methodId:'dns',guideId:'wix',
  tasks:[{en:'Select the DNS TXT method in AEGIS and generate its unique record.',ar:'اختار طريقة DNS TXT في AEGIS وأنشئ السجل الفريد.'},{en:'Open DNS management for your custom domain (either in your builder or DNS provider). Add the exact TXT name and value.',ar:'افتح إدارة DNS للدومين الخاص بك داخل منصة الموقع أو مزوّد DNS، وأضف الاسم والقيمة كما ظهرا.'},{en:'Wait for DNS propagation, then check ownership. Builder-owned subdomains may not allow custom DNS records; choose another supported method.',ar:'انتظر انتشار DNS ثم تحقق من الملكية. النطاقات الفرعية التابعة للمنصة قد لا تسمح بتعديل DNS؛ وقتها اختار طريقة أخرى مدعومة.'}]},
 other:{label:{en:'Other / not sure',ar:'أخرى / مش متأكد'},method:{en:'Choose file, meta or DNS',ar:'اختر ملف أو Meta أو DNS'},methodId:'dns',guideId:'unsure',
  tasks:[{en:'Find where your website is actually hosted and whether you control its public files, HTML head or domain DNS.',ar:'اعرف مكان استضافة موقعك وهل تقدر تتحكم في ملفاته العامة أو HTML head أو DNS.'},{en:'In My websites, open verification and choose the method your hosting supports. Never upload your proof to AEGIS itself.',ar:'في «مواقعي» افتح إثبات الملكية واختار الطريقة التي تدعمها الاستضافة. ما ترفعش الإثبات داخل AEGIS نفسها.'},{en:'Use the exact challenge shown for your public site. If you cannot publish proof, ask your hosting administrator, then check ownership.',ar:'استخدم الإثبات المحدد لموقعك المنشور. لو مش قادر تنشره اسأل مسؤول الاستضافة، ثم تحقق من الملكية.'}]}
};
export type GuidedAssistantProps={guest?:boolean;verified?:boolean;hasOrg?:boolean;assets?:number;verifiedAssets?:number;completed?:number;onNavigate?:(page:string)=>void;onAuthNavigate?:(mode:'register'|'login'|'verify')=>void};
export function suggestedGuideStep({guest=false,verified=false,hasOrg=false,assets=0,verifiedAssets=0,completed=0}:GuidedAssistantProps):number{
 if(guest)return 0;
 if(!verified)return 1;
 if(!hasOrg)return 2;
 if(!assets)return 3;
 if(!verifiedAssets)return 4;
 if(!completed)return 5;
 return 6;
}
export default function GuidedAssistant(props:GuidedAssistantProps){
 const {t,language}=useExperience();
 const id=useId();
 const [open,setOpen]=useState(false);
 const [step,setStep]=useState(()=>suggestedGuideStep(props));
 const [host,setHost]=useState<Host>('vercel');
 const recommended=suggestedGuideStep(props);
 useEffect(()=>{if(!open)setStep(recommended)},[recommended,open]);
 useEffect(()=>{
  if(!open)return;
  const onEscape=(event:KeyboardEvent)=>{if(event.key==='Escape')setOpen(false)};
  window.addEventListener('keydown',onEscape);
  return()=>window.removeEventListener('keydown',onEscape);
 },[open]);
 const item=steps[step],current=hosts[host];
 const L=(pair:Pair)=>pair[language];
 const goto=()=>{
  if(props.guest){
   props.onAuthNavigate?.(step===1?'verify':'register');
   setOpen(false);
   return;
  }
  if(!props.verified){setStep(1);return}
  if(!props.hasOrg){setStep(2);setOpen(false);return}
  if(item.target){props.onNavigate?.(item.target);setOpen(false);return}
  props.onNavigate?.('Overview');setOpen(false);
 };
 return <div className="aegis-guide-root" dir={language==='ar'?'rtl':'ltr'}>
  {!open&&<button type="button" className="aegis-guide-launch" aria-expanded={false} aria-controls={id} onClick={()=>{setStep(recommended);setOpen(true)}}><span className="aegis-guide-launch-icon"><Sparkles size={19}/></span><span>{t('Guide me step by step','ساعدني خطوة بخطوة')}</span><ChevronRight size={16} aria-hidden="true"/></button>}
  {open&&<section className="aegis-guide-panel" id={id} aria-label={t('AEGIS Guided Assistant','مساعد AEGIS التفاعلي')}>
   <header className="aegis-guide-header"><div className="aegis-guide-identity"><span className="aegis-guide-icon"><ShieldCheck size={21}/></span><div><strong>{t('AEGIS Guided Assistant','مساعد AEGIS التفاعلي')}</strong><small>{t('Your setup, explained clearly','دليلك في كل خطوة')}</small></div></div><button type="button" className="aegis-guide-close" aria-label={t('Close assistant','إغلاق المساعد')} onClick={()=>setOpen(false)}><X size={19}/></button></header>
   <div className="aegis-guide-body">
    <div className="aegis-guide-intro"><span><Sparkles size={14}/>{t('PRACTICAL WALKTHROUGH','شرح تفاعلي عملي')}</span><p>{t('I will show you the next steps. Nothing is changed or scanned automatically.','هشرح لك الخطوات الجاية. مش هنعدل موقعك أو نبدأ فحص بشكل تلقائي.')}</p></div>
    <div className="aegis-guide-progress-head"><span>{t('Step','خطوة')} {step+1} / {steps.length}</span>{step===recommended&&<span className="aegis-guide-recommended"><CheckCircle2 size={13}/>{t('Suggested now','المقترحة الآن')}</span>}</div>
    <div className="aegis-guide-progress" role="progressbar" aria-label={t('Walkthrough progress','تقدم الشرح')} aria-valuemin={0} aria-valuemax={steps.length} aria-valuenow={step+1}><span style={{width:((step+1)/steps.length*100)+'%'}}/></div>
    <div className="aegis-guide-step-pills" role="group" aria-label={t('Choose a step','اختر خطوة')}>
     {steps.map((s,i)=><button type="button" className={step===i?'selected':''} key={s.title.en} aria-label={L(s.title)} aria-pressed={step===i} onClick={()=>setStep(i)}>{i+1}</button>)}
    </div>
    <section className="aegis-guide-current" aria-live="polite">
     <p className="aegis-guide-kicker">{t('HERE IS WHAT TO DO','اعمل إيه دلوقتي؟')}</p>
     <h2>{L(item.title)}</h2><p>{L(item.explain)}</p>
     <ol className="aegis-guide-instructions">{item.tasks.map((task,i)=><li key={task.en}><span>{String(i+1).padStart(2,'0')}</span><p>{L(task)}</p></li>)}</ol>
    </section>
    {step===4&&<section className="aegis-guide-host-section" aria-label={t('Choose your website platform','اختر منصة موقعك')}>
     <label>{t('Where is your website hosted?','موقعك على أي منصة؟')}
      <select aria-label={t('Website hosting platform','منصة استضافة الموقع')} value={host} onChange={e=>setHost(e.target.value as Host)}>{(Object.keys(hosts) as Host[]).map(key=><option key={key} value={key}>{L(hosts[key].label)}</option>)}</select>
     </label>
     <div className="aegis-guide-method"><Globe2 size={18}/><div><strong>{L(current.method)}</strong><small>{t('Recommended for the selected platform','طريقة مناسبة للمنصة المختارة')}</small></div></div>
     {current.path&&<div className="aegis-guide-path"><span>{t('Put the proof file here, in YOUR website files:','ارفع ملف الإثبات هنا داخل ملفات موقعك:')}</span><code dir="ltr">{current.path}</code></div>}
     <ol className="aegis-guide-host-steps">{current.tasks.map((task,i)=><li key={i}><span>{i+1}</span>{L(task)}</li>)}</ol>
     <div className="aegis-guide-exact"><LockKeyhole size={15}/>{t('Download the real token or file from your selected website inside AEGIS. This guide never creates tokens, uploads files or verifies ownership for you.','نزّل الرمز أو الملف الحقيقي من الموقع المحدد داخل AEGIS. الدليل لا ينشئ رموزًا ولا يرفع ملفات ولا يثبت الملكية نيابة عنك.')}</div>
     <Link href={'/guides?platform='+encodeURIComponent(current.guideId)+'&method='+current.methodId} className="aegis-guide-link" target="_blank" rel="noopener noreferrer"><BookOpen size={17}/>{t('Watch platform tutorial','شاهد شرح المنصة')}<ExternalLink size={14}/></Link>
    </section>}
    <div className="aegis-guide-navigation">
     <button type="button" disabled={step===0} onClick={()=>setStep(v=>Math.max(v-1,0))}><ArrowLeft size={16}/>{t('Back','السابق')}</button>
     <button type="button" disabled={step===steps.length-1} onClick={()=>setStep(v=>Math.min(v+1,steps.length-1))}>{t('Next','التالي')}<ArrowRight size={16}/></button>
    </div>
    <button type="button" className="aegis-guide-action" onClick={goto}>{props.guest?t(step===1?'Open email verification':'Open registration',step===1?'افتح تفعيل البريد':'افتح التسجيل'):!props.verified?t('Verify your email first','فعّل بريدك أولًا'):!props.hasOrg?t('Create your workspace first','أنشئ مساحة العمل أولًا'):step>=3?t('Open the relevant workspace screen','افتح الشاشة المطلوبة في المنصة'):t('Continue in your workspace','متابعة في مساحة العمل')}<ChevronRight size={17}/></button>
    <footer className="aegis-guide-footer"><span><CircleHelp size={15}/>{t('Still need help?','لسه محتاج مساعدة؟')}</span><Link href="/contact"><Mail size={15}/>{t('Contact AEGIS','تواصل مع AEGIS')}</Link></footer>
   </div>
  </section>}
 </div>;
}
