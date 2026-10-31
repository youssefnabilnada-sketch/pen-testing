'use client';
import {useState} from 'react';
import {useExperience} from './Experience';
import {
 Activity,BarChart3,BookOpen,ChevronDown,CircleHelp,FileText,Globe2,
 LayoutDashboard,LockKeyhole,ScanLine,Settings2,ShieldCheck,
 Sparkles,Users,Wrench
} from 'lucide-react';

const primary=[
 ['Overview','Overview',LayoutDashboard],
 ['Assets','My websites',Globe2],
 ['Assessments','Security assessments',ScanLine],
 ['Findings','Findings & fixes',ShieldCheck],
 ['Reports','Reports',FileText],
] as const;
const operations=[
 ['Remediation','Remediation',Wrench],
 ['Website Health','Monitoring',Activity],
] as const;
const advanced=[
 ['Threat Intelligence','Threat intelligence',Sparkles],
 ['API Assessment','API assessments',ScanLine],
 ['Launch Guard','Launch Guard',ShieldCheck],
 ['Evidence Vault','Evidence vault',LockKeyhole],
 ['Agency','Agency workspace',Globe2],
 ['Onboarding','Customer onboarding',BookOpen],
 ['Team','Team',Users],
 ['Support','Support',CircleHelp],
 ['Account security','Account security',Settings2],
] as const;
const arabic:Record<string,string>={
 Overview:'نظرة عامة',Assets:'مواقعي',Assessments:'الفحوص الأمنية',Findings:'النتائج والإصلاحات',
 Remediation:'طلبات الإصلاح','Website Health':'المراقبة',Reports:'التقارير',
 'Threat Intelligence':'المعلومات الأمنية','API Assessment':'فحص API','Launch Guard':'مراجعة الإطلاق',
 'Evidence Vault':'خزنة الأدلة',Agency:'مساحة الوكالة',Onboarding:'تهيئة العملاء',Team:'الفريق',
 Support:'الدعم','Account security':'أمان الحساب',Administration:'الإدارة'
};

export default function WorkspaceNavigation({page,onNavigate,superadmin=false}:{page:string;onNavigate:(page:string)=>void;superadmin?:boolean}){
 const {t}=useExperience();
 const isToolsActive=advanced.some(([id])=>id===page)||page==='Administration';
 const [expanded,setExpanded]=useState(isToolsActive);
 const item=([id,label,Icon]:readonly [string,string,typeof LayoutDashboard])=><button
  key={id}
  type="button"
  aria-current={page===id?'page':undefined}
  className={'workspace-nav-item'+(page===id?' active':'')}
  onClick={()=>onNavigate(id)}
 ><Icon size={18} strokeWidth={1.8} aria-hidden="true"/><span>{t(label,arabic[id]||label)}</span>{page===id&&<span className="workspace-nav-current" aria-hidden="true"/>}</button>;
 return <nav aria-label="Workspace navigation" className="workspace-nav">
  <div className="workspace-nav-group">
   <p className="workspace-nav-caption">{t('WORKSPACE','مساحة العمل')}</p>
   <div className="nav-primary">{primary.map(item)}</div>
  </div>
  <div className="workspace-nav-group">
   <p className="workspace-nav-caption">{t('OPERATIONS','العمليات')}</p>
   <div className="nav-operations">{operations.map(item)}</div>
  </div>
  <div className="workspace-nav-group workspace-nav-group-last">
   <button type="button" className={'workspace-tools-toggle'+(expanded?' expanded':'')}
     aria-expanded={expanded||isToolsActive} aria-controls="workspace-tools"
     onClick={()=>setExpanded(v=>!v)}>
     <Settings2 size={18} aria-hidden="true"/><span>{t('Tools & settings','الأدوات والإعدادات')}</span>
     <ChevronDown size={16} aria-hidden="true"/>
   </button>
   <div id="workspace-tools" hidden={!(expanded||isToolsActive)} className="nav-tools">
    {advanced.map(item)}
    {superadmin&&item(['Administration','Administration',BarChart3])}
   </div>
  </div>
 </nav>;
}

export function GettingStarted({assets,verified,completed,onNavigate}:{assets:number;verified:number;completed:number;onNavigate:(page:string)=>void}){
 const {t}=useExperience();
 const step=assets===0?0:verified===0?1:completed===0?2:3;
 const labels=[t('Add your website','أضف موقعك'),t('Verify ownership','أثبت ملكية الموقع'),t('Approve & assess','وافق وابدأ الفحص'),t('Review your results','راجع النتائج')];
 const descriptions=[
  t('Start with a website you control. Every assessment starts with an asset you own.','ابدأ بموقع تتحكم فيه. كل فحص يبدأ بموقع تملكه.'),
  t('Follow an easy verification method. Nothing is assessed before your ownership is confirmed.','اتبع طريقة تحقق بسيطة. لن يبدأ أي فحص قبل التأكد من ملكيتك.'),
  t('Review the exact scope and approve a non-destructive assessment before it begins.','راجع النطاق المحدد ووافق على فحص غير تدميري قبل بدء التنفيذ.'),
  t('Review real evidence, plan approved improvements, and validate with a retest.','راجع الأدلة الفعلية وخطط للإصلاحات المعتمدة ثم أعد الفحص للتحقق.')
 ];
 return <section className="glass panel journey premium-journey" aria-label={t('Your next step','خطوتك التالية')}>
  <div className="premium-journey-layout">
   <div className="premium-journey-copy">
    <div className="premium-journey-kicker"><span className="premium-pulse"/>{t('YOUR GUIDED SETUP','رحلتك خطوة بخطوة')}<span>{String(step+1).padStart(2,'0')} / 04</span></div>
    <h2>{labels[step]}</h2>
    <p>{descriptions[step]}</p>
    <button className="primary premium-journey-action" onClick={()=>onNavigate(step===3?'Findings':'Assets')}>{labels[step]} →</button>
    <small><ShieldCheck size={15} aria-hidden="true"/>{t('Ownership verification and assessment permission are always separate.','إثبات الملكية والإذن بالفحص خطوتان منفصلتان دائمًا.')}</small>
   </div>
   <ol className="premium-journey-steps">
    {labels.map((label,i)=><li key={label} aria-current={i===step?'step':undefined} className={i<step?'completed-step':''}>
      <span>{i<step?'✓':String(i+1).padStart(2,'0')}</span>
      <div><strong>{label}</strong><small>{i<step?t('Completed','مكتمل'):i===step?t('Up next','الخطوة الحالية'):t('Next','لاحقًا')}</small></div>
    </li>)}
   </ol>
  </div>
 </section>;
}
