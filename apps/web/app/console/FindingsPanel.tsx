'use client';
import {useEffect,useState} from 'react';
import {AlertTriangle,ArrowRight,CheckCircle2,ClipboardList,Eye,FileSearch,Filter,History,RefreshCw,Search,ShieldCheck,Wrench} from 'lucide-react';
import {useExperience} from './Experience';
import FastFixGuidance from './FastFixGuidance';

type API=(path:string,method?:string,data?:unknown)=>Promise<any>;
type Finding={
 id:string;title:string;origin:string;rule:string;severity:string;confidence:string;status:string;
 evidence:string;remediation:string;
};
type FindingPage={total:number;items:Finding[]};
const reviewable=['open','under_review','accepted_risk','false_positive'];
const cannotRequest=['resolved','false_positive','accepted_risk'];
const statuses=['new','open','under_review','accepted_risk','false_positive','remediation_requested','in_progress','ready_for_retest','resolved','reopened'];
const priorities=['critical','high','medium','low','info'];
export default function FindingsPanel({api,org,role,onRemediation,onOpenRemediation}:{
 api:API;org:string;role:string;onRemediation:()=>Promise<void>;onOpenRemediation?:()=>void;
}){
 const {t}=useExperience();
 const [query,setQuery]=useState(''),[q,setQ]=useState(''),[severity,setSeverity]=useState(''),[status,setStatus]=useState(''),[sort,setSort]=useState('recent'),[offset,setOffset]=useState(0),[revision,setRevision]=useState(0);
 const [page,setPage]=useState<FindingPage|null>(null),[history,setHistory]=useState<any>(null),[historyId,setHistoryId]=useState(''),[historyOffset,setHistoryOffset]=useState(0),[explanation,setExplanation]=useState<any>(null),[explanationId,setExplanationId]=useState('');
 const [error,setError]=useState(''),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true);
 const canWrite=['owner','admin','analyst'].includes(role);
 useEffect(()=>{
  let active=true;setPage(null);setError('');setLoading(true);setHistory(null);setHistoryId('');setExplanation(null);setExplanationId('');
  const params=new URLSearchParams({q,severity,status,sort,offset:String(offset),limit:'25'});
  api(`/organizations/${org}/finding-page?${params.toString()}`).then((r:FindingPage)=>{if(active)setPage(r)}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});
  return()=>{active=false};
 },[api,org,q,severity,status,sort,offset,revision]);
 async function act(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function loadHistory(id:string,start=0){await act(async()=>{setExplanation(null);setExplanationId('');const r=await api(`/findings/${id}/history?offset=${start}&limit=25`);setHistory(r);setHistoryId(id);setHistoryOffset(start)})}
 async function loadExplanation(id:string){await act(async()=>{setHistory(null);setHistoryId('');setExplanation(await api(`/findings/${id}/explanation`));setExplanationId(id)})}
 const counts=Object.fromEntries(priorities.map(key=>[key,page?.items.filter(f=>f.severity===key).length||0]));
 const openCount=page?.items.filter(f=>!cannotRequest.includes(f.status)).length||0;
 return <section className="finding-workspace" aria-label={t('Findings and fixing workspace','مساحة النتائج والإصلاحات')}>
  <header className="finding-hero glass">
   <div className="finding-eyebrow"><ShieldCheck size={15}/>{t('FINDINGS & FIXING','النتائج والإصلاحات')}</div>
   <div className="finding-hero-head">
    <div><h2>{t('From evidence to a verified improvement.','من الدليل إلى إصلاح تم التحقق منه.')}</h2>
     <p>{t('One clear workflow: review the observation, choose a safe response, approve any change and retest.','رحلة واضحة: افهم الملاحظة، اختار الحل، وافق على أي تعديل، ثم أعد الفحص.')}</p>
    </div>
    {onOpenRemediation&&<button type="button" className="finding-requests-link" onClick={onOpenRemediation}><Wrench size={16}/>{t('My fix requests','طلبات الإصلاح')}<ArrowRight size={15}/></button>}
   </div>
   <ol className="finding-journey">
    {[[FileSearch,t('Detect','اكتشاف')],[Eye,t('Understand','فهم الدليل')],[Wrench,t('Approve fix','اعتماد الإصلاح')],[RefreshCw,t('Retest','إعادة الفحص')]].map(([Icon,label],i)=>{
     const StepIcon=Icon as typeof FileSearch;
     return <li key={i}><span className="finding-journey-icon"><StepIcon size={17}/></span><small>{String(i+1).padStart(2,'0')} · {label as string}</small></li>;
    })}
   </ol>
  </header>
  <div className="finding-metrics" aria-label={t('Results on this page','نتائج الصفحة الحالية')}>
   <div className="finding-metric total"><span>{t('Matching results','النتائج المطابقة')}</span><strong>{page?.total??(loading?'…':'—')}</strong><small>{t('Across search and filters','حسب البحث والفلاتر')}</small></div>
   <div className="finding-metric"><span>{t('Needs a decision','تحتاج قرارًا')}</span><strong>{page?openCount:'—'}</strong><small>{t('On this page','في الصفحة الحالية')}</small></div>
   <div className="finding-metric"><span>{t('High priority','عالية الأولوية')}</span><strong>{page?counts.critical+counts.high:'—'}</strong><small>{t('Critical + high on this page','حرجة وعالية في هذه الصفحة')}</small></div>
   <div className="finding-metric"><span>{t('Medium / low','متوسطة / منخفضة')}</span><strong>{page?counts.medium+counts.low:'—'}</strong><small>{t('On this page','في الصفحة الحالية')}</small></div>
  </div>
  <section className="finding-filters glass" aria-label={t('Filter observations','تصفية الملاحظات')}>
   <div className="finding-filter-head"><h3><Filter size={18}/>{t('Find the issue you need','حدد المشكلة اللي عايز تراجعها')}</h3>
   {(q||severity||status||sort!=='recent')&&<button type="button" onClick={()=>{setQuery('');setQ('');setSeverity('');setStatus('');setSort('recent');setOffset(0)}}>{t('Clear filters','مسح الفلاتر')}</button>}</div>
   <form className="finding-search-form" onSubmit={e=>{e.preventDefault();setQ(query);setOffset(0)}}>
    <label>{t('Search observations','ابحث في الملاحظات')}<span className="finding-search-control"><Search size={16}/><input maxLength={100} placeholder={t('Title, rule or website','العنوان أو القاعدة أو الموقع')} value={query} onChange={e=>setQuery(e.target.value)}/></span></label>
    <button type="submit" disabled={loading}>{t('Search all findings','بحث في كل النتائج')}</button>
   </form>
   <div className="finding-filter-grid">
    <label>{t('Severity','الخطورة')}<select value={severity} onChange={e=>{setSeverity(e.target.value);setOffset(0)}}><option value="">{t('All severities','كل المستويات')}</option>{priorities.map(s=><option key={s} value={s}>{s}</option>)}</select></label>
    <label>{t('Status','الحالة')}<select value={status} onChange={e=>{setStatus(e.target.value);setOffset(0)}}><option value="">{t('All statuses','كل الحالات')}</option>{statuses.map(s=><option key={s} value={s}>{s.replaceAll('_',' ')}</option>)}</select></label>
    <label>{t('Sort','الترتيب')}<select value={sort} onChange={e=>{setSort(e.target.value);setOffset(0)}}><option value="recent">{t('Recently observed','الأحدث')}</option><option value="oldest">{t('First observed','الأقدم')}</option><option value="severity">{t('Severity priority','الأعلى خطورة')}</option></select></label>
   </div>
  </section>
  <p className="finding-safety"><ShieldCheck size={15}/>{t('These are observed configuration signals, not demonstrated exploits. No fix is applied without separate approval and validation.','هذه ملاحظات إعدادات وليست ثغرات مثبتة الاستغلال. لن يُطبّق إصلاح بدون موافقة وتحقق منفصل.')}</p>
  {error&&<p role="alert" className="error">{error}</p>}
  {loading&&<p role="status">{t('Loading findings…','جاري تحميل النتائج…')}</p>}
  {page&&<>
   <div className="finding-results-head"><h3>{t('Your observations','ملاحظات موقعك')}</h3><span>{page.total} {t('matching findings','نتيجة مطابقة')}</span></div>
   {!page.items.length&&<div className="finding-empty glass"><CheckCircle2 size={25}/><strong>{t('No observations match these filters.','لا توجد ملاحظات تطابق هذه الفلاتر.')}</strong><p>{t('This does not certify that the website is secure.','ده مش ضمان إن الموقع آمن بالكامل.')}</p></div>}
   <div className="finding-results-list">
   {page.items.map((f,index)=><article className="finding-result-card glass" key={f.id}>
    <div className="finding-result-top"><div className="finding-result-index">{String(offset+index+1).padStart(2,'0')}</div><div className="finding-result-heading"><h4>{f.title}</h4><p dir="auto">{f.origin}</p></div><span className={'finding-severity '+f.severity}>{f.severity}</span></div>
    <div className="finding-result-tags"><span>{t('Status','الحالة')}: {f.status.replaceAll('_',' ')}</span><span>{t('Rule','القاعدة')}: {f.rule}</span><span>{t('Confidence','الثقة')}: {f.confidence}</span></div>
    <div className="finding-next-action"><strong><ClipboardList size={15}/>{t('Recommended next action','الخطوة المقترحة')}</strong><p>{f.remediation}</p></div>
    <details className="finding-review-details">
     <summary><Eye size={15}/>{t('Evidence and technical context','الدليل والتفاصيل الفنية')}</summary>
     <p dir="auto">{f.evidence}</p><p>{t('Observed configuration; exploitability has not been demonstrated.','ملاحظة إعدادات؛ لم يتم إثبات إمكانية استغلالها.')}</p>
     <FastFixGuidance key={f.id} api={api} findingId={f.id}/>
    </details>
    <div className="finding-result-actions">
     {canWrite&&<button type="button" className="primary" disabled={busy||cannotRequest.includes(f.status)} onClick={()=>act(async()=>{await api('/remediations','POST',{finding_id:f.id});await onRemediation()})}><Wrench size={15}/>{t('Request remediation','اطلب إصلاحًا')}</button>}
     <button type="button" disabled={busy} onClick={()=>loadExplanation(f.id)}><FileSearch size={15}/>{t('Explain','اشرح')} · {f.title}</button>
     <button type="button" disabled={busy} onClick={()=>loadHistory(f.id)}><History size={15}/>{t('History','السجل')} · {f.title}</button>
    </div>
    {canWrite&&<div className="finding-review-state"><label>{t('Human review status','حالة المراجعة البشرية')}<select disabled={busy} value={reviewable.includes(f.status)?f.status:''} onChange={e=>{const value=e.target.value;act(async()=>{await api(`/findings/${f.id}`,'PATCH',{status:value});setRevision(v=>v+1)})}}><option value="" disabled>{t('Review status','تحديث الحالة')}</option>{reviewable.map(s=><option key={s} value={s}>{s.replaceAll('_',' ')}</option>)}</select></label></div>}
    {history&&historyId===f.id&&<section className="finding-inline-detail" aria-label="Finding history">
     <div className="finding-detail-head"><h5>{t('Finding history','سجل الملاحظة')}</h5><button type="button" onClick={()=>{setHistory(null);setHistoryId('')}}>{t('Close','إغلاق')}</button></div>
     <p>{history.total} {t('recorded events','حدث مسجل')}</p>
     {history.items.map((h:any)=><div className="finding-history-row" key={h.id}><span>{new Date(h.created*1000).toLocaleString()} · {h.status.replaceAll('_',' ')}</span><span>{h.job_id?'Assessment '+h.job_id:t('Human review event','مراجعة بشرية')}</span></div>)}
     <div className="actions"><button disabled={busy||historyOffset===0} onClick={()=>loadHistory(f.id,Math.max(0,historyOffset-25))}>{t('Earlier history page','صفحة سجل سابقة')}</button><button disabled={busy||historyOffset+25>=history.total} onClick={()=>loadHistory(f.id,historyOffset+25)}>{t('Next history page','صفحة سجل تالية')}</button></div>
    </section>}
    {explanation&&explanationId===f.id&&<section className="finding-inline-detail" aria-label="Finding explanation">
     <div className="finding-detail-head"><h5>{t('Finding explanation','شرح الملاحظة')}</h5><button type="button" onClick={()=>{setExplanation(null);setExplanationId('')}}>{t('Close','إغلاق')}</button></div>
     <p className="subtle">{explanation.mode}</p><p>{explanation.summary}</p><p>{explanation.business_impact}</p><p>{explanation.limitations}</p><p>{explanation.effort_classification}</p>
     {Object.entries(explanation.effort||{}).map(([rule,effort])=><p key={rule}>{rule}: {String(effort).replaceAll('_',' ')}</p>)}
     {explanation.fallback_reason&&<p>{explanation.fallback_reason}</p>}
     {explanation.recommendations?.map((r:any)=><p key={r.rule}>{r.action}</p>)}
    </section>}
   </article>)}
   </div>
   <nav className="finding-pagination" aria-label={t('Findings pages','صفحات النتائج')}>
    <span>{page.total>0?offset+1:0}–{Math.min(offset+page.items.length,page.total)} / {page.total}</span>
    <div className="actions"><button disabled={loading||offset===0} onClick={()=>setOffset(v=>Math.max(0,v-25))}>{t('Previous findings','النتائج السابقة')}</button><button disabled={loading||offset+25>=page.total} onClick={()=>setOffset(v=>v+25)}>{t('Next findings','النتائج التالية')}</button></div>
   </nav>
  </>}
 </section>;
}
