'use client';
import {useEffect,useState} from 'react';
import {useExperience} from './Experience';
import VerificationRetry from './VerificationRetry';
import SmartVerifyPlatformGuide from './SmartVerifyPlatformGuide';
import {Github,Globe2,Cloud,FileCheck2,Server,HelpCircle,CheckCircle2,ExternalLink,ShieldCheck} from 'lucide-react';
type Challenge={id:string;method:string;token:string;instruction:string;expires:number;wordpress?:{origin:string;token:string;expires:number}};
function githubRepository(value:string){
 const trimmed=value.trim();
 if(!trimmed.startsWith('https://github.com/'))return trimmed.replace(/\.git$/i,'');
 try{
  const url=new URL(trimmed);
  if(url.hostname!=='github.com'||url.username||url.password)return trimmed;
  return url.pathname.split('/').filter(Boolean).slice(0,2).join('/').replace(/\.git$/i,'');
 }catch{return trimmed}
}
export default function OwnershipGuide({assetId,api,onVerified}:{assetId:string;api:(p:string,m?:string,d?:unknown)=>Promise<any>;onVerified:()=>Promise<void>}){
 const {t}=useExperience();
 const [autoChecking,setAutoChecking]=useState(false);
 const [host,setHost]=useState('unsure'),[branch,setBranch]=useState('main');
 const [history,setHistory]=useState<any[]>([]);
 const [c,setC]=useState<Challenge|null>(null),[method,setMethod]=useState('dns'),[repository,setRepository]=useState(''),[directory,setDirectory]=useState(''),[link,setLink]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [cfZone,setCfZone]=useState(''),[cfToken,setCfToken]=useState(''),[cfApproved,setCfApproved]=useState(false),[cfMfa,setCfMfa]=useState(''),[cfPreview,setCfPreview]=useState<{name:string;content:string;ttl:number}|null>(null);
 useEffect(()=>{setCfToken('');setCfZone('');setCfApproved(false);setCfMfa('');setCfPreview(null);let active=true;api(`/assets/${assetId}/challenge`).then(v=>{if(active){setC(v);if(v)setMethod(v.method)}}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[assetId,api]);
 function chooseHost(id:string,choice:string){
  if(busy||autoChecking)return;
  setHost(id);setMethod(choice);if(c?.method!==choice)setC(null);
  setLink('');setCfPreview(null);setCfToken('');setDirectory(id==='vercel'?'public':'');
  setError('');setNotice('');
 }
 async function act(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <section aria-label="Ownership guide" className="ownership-wizard">
 <div className="ownership-welcome">
  <span className="ownership-eyebrow"><ShieldCheck size={17}/>{t('STEP 2 · OWNERSHIP VERIFICATION','الخطوة ٢ · إثبات الملكية')}</span>
  <h3>{t('Verify your website, without the complexity.','أثبت ملكية موقعك بدون تعقيد.')}</h3>
  <p>{t('Where do you manage your website? Pick one option — we’ll show the simplest safe path.','موقعك على أي منصة؟ اختار واحدة وهنعرض لك أسهل طريقة آمنة.')}</p>
 </div>
 {error&&<p role="alert" className="error">{error}</p>}
 {notice&&<p role="status" className="notice">{notice}</p>}
 <div className="ownership-hosts" role="group" aria-label={t('Where is your website managed?','موقعك على أي منصة؟')}>
 {([
  ['github','GitHub / GitHub Pages','GitHub / GitHub Pages',Github,'file'],
  ['vercel','Vercel + GitHub','Vercel + GitHub',Globe2,'file'],
  ['wordpress','WordPress','ووردبريس',FileCheck2,'meta'],
  ['cloudflare','Cloudflare / DNS','كلاودفلير / DNS',Cloud,'dns'],
  ['cpanel','cPanel / Plesk','سي بانل / بليسك',Server,'file'],
  ['netlify','Netlify','نتليفاي',Globe2,'file'],
  ['shopify','Shopify','شوبيفاي',Cloud,'meta'],
  ['unsure','Other / not sure','أخرى / مش متأكد',HelpCircle,'dns']
 ] as const).map(([id,en,ar,Icon,choice])=><button key={id} type="button" disabled={busy||autoChecking}
  aria-pressed={host===id} className={'ownership-host'+(host===id?' selected':'')}
  onClick={()=>chooseHost(id,choice)}>
  <Icon size={22} aria-hidden="true"/><span>{t(en,ar)}</span>{host===id&&<CheckCircle2 size={16} aria-hidden="true"/>}
 </button>)}
 </div>
 <details className="ownership-other-platforms">
  <summary>{t('More options: Wix, Squarespace and Google Search Console','منصات أخرى: Wix وSquarespace وGoogle Search Console')}</summary>
  <div className="ownership-hosts" role="group" aria-label={t('Additional website platforms','منصات مواقع إضافية')}>
   {([
    ['wix','Wix','ويكس',Cloud,'dns'],
    ['squarespace','Squarespace','سكوير سبيس',Globe2,'dns'],
    ['google','Google Search Console','جوجل سيرش كونسول',Globe2,'dns']
   ] as const).map(([id,en,ar,Icon,choice])=><button key={id} type="button" disabled={busy||autoChecking}
    aria-pressed={host===id} className={'ownership-host'+(host===id?' selected':'')}
    onClick={()=>chooseHost(id,choice)}>
    <Icon size={22} aria-hidden="true"/><span>{t(en,ar)}</span>{host===id&&<CheckCircle2 size={16} aria-hidden="true"/>}
   </button>)}
  </div>
 </details>
 <div className="ownership-simple-steps">
  <div><span>01</span><strong>{t('Choose your platform','اختر منصتك')}</strong></div>
  <div><span>02</span><strong>{t('Publish a simple proof','انشر رمز التحقق')}</strong></div>
  <div><span>03</span><strong>{t('Confirm ownership','أكد الملكية')}</strong></div>
 </div>
 <SmartVerifyPlatformGuide platform={host}/>
 <div className="ownership-choice">
  <p>{t('Recommended proof:','طريقة التحقق المقترحة:')} <strong>{method==='file'?t('Verification file','ملف تحقق'):method==='dns'?t('DNS TXT record','سجل DNS TXT'):t('HTML meta tag','وسم HTML')}</strong></p>
  <details className="ownership-advanced-method"><summary>{t('Choose another verification method','اختر طريقة تحقق أخرى')}</summary>
   <label className="form">{t('Verification method','طريقة إثبات الملكية')}
    <select value={method} onChange={e=>{setMethod(e.target.value);if(c?.method!==e.target.value)setC(null);setLink('');setCfPreview(null);setCfToken('')}}>
     <option value="file">{t('Verification file (GitHub optional)','ملف التحقق — GitHub اختياري')}</option>
     <option value="dns">{t('DNS TXT record','سجل DNS TXT')}</option>
     <option value="meta">{t('HTML meta tag','وسم HTML')}</option>
    </select>
   </label>
  </details>
 </div>
 {!c&&<button className="primary ownership-prepare" disabled={busy} onClick={()=>act(async()=>{setC(await api('/assets/'+assetId+'/challenge','POST',{method}));setLink('');setCfPreview(null);setCfToken('')})}>{t('Get verification instructions','عرض خطوات التحقق')} <ExternalLink size={16}/></button>}
 <details className="ownership-extra-settings"><summary>{t('Help and verification history','المساعدة وسجل التحقق')}</summary>
  <p>{t('A GitHub repository alone is not enough: AEGIS always checks the exact published website.','مجرد ملكية مستودع GitHub غير كافي. AEGIS بيتأكد من الموقع المنشور نفسه.')}</p>
  <button onClick={()=>act(async()=>setHistory(await api('/assets/'+assetId+'/verification-history')))}>{t('View verification history','سجل التحقق')}</button>
  {history.map(h=><p key={h.id}>{h.method} · {h.state} · {new Date(h.created*1000).toLocaleString()}</p>)}
 </details>
 {c&&<><div className="ownership-challenge-card"><p className="eyebrow">{t('YOUR THREE-STEP GUIDE','دليلك في ٣ خطوات')}</p><ol className="verification-steps">
 <li>{c.method==='file'
  ?t('Download the proof file without changing its name or contents.','نزّل ملف التحقق بدون تغيير اسمه أو محتواه.')
  :c.method==='dns'
   ?t('Open DNS settings and add the TXT record shown below.','افتح إعدادات DNS وأضف سجل TXT الموضح تحت.')
   :t('Edit the public homepage and add the supplied tag inside HTML head.','افتح الصفحة الرئيسية لموقعك وضع وسم التحقق في رأس صفحة HTML.')}</li>
 <li>{c.method==='file'
  ?t('Publish the file at the exact .well-known address on your website. GitHub users can use the shortcut below.','انشر الملف في رابط .well-known المحدد. لو بتستخدم GitHub استعمل الاختصار الموجود تحت.')
  :c.method==='dns'
   ?t('Save the record and allow time for DNS propagation.','احفظ السجل وانتظر قليلًا حتى يظهر تغيير DNS.')
   :t('Publish the update and clear any website cache.','انشر التعديل وامسح ذاكرة التخزين المؤقت للموقع.')}</li>
 <li>{t('Return here and choose Check ownership. This does not start a scan.','ارجع هنا واضغط تحقق من الملكية. هذه الخطوة لا تبدأ فحصًا.')}</li>
 </ol><div className="code" dir="ltr">{c.instruction}</div><p>{t('Proof expires','تنتهي صلاحية التحقق')}: {new Date(c.expires*1000).toLocaleString()}. Reopening instructions keeps the same valid token.</p><button disabled={busy} onClick={()=>act(async()=>{await navigator.clipboard.writeText(c.method==='meta'?c.instruction:c.token);setNotice(t('Copied.','تم النسخ.'))})}>{t('Copy verification value','نسخ قيمة التحقق')}</button>
 {c.method==='meta'&&c.wordpress&&<details><summary>{t('Use the AEGIS WordPress plugin','استخدام إضافة AEGIS في WordPress')}</summary><p>Install the supplied AEGIS verification plugin as a WordPress administrator. Open Settings → AEGIS verification, paste this challenge, save and clear the page cache. Then check ownership below.</p><pre className="code">{JSON.stringify(c.wordpress)}</pre><button onClick={()=>act(async()=>{await navigator.clipboard.writeText(JSON.stringify(c.wordpress));setNotice('WordPress challenge copied.')})}>{t('Copy WordPress challenge','نسخ بيانات تحقق WordPress')}</button></details>}
 {c.method==='dns'&&<details><summary>{t('Publish this TXT proof using Cloudflare (optional)','نشر سجل التحقق عبر Cloudflare (اختياري)')}</summary>
 <p>This creates one AEGIS TXT record in the Cloudflare zone you control. It cannot edit other DNS records or authorize website scanning. Use a Cloudflare token restricted to this zone with <strong>Zone Read and DNS Write</strong> permissions. The token is used only for this request; it is not stored in your AEGIS account.</p>
 <button disabled={busy} onClick={()=>act(async()=>setCfPreview(await api(`/assets/${assetId}/challenge/${c.id}/cloudflare/preview`)))}>{t('Review exact DNS change','مراجعة تغيير DNS المحدد')}</button>
 {cfPreview&&<div className="form"><p>Record: {cfPreview.name} · TXT · TTL {cfPreview.ttl}s</p><div className="code">{cfPreview.content}</div>
 <label>Cloudflare zone ID<input autoComplete="off" maxLength={32} value={cfZone} onChange={e=>setCfZone(e.target.value.trim())} placeholder="32-character zone ID" /></label>
 <label>Scoped Cloudflare API token<input type="password" autoComplete="off" value={cfToken} onChange={e=>setCfToken(e.target.value)} /></label>
 <label>Authenticator code (if enabled)<input autoComplete="one-time-code" value={cfMfa} onChange={e=>setCfMfa(e.target.value)} /></label>
 <label><input type="checkbox" checked={cfApproved} onChange={e=>setCfApproved(e.target.checked)} /> I authorize creating this exact TXT record in the zone I control.</label>
 <button disabled={busy||!cfApproved||cfZone.length!==32||cfToken.length<12} onClick={()=>act(async()=>{
 const result=await api(`/assets/${assetId}/challenge/${c.id}/cloudflare/publish`,'POST',{zone_id:cfZone,api_token:cfToken,confirm_dns_change:true,mfa_code:cfMfa});
 setCfToken('');setCfMfa('');setCfApproved(false);setNotice(result.message)
 })}>{t('Publish this single TXT record','نشر سجل TXT المحدد')}</button>
 <p>Publishing the record does not verify ownership immediately. Wait for DNS propagation, then select Check ownership below.</p></div>}
 </details>}
 {c.method==='dns'&&<VerificationRetry disabled={busy} key={c.id} assetId={assetId} challengeId={c.id} api={api} onRunning={setAutoChecking} onVerified={async()=>{setC(null);await onVerified()}}/>}
 {c.method==='file'&&<a className="button" href={`/api/assets/${assetId}/challenge/${c.id}/file`}>{t('Download verification file','تنزيل ملف التحقق')}</a>}
 {c.method==='file'&&<details className="ownership-github" open={host==='github'||host==='vercel'?true:undefined}><summary>{t('My website deploys from GitHub','موقعي يُنشر عبر GitHub')}</summary>
 <p>{t('This shortcut opens GitHub to prepare a verification file. Sign in on GitHub, review and commit it, and wait for your website to deploy. AEGIS does not get your GitHub password or repository access.','الاختصار ده بيفتح GitHub ويجهز ملف التحقق. سجّل دخولك هناك، راجع الملف واحفظه، وانتظر نشر الموقع. AEGIS مش بياخد كلمة السر أو صلاحيات المستودع.')}</p><div className="form"><label>{t('GitHub repository link (or owner/name)','رابط مستودع GitHub أو المالك/المستودع')}<input value={repository} placeholder="https://github.com/owner/site" onChange={e=>{setRepository(e.target.value);setLink('')}} onBlur={()=>setRepository(githubRepository(repository))}/></label><label>Public files directory<select value={directory} onChange={e=>{setDirectory(e.target.value);setLink('')}}><option value="">Root — static HTML</option><option value="public">public — Next.js / Vite</option></select></label><details><summary>{t('My deployment branch is not main','فرع النشر مش main')}</summary><label>{t('Deployment branch','فرع النشر')}<input value={branch} onChange={e=>{setBranch(e.target.value);setLink('')}} maxLength={100}/></label></details>
 <button className="primary" disabled={busy||!repository} onClick={()=>act(async()=>{const r=await api('/assets/'+assetId+'/challenge/'+c.id+'/github','POST',{repository:githubRepository(repository),directory,branch});setLink(r.url)})}>{t('Prepare file on GitHub','جهّز الملف على GitHub')} <ExternalLink size={16}/></button>{link&&<><a className="button" href={link} target="_blank" rel="noopener noreferrer">{t('Open prepared file on GitHub','افتح الملف المجهز على GitHub')} <ExternalLink size={15}/></a><p>Review and commit on the selected deployment branch, wait for your website to publish, then check ownership below. No site scan will start.</p></>}</div></details>}
 <button className="primary ownership-check" disabled={busy||autoChecking} onClick={()=>act(async()=>{const r=await api('/assets/'+assetId+'/verify/'+c.id,'POST');setNotice(r.message);setC(null);await onVerified()})}>{busy?t('Working…','جارٍ التحقق…'):t('Check ownership','تحقق من الملكية')} <CheckCircle2 size={17}/></button></div></>}
 <p className="subtle ownership-trust"><ShieldCheck size={16} aria-hidden="true"/>{t('Ownership proof does not permit scanning or AutoFix. Every assessment needs separate authorization.','إثبات الملكية لا يسمح بالفحص أو الإصلاح التلقائي. كل فحص يحتاج موافقة منفصلة.')}</p></section>
}
