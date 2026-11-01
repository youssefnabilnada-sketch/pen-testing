'use client';
import Link from 'next/link';
import PlatformExplainer from './PlatformExplainer';
import {useEffect,useState} from 'react';
import {
 ArrowUpRight,ArrowRight,ShieldCheck,Target,Eye,ScanLine,
 FileCheck2,Wrench,RefreshCw,LockKeyhole,BookOpen,CheckCircle2,Workflow
} from 'lucide-react';

type Language='en'|'ar';
type Localized={en:string;ar:string};
const values:{title:Localized;body:Localized;icon:typeof ShieldCheck}[]=[
 {icon:LockKeyhole,title:{en:'Permission before assessment',ar:'التصريح قبل الفحص'},
  body:{en:'Website ownership and a defined scope come first. AEGIS does not run assessments on arbitrary third-party sites.',ar:'إثبات ملكية الموقع وتحديد نطاق الفحص أولًا. لا تجري AEGIS فحوصات على مواقع الغير دون تصريح.'}},
 {icon:Eye,title:{en:'Evidence before claims',ar:'الأدلة قبل الادعاءات'},
  body:{en:'Findings are explained in the context of observed configuration and the limits of each check.',ar:'نشرح النتائج حسب الإعدادات التي تم رصدها فعليًا، مع توضيح حدود كل اختبار.'}},
 {icon:Wrench,title:{en:'Approval before changes',ar:'الموافقة قبل التعديل'},
  body:{en:'Remediation proposals and repository-assisted changes require review and approval; AEGIS never silently edits your live website.',ar:'مقترحات الإصلاح وتعديلات المستودعات البرمجية تحتاج إلى مراجعة وموافقة، ولا تعدل AEGIS موقعك المنشور دون علمك.'}},
 {icon:RefreshCw,title:{en:'Verification after action',ar:'التحقق بعد الإصلاح'},
  body:{en:'A proposed change is not a proven fix. Supported checks can be repeated to compare the evidence after implementation.',ar:'اقتراح التعديل لا يعني نجاح الإصلاح. يمكن إعادة الفحوصات المدعومة للمقارنة والتحقق بعد التنفيذ.'}},
];
const steps:{n:string;title:Localized;body:Localized;icon:typeof ShieldCheck}[]=[
 {n:'01',icon:ShieldCheck,title:{en:'Add and verify',ar:'أضف موقعك وأثبت الملكية'},body:{en:'Create your workspace, add an owned website, and complete the available DNS, file or meta-tag ownership challenge.',ar:'أنشئ مساحة العمل، وأضف موقعًا تملكه، ثم أكمل التحقق عبر DNS أو ملف HTML أو وسم Meta.'}},
 {n:'02',icon:LockKeyhole,title:{en:'Authorize a clear scope',ar:'حدد نطاق الفحص ووافق عليه'},body:{en:'Choose the permitted asset and assessment limits before any automated check starts.',ar:'حدد الموقع المسموح بفحصه وحدود التقييم قبل تشغيل أي اختبار آلي.'}},
 {n:'03',icon:ScanLine,title:{en:'Run bounded checks',ar:'شغّل الفحوصات الآمنة'},body:{en:'Review supported response-level checks, including TLS configuration, headers, cookies and CSP signals.',ar:'افحص الإعدادات المدعومة مثل TLS وترويسات الاستجابة وخصائص ملفات تعريف الارتباط وإشارات CSP.'}},
 {n:'04',icon:FileCheck2,title:{en:'Understand the findings',ar:'افهم النتائج والتقارير'},body:{en:'Read evidence-based explanations, suggested priorities and reports that make clear what was—and was not—tested.',ar:'اطلع على شرح النتائج المبني على الأدلة والأولويات المقترحة والتقارير التي توضح ما اختُبر وما لم يُختبر.'}},
 {n:'05',icon:RefreshCw,title:{en:'Review, improve, retest',ar:'راجع ثم أصلح وأعد الفحص'},body:{en:'Request remediation guidance, review changes and quotations separately, approve any applicable work, then retest.',ar:'اطلب إرشادات الإصلاح، وراجع التعديلات وعروض الأسعار بصورة منفصلة، ووافق على العمل المناسب ثم أعد الفحص.'}},
];
export default function AboutExperience(){
 const [language,setLanguage]=useState<Language>('en');
 useEffect(()=>{try{if(localStorage.getItem('aegis-language')==='ar')setLanguage('ar')}catch{}},[]);
 const t=(en:string,ar:string)=>language==='ar'?ar:en;
 const tr=(x:Localized)=>x[language];
 const toggle=()=>{const next=language==='en'?'ar':'en';setLanguage(next);try{localStorage.setItem('aegis-language',next)}catch{}};
 return <main className="landing about-landing" dir={language==='ar'?'rtl':'ltr'} lang={language}>
  <a href="#about-main" className="about-skip">{t('Skip to main content','انتقل إلى المحتوى')}</a>
  <nav className="landing-nav about-nav" aria-label={t('AEGIS platform navigation','قائمة منصة AEGIS')}>
   <Link className="brand" href="/"><ShieldCheck size={22}/> AEGIS <small>SECURITY CLOUD</small></Link>
   <div className="about-nav-links"><a href="#what-it-does">{t('What it does','ماذا تقدم؟')}</a><a href="#how-it-works">{t('How it works','كيف تعمل؟')}</a><a href="#mission">{t('Mission & vision','الرسالة والرؤية')}</a><Link href="/trust">{t('Trust','الأمان')}</Link><Link href="/contact">{t('Contact','تواصل معنا')}</Link></div>
   <div className="about-nav-actions"><button type="button" className="about-language" onClick={toggle} aria-label={language==='en'?'التبديل إلى العربية':'Switch to English'}>{language==='en'?'العربية':'English'}</button><Link className="button ghost" href="/console">{t('Open workspace','دخول المنصة')} <ArrowUpRight size={16}/></Link></div>
  </nav>
  <div id="about-main">
   <section className="about-hero">
    <div className="about-hero-copy">
     <p className="eyebrow"><span className="dot"/>{t('AEGIS SECURITY CLOUD — THE PLATFORM EXPLAINED','AEGIS SECURITY CLOUD — دليل المنصة')}</p>
     <h1>{t('What AEGIS does.','ماذا تفعل AEGIS؟')}<span>{t('How you stay in control.','وكيف تظل أنت المتحكم.')}</span></h1>
     <p className="lead">{t('Explore how AEGIS helps you add and verify your website, authorize a safe assessment, understand findings, plan fixes and validate progress — without giving up control.', 'اكتشف كيف تساعدك AEGIS على إضافة موقعك وإثبات ملكيته، والسماح بفحص آمن، وفهم النتائج، وتخطيط الإصلاحات، والتحقق من التحسن — وأنت المتحكم في كل خطوة.')}</p>
     <div className="actions"><Link href="/console" className="button primary">{t('Explore your workspace','ابدأ من مساحة العمل')} <ArrowUpRight size={17}/></Link><a href="#what-it-does" className="button ghost">{t('Explore every feature','اكتشف كل إمكانيات المنصة')} <ArrowRight size={17}/></a></div>
     <p className="about-hero-caveat"><LockKeyhole size={15}/>{t('Authorized, bounded configuration checks—not a promise that any website is vulnerability-free.', 'فحوصات إعدادات محدودة ومصرح بها، وليست ضمانًا لخلو أي موقع من الثغرات.')}</p>
    </div>
    <div className="about-hero-visual" aria-hidden="true"><div className="about-visual-orbit"><ShieldCheck size={110} strokeWidth={1.15}/></div><div className="about-visual-note"><CheckCircle2 size={16}/>{t('Verify • Assess • Improve','تحقق • افحص • حسّن')}</div><div className="about-visual-caption">{t('SECURITY WITH PERMISSION & PROOF','أمان مبني على التصريح والدليل')}</div></div>
   </section>
   <section className="section about-intro" id="story">
    <p className="eyebrow">{t('WHAT WE BELIEVE','ما نؤمن به')}</p>
    <h2>{t('Security should be understandable, not intimidating.','الأمان لازم يكون واضحًا، مش معقدًا.')}</h2>
    <p>{t('Website owners often receive technical findings without knowing what they mean or what to do next. AEGIS is designed to make that journey clearer: confirm ownership, inspect what is in scope, explain the evidence, and support responsible follow-through.', 'أصحاب المواقع ممكن يحصلوا على نتائج تقنية من غير ما يعرفوا معناها أو الخطوة التالية. AEGIS مصممة لتسهيل الرحلة: إثبات الملكية، وفحص ما يقع داخل النطاق المصرح به، وشرح الأدلة، ومتابعة التحسين بشكل مسؤول.')}</p>
   </section>
   <section className="section about-purpose" id="mission" aria-labelledby="about-purpose-title">
    <p className="eyebrow">{t('OUR PURPOSE','هدفنا')}</p>
    <h2 id="about-purpose-title">{t('A mission with a direction.','رسالة واضحة ورؤية للمستقبل.')}</h2>
    <div className="about-purpose-grid">
     <article className="glass about-purpose-card"><div className="about-card-heading"><Target size={26}/><span>01 / {t('OUR MISSION','رسالتنا')}</span></div><h3>{t('Make security easier to act on.','نحوّل فهم الأمان إلى خطوات عملية.')}</h3><p>{t('Our mission is to help website owners and teams improve their security posture through permission-based assessments, evidence-led guidance, and remediation that stays under human control.', 'رسالتنا هي مساعدة أصحاب المواقع والفرق على تحسين مستوى الأمان من خلال فحوصات مصرح بها، وإرشادات مبنية على الأدلة، وإصلاحات تظل تحت مراجعة وموافقة البشر.')}</p></article>
     <article className="glass about-purpose-card"><div className="about-card-heading"><Eye size={26}/><span>02 / {t('OUR VISION','رؤيتنا')}</span></div><h3>{t('A clearer, more responsible digital future.','مستقبل رقمي أوضح وأكثر مسؤولية.')}</h3><p>{t('We envision a future where every website owner can understand meaningful risks, prioritize improvements, and measure progress over time—without giving up control of their systems.', 'نتطلع إلى مستقبل يستطيع فيه كل صاحب موقع فهم المخاطر المهمة، وتحديد أولويات التحسين، وقياس التقدم مع الوقت، مع الاحتفاظ بالتحكم الكامل في أنظمته.')}</p></article>
    </div>
   </section>
   <section className="section about-values" id="principles">
    <p className="eyebrow">{t('OUR PRINCIPLES','مبادئنا')}</p>
    <h2>{t('Built around trust, not shortcuts.','ثقة ومسؤولية، مش وعود سريعة.')}</h2>
    <div className="about-values-grid">{values.map(item=>{const Icon=item.icon;return <article className="about-value" key={item.title.en}><Icon size={24} aria-hidden="true"/><h3>{tr(item.title)}</h3><p>{tr(item.body)}</p></article>})}</div>
   </section>
   <section className="section about-process glass" id="how-it-works">
    <div className="about-process-heading"><div><p className="eyebrow">{t('THE CUSTOMER JOURNEY','رحلة العميل')}</p><h2>{t('From your first website to your next retest.','من إضافة الموقع إلى إعادة الفحص.')}</h2></div><p>{t('Each stage is visible, intentional, and built around your approval.', 'كل مرحلة واضحة ومقصودة، وتخضع للحدود والموافقات المناسبة.')}</p></div>
    <ol className="about-step-list">{steps.map(step=>{const Icon=step.icon;return <li key={step.n}><span className="about-step-no">{step.n}</span><Icon size={21} aria-hidden="true"/><div><h3>{tr(step.title)}</h3><p>{tr(step.body)}</p></div></li>})}</ol>
    <Link href="/guides" className="about-text-link"><BookOpen size={17}/>{t('Watch website ownership tutorials','شاهد فيديوهات إثبات ملكية الموقع')}<ArrowUpRight size={15}/></Link>
   </section>
   <section className="section about-capabilities" id="capabilities">
    <p className="eyebrow">{t('WHAT AEGIS SUPPORTS','ماذا تقدم AEGIS؟')}</p>
    <h2>{t('One workspace. A practical security journey.','مساحة عمل واحدة لرحلة أمان منظمة.')}</h2>
    <div className="about-capabilities-grid">
     <article className="glass"><ScanLine size={24}/><h3>{t('Authorized security assessment','فحص أمني مصرح به')}</h3><p>{t('Non-destructive checks for selected website and supported API response configurations within your approved scope.', 'فحوصات غير تخريبية لإعدادات استجابة المواقع وبعض واجهات API المدعومة داخل النطاق الذي وافقت عليه.')}</p></article>
     <article className="glass"><FileCheck2 size={24}/><h3>{t('Clear findings and reports','نتائج وتقارير مفهومة')}</h3><p>{t('Findings are paired with readable explanations and evidence. Optional AI assistance depends on configuration and availability.', 'نتائج مصحوبة بشرح مبسط وأدلة فعلية. دعم الذكاء الاصطناعي الإضافي يتوقف على الإعداد والتوافر.')}</p></article>
     <article className="glass"><Workflow size={24}/><h3>{t('Guided remediation & FastFix','إرشاد الإصلاح وFastFix')}</h3><p>{t('Review guidance and applicable change proposals. FastFix support varies by finding and integration; it does not automatically repair every vulnerability.', 'راجع إرشادات الإصلاح ومقترحات التعديل الممكنة. دعم FastFix يختلف حسب المشكلة والتكامل، ولا يصلح كل الثغرات تلقائيًا.')}</p></article>
     <article className="glass"><RefreshCw size={24}/><h3>{t('Follow-up and retesting','المتابعة وإعادة الفحص')}</h3><p>{t('Track remediation requests and repeat supported checks to compare evidence after an approved change.', 'تابع طلبات الإصلاح وأعد الاختبارات المدعومة للمقارنة بين الأدلة بعد إجراء التغييرات المعتمدة.')}</p></article>
    </div>
   </section>
   <PlatformExplainer language={language} t={t}/>
   <section className="about-disclaimer" aria-label={t('Assessment limitations','حدود التقييم')}>
    <ShieldCheck size={24}/><div><h3>{t('What AEGIS does not promise','ما الذي لا تعدك به AEGIS؟')}</h3><p>{t('An automated configuration assessment is not a comprehensive penetration test. No scan can prove a website is completely secure. AEGIS does not alter production code automatically, and a proposed fix is not considered verified until it is applied and retested.', 'تقييم الإعدادات الآلي ليس اختبار اختراق شاملًا. ولا يمكن لأي فحص إثبات أن الموقع آمن تمامًا. لا تعدل AEGIS كود الإنتاج تلقائيًا، ولا يعتبر الإصلاح ناجحًا لمجرد اقتراحه، بل بعد تطبيقه وإعادة التحقق.')}</p></div>
   </section>
   <section className="about-final-cta">
    <div><p className="eyebrow">{t('READY TO TAKE THE FIRST STEP?','مستعد تبدأ؟')}</p><h2>{t('Start with visibility. Improve with confidence.','ابدأ بالرؤية الواضحة، وطوّر بثقة.')}</h2><p>{t('Create an account, verify a website you control, and explore the supported assessment workflow. No payment is required in the current launch version.', 'أنشئ حسابك، وأثبت ملكية موقع تديره، وابدأ استكشاف رحلة الفحص المتاحة. لا يُطلب دفع أي رسوم في نسخة الإطلاق الحالية.')}</p></div>
    <Link className="button primary" href="/console">{t('Create your workspace','أنشئ مساحة العمل')}<ArrowUpRight size={19}/></Link>
   </section>
  </div>
  <footer className="about-footer"><Link className="brand" href="/"><ShieldCheck/> AEGIS</Link><p>{t('Understand. Authorize. Improve.','افهم. صرّح. حسّن.')}</p><div><Link href="/trust">{t('Trust Center','مركز الثقة')}</Link><Link href="/guides">{t('Verification guides','إرشادات التحقق')}</Link><Link href="/contact">{t('Contact us','تواصل معنا')}</Link><Link href="/">{t('Home','الرئيسية')}</Link></div></footer>
 </main>;
}
