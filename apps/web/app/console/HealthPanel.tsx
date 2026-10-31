'use client';
import {useEffect,useState} from 'react';
import {Activity,ArrowRight,CheckCircle2,Clock3,FileText,Globe2,History,PauseCircle,Plus,RefreshCw,ShieldCheck} from 'lucide-react';
import {useExperience} from './Experience';
type API=(p:string,m?:string,d?:unknown)=>Promise<any>;
type Asset={id:string;origin:string;verified:boolean};
type Monitor={id:string;origin:string;enabled:boolean;last_status?:string|null;expires:number};
type Sample={id:string;created:number;status:string;http_status:number|null;response_ms:number|null;tls_expires:number|null};
export default function HealthPanel({api,org,assets,canManage=false}:{api:API;org:string;canManage?:boolean;assets:Asset[]}){
 const {t}=useExperience();
 const [rows,setRows]=useState<Monitor[]>([]),[samples,setSamples]=useState<Sample[]>([]),[selectedHistory,setSelectedHistory]=useState(''),[loaded,setLoaded]=useState(false),[formOpen,setFormOpen]=useState(false);
 const [asset,setAsset]=useState(''),[path,setPath]=useState('/'),[interval,setInterval]=useState(900),[consent,setConsent]=useState(false);
 const [error,setError]=useState(''),[busy,setBusy]=useState(false);
 const verified=assets.filter(a=>a.verified),active=rows.filter(r=>r.enabled&&r.expires>Date.now()/1000).length;
 async function load(){const result=await api(`/organizations/${org}/health-monitors`);setRows(Array.isArray(result)?result:[]);setLoaded(true)}
 useEffect(()=>{let current=true;setLoaded(false);setRows([]);setSamples([]);setSelectedHistory('');api(`/organizations/${org}/health-monitors`).then(r=>{if(current){setRows(Array.isArray(r)?r:[]);setLoaded(true)}}).catch(e=>{if(current){setError(e.message);setLoaded(true)}});return()=>{current=false}},[api,org]);
 async function act(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function viewHistory(id:string){await act(async()=>{if(selectedHistory===id){setSelectedHistory('');setSamples([]);return;}const data=await api(`/health-monitors/${id}/samples`);setSamples(Array.isArray(data)?data:[]);setSelectedHistory(id)})}
 return <div className="ops-module">
  <header className="ops-hero">
   <div className="ops-eyebrow"><Activity size={15}/>{t('CONTINUOUS MONITORING','المراقبة المستمرة')}</div>
   <div className="ops-hero-content"><div><h2>{t('Know when your website needs attention.','اعرف إمتى موقعك محتاج متابعة.')}</h2><p>{t('Monitor the availability of approved public pages, check recent responses and download reports. Monitoring is not a vulnerability scan.','تابع توافر الصفحات العامة اللي وافقت عليها، وشوف الردود السابقة وحمّل التقارير. المراقبة مش فحص ثغرات.')}</p></div>
    <span className="ops-hero-safety"><ShieldCheck size={16}/>{t('Approved checks only','فحوص متابعة بموافقتك')}</span>
   </div>
  </header>
  {error&&<p role="alert" className="ops-feedback">{error}</p>}
  <div className="ops-monitor-stats">
   <div><span><Globe2 size={15}/>{t('Verified websites','مواقع مثبتة الملكية')}</span><strong>{verified.length}</strong></div>
   <div><span><Activity size={15}/>{t('Active monitors','مراقبات فعالة')}</span><strong>{loaded?active:'…'}</strong></div>
   <div><span><History size={15}/>{t('Recorded monitors','مراقبات مسجلة')}</span><strong>{loaded?rows.length:'…'}</strong></div>
  </div>
  <section className="ops-section">
   <div className="ops-toolbar"><div><h3>{t('My website monitors','مراقبة مواقعي')}</h3><p>{t('Only results returned by the monitoring service are shown.','البيانات دي من نظام المراقبة الحقيقي فقط.')}</p></div>
    <div className="ops-actions">
      <button disabled={busy} onClick={()=>act(load)}><RefreshCw size={15}/>{t('Refresh status','تحديث الحالة')}</button>
      {canManage&&<button className="primary" onClick={()=>setFormOpen(s=>!s)}><Plus size={16}/>{formOpen?t('Close setup','إغلاق الإعداد'):t('Add a monitor','أضف مراقبة')}</button>}
    </div>
   </div>
   {!loaded&&!error&&<p role="status">{t('Loading monitoring records…','جاري تحميل سجلات المراقبة…')}</p>}
   {loaded&&!rows.length&&<div className="ops-empty"><Activity size={26}/><strong>{t('No monitoring set up yet','لسه مفيش مراقبة مفعّلة')}</strong>
    <p>{t('Choose a verified website and an approved public path to start bounded health checks.','اختار موقع مثبت الملكية ومسار عام ووافق على فحوص متابعة محدودة.')}</p>
    {canManage&&verified.length>0&&<button className="primary" onClick={()=>setFormOpen(true)}>{t('Set up my first monitor','إعداد أول مراقبة')} <ArrowRight size={15}/></button>}
   </div>}
   <div className="ops-monitor-list">
    {rows.map(r=><article key={r.id} className="ops-monitor-card">
     <div className="ops-monitor-row"><div><strong>{r.origin}</strong><p>{t('Latest result','آخر نتيجة')}: {r.last_status||t('No sample yet','لم يتم تسجيل نتيجة بعد')}</p></div><span className={'ops-status '+(r.enabled&&r.expires>Date.now()/1000?'good':'')}>{r.enabled&&r.expires>Date.now()/1000?t('Enabled','مفعّل'):t('Inactive','غير مفعّل')}</span></div>
     <div className="ops-monitor-detail"><Clock3 size={14}/>{t('Permission ends','تنتهي الموافقة')}: {new Date(r.expires*1000).toLocaleString()}</div>
     <div className="ops-inline-actions">
      <button disabled={busy} onClick={()=>void viewHistory(r.id)}><History size={14}/>{selectedHistory===r.id?t('Hide observations','إخفاء السجل'):t('View observations','عرض السجل')}</button>
      <a className="button" href={`/api/health-monitors/${encodeURIComponent(r.id)}/report.pdf`} download><FileText size={14}/>{t('PDF report','تقرير PDF')}</a>
      {canManage&&r.enabled&&<button className="ops-danger-action" disabled={busy} onClick={()=>act(async()=>{await api(`/health-monitors/${r.id}`,'DELETE');await load();if(selectedHistory===r.id){setSelectedHistory('');setSamples([])}})}><PauseCircle size={14}/>{t('Stop monitoring','إيقاف المراقبة')}</button>}
     </div>
     {selectedHistory===r.id&&<section className="ops-history" aria-label={t('Monitoring observations','سجل المراقبة')}>
      {!samples.length?<p>{t('No recorded samples for this monitor yet.','لا يوجد سجل قياسات لهذا الموقع حتى الآن.')}</p>:samples.map(s=><div key={s.id} className="ops-history-row">
        <span>{new Date(s.created*1000).toLocaleString()}</span><strong>{s.status}</strong><span>HTTP {s.http_status??'—'}</span><span>{s.response_ms==null?'—':Math.round(s.response_ms)+' ms'}</span>
        <span>{t('TLS expiry','انتهاء TLS')}: {s.tls_expires?new Date(s.tls_expires*1000).toLocaleDateString():t('Unavailable','غير متاح')}</span>
       </div>)}
     </section>}
    </article>)}
   </div>
  </section>
  {formOpen&&canManage&&<section className="ops-section">
   <div className="ops-section-title"><span className="ops-section-num">01</span><div><h3>{t('Create an approved monitor','إعداد مراقبة بموافقتك')}</h3><p>{t('A single bounded GET to the chosen path per interval, for up to 24 hours. No scans or changes.','طلب GET محدود للمسار المحدد حسب الفترة ولمدة أقصاها 24 ساعة. من غير فحص ثغرات أو تعديل.')}</p></div></div>
   {!verified.length?<div className="ops-empty"><ShieldCheck size={24}/><strong>{t('Verify a website first','لازم إثبات ملكية موقع أولًا')}</strong><p>{t('No verified website is currently available for monitoring.','مفيش موقع مثبت الملكية متاح للمراقبة حاليًا.')}</p></div>:<form className="ops-monitor-form" onSubmit={e=>{e.preventDefault();void act(async()=>{await api(`/assets/${asset}/health-monitor`,'PUT',{accepted:consent,path,interval_seconds:interval,hours:24});setConsent(false);setFormOpen(false);await load()})}}>
     <label>{t('Verified website','الموقع المثبت ملكيته')}<select value={asset} onChange={e=>{setAsset(e.target.value);setConsent(false)}} required><option value="">{t('Choose your website','اختار موقعك')}</option>{verified.map(a=><option key={a.id} value={a.id}>{a.origin}</option>)}</select></label>
     <label>{t('Public URL path','مسار الصفحة العامة')}<input value={path} onChange={e=>{setPath(e.target.value);setConsent(false)}} required placeholder="/" pattern="/.*"/></label>
     <label>{t('Check frequency','تكرار فحص التوافر')}<select value={interval} onChange={e=>{setInterval(Number(e.target.value));setConsent(false)}}><option value={300}>{t('Every 5 minutes','كل 5 دقائق')}</option><option value={900}>{t('Every 15 minutes','كل 15 دقيقة')}</option><option value={3600}>{t('Every hour','كل ساعة')}</option><option value={86400}>{t('Daily','يوميًا')}</option></select></label>
     <label className="ops-consent"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/><span>{t('I authorize one bounded GET per interval to this exact path for up to 24 hours. This does not authorize security assessments or edits.','أوافق على طلب GET واحد محدود للمسار ده في كل فترة لمدة أقصاها 24 ساعة. ده مش إذن بفحص ثغرات أو تعديل الموقع.')}</span></label>
     <button className="primary" disabled={busy||!asset||!consent}><CheckCircle2 size={16}/>{t('Authorize monitoring','الموافقة وبدء المراقبة')}</button>
    </form>}
  </section>}
  <p className="ops-safety-note"><ShieldCheck size={14}/>{t('Checks stop when ownership or permission expires. Domain expiry dates are not inferred. Monitoring does not guarantee availability.','المراقبة بتتوقف بانتهاء الملكية أو الموافقة. لا نخمن صلاحية الدومين ولا نضمن توافر الموقع طوال الوقت.')}</p>
 </div>;
}
