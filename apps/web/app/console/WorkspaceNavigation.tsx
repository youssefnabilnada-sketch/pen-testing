'use client';
import {useExperience} from './Experience';
import {useState} from 'react';
const primary=[['Overview','Overview'],['Assets','My websites'],['Assessments','Security assessments'],['Findings','Findings & fixes'],['Remediation','Remediation'],['Website Health','Monitoring'],['Reports','Reports']];
const advanced=[['Threat Intelligence','Threat intelligence'],['API Assessment','API assessments'],['Launch Guard','Launch Guard'],['Evidence Vault','Evidence vault'],['Agency','Agency workspace'],['Onboarding','Customer onboarding'],['Team','Team'],['Support','Support'],['Account security','Account security']];
export default function WorkspaceNavigation({page,onNavigate,superadmin=false}:{page:string;onNavigate:(page:string)=>void;superadmin?:boolean}){
 const {t}=useExperience();
 const arabic:Record<string,string>={Overview:'نظرة عامة',Assets:'مواقعي',Assessments:'الفحوص الأمنية',Findings:'النتائج والإصلاحات',Remediation:'طلبات الإصلاح','Website Health':'المراقبة',Reports:'التقارير','Threat Intelligence':'المعلومات الأمنية','API Assessment':'فحص API','Launch Guard':'مراجعة الإطلاق','Evidence Vault':'خزنة الأدلة',Agency:'مساحة الوكالة',Onboarding:'تهيئة العملاء',Team:'الفريق',Support:'الدعم','Account security':'أمان الحساب',Administration:'الإدارة'};
 const [expanded,setExpanded]=useState(false);
 const button=([id,label]:string[])=><button key={id} aria-current={page===id?'page':undefined} className={page===id?'active':''} onClick={()=>onNavigate(id)}>{t(label,arabic[id]||label)}</button>;
 return <nav aria-label="Workspace navigation"><div className="nav-primary">{primary.map(button)}</div><button aria-expanded={expanded} aria-controls="workspace-tools" onClick={()=>setExpanded(!expanded)}>{t('Tools & settings','الأدوات والإعدادات')} {expanded?'−':'+'}</button><div id="workspace-tools" hidden={!expanded} className="nav-tools">{advanced.map(button)}{superadmin&&button(['Administration','Administration'])}</div></nav>;
}
export function GettingStarted({assets,verified,completed,onNavigate}:{assets:number;verified:number;completed:number;onNavigate:(page:string)=>void}){
 const step=assets===0?0:verified===0?1:completed===0?2:3;
 const labels=['Add your website','Verify ownership','Approve & assess','Review your results'];
 return <section className="glass panel journey" aria-label="Your next step"><p className="eyebrow">YOUR NEXT STEP</p><h2>{labels[step]}</h2><p>{['Start with the address of a website you control.','Choose a verification method, follow the instructions, then check ownership.','Review the exact scope and give permission before starting a read-only assessment.','Review the evidence, request help with fixes, and retest after approved changes.'][step]}</p><ol>{labels.map((label,i)=><li key={label} aria-current={i===step?'step':undefined}><span>{i+1}</span>{label}</li>)}</ol><button className="primary" onClick={()=>onNavigate(step===3?'Findings':'Assets')}>{labels[step]} →</button><small>Verification is separate from permission to assess or change your website.</small></section>;
}
