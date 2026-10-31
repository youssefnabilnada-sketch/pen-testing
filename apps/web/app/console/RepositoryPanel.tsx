'use client';
import RecoveryPanel from './RecoveryPanel';
import {useExperience} from './Experience';
import {useCallback,useEffect,useState} from 'react';
import {AlertCircle,ArrowRight,Code2,FileCode2,GitBranch,GitPullRequest,LockKeyhole,RefreshCw,ShieldCheck} from 'lucide-react';
type API=(path:string,method?:string,data?:unknown)=>Promise<any>;
type Patch={id:string;repository:string;diff:string;status:string;tests:Record<string,unknown>;pull_number:number|null};
type Connection={id:string;login:string;revoked?:boolean;expires:number};
type Repository={name:string};
export default function RepositoryPanel({api,org,requests,role,onOpenFindings}:{
 api:API;org:string;requests:{id:string;finding_title:string}[];role:string;onOpenFindings?:()=>void;
}){
 const {t}=useExperience();
 const [connections,setConnections]=useState<Connection[]>([]),[patches,setPatches]=useState<Patch[]>([]),[repos,setRepos]=useState<Repository[]>([]);
 const [connection,setConnection]=useState(''),[repository,setRepository]=useState(''),[request,setRequest]=useState(''),[consent,setConsent]=useState(false);
 const [proposalConsent,setProposalConsent]=useState(false),[approved,setApproved]=useState(''),[code,setCode]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[fetchingRepos,setFetchingRepos]=useState(false);
 const [callback,setCallback]=useState<{code:string;state:string}|null>(null),[adapter,setAdapter]=useState('vercel'),[repoPage,setRepoPage]=useState(1);
 const canWrite=['owner','admin'].includes(role),hasConnection=connections.some(c=>!c.revoked);
 const blocked=error.toLowerCase().includes('github app configuration')||error.toLowerCase().includes('github integration is not configured');
 const refresh=useCallback(async()=>{
  if(!canWrite)return;
  const [c,p]=await Promise.all([api(`/organizations/${org}/github`),api(`/organizations/${org}/repository-patches`)]);
  setConnections(Array.isArray(c)?c:[]);setPatches(Array.isArray(p)?p:[]);
 },[api,org,canWrite]);
 useEffect(()=>{setConnections([]);setPatches([]);setConnection('');setRepos([]);setRepository('');setRequest('');setConsent(false);setApproved('');setError('');refresh().catch(e=>setError(e.message))},[refresh]);
 useEffect(()=>{const params=new URLSearchParams(window.location.search);if(params.get('code')&&params.get('state'))setCallback({code:params.get('code')!,state:params.get('state')!})},[]);
 useEffect(()=>{setConsent(false);setProposalConsent(false);setApproved('')},[connection,repository,request,adapter]);
 async function run(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn();await refresh()}catch(e){setError((e as Error).message)}finally{setBusy(false);setCode('')}}
 async function loadRepositories(id:string,page:number){
  setRepoPage(page);setRepository('');setRepos([]);if(!id)return;
  setFetchingRepos(true);setError('');
  try{const list=await api(`/github/connections/${id}/repositories?page=${page}`);setRepos(Array.isArray(list)?list:[])}
  catch(e){setError((e as Error).message)}
  finally{setFetchingRepos(false)}
 }
 const canPropose=canWrite&&Boolean(connection&&repository&&request&&proposalConsent)&&!busy;
 return <section className="repo-journey" aria-label={t('Repository review and proposed fixes','مراجعة المستودع والإصلاحات المقترحة')}>
  <header className="ops-hero">
   <div className="ops-eyebrow"><GitPullRequest size={15}/>{t('OPTIONAL · CODE-ASSISTED FIXES','اختياري · إصلاحات مدعومة بالكود')}</div>
   <div className="ops-hero-content"><div><h2>{t('Review a fix before anything changes.','راجع الإصلاح قبل أي تعديل.')}</h2>
   <p>{t('Connect only a repository you choose, generate a limited proposal, and approve a draft pull request. No source code access or deployment happens just by finding an issue.','اربط المستودع اللي تختاره فقط، وراجع التعديل المقترح قبل الموافقة على Pull Request. اكتشاف مشكلة لا يمنح وصولًا للكود ولا ينشر إصلاحًا.')}</p></div>
   <span className="ops-hero-safety"><ShieldCheck size={18}/>{t('No automatic production changes','مفيش تغيير مباشر على الإنتاج')}</span></div>
   <div className="ops-steps">
    <div><span>01</span><strong>{t('Connect safely','اربط بأمان')}</strong><small>{t('Only selected repos','المستودعات المحددة فقط')}</small></div>
    <div><span>02</span><strong>{t('Choose a finding','اختار الملاحظة')}</strong><small>{t('Limited supported fixes','إصلاحات مدعومة محدودة')}</small></div>
    <div><span>03</span><strong>{t('Review a proposal','راجع الاقتراح')}</strong><small>{t('Explicit approval & retest','موافقة ثم إعادة فحص')}</small></div>
   </div>
  </header>
  <div className="ops-toolbar"><strong>{t('Repository connection','ربط المستودع')}</strong><span className={'ops-status'+(hasConnection?' good':'')}>{hasConnection?t('Connection available','يوجد اتصال'):t('Not connected','غير متصل')}</span></div>
  {error&&<div role="alert" className={'ops-feedback'+(blocked?' ops-feedback-config':'')}><AlertCircle size={18}/><div><strong>{blocked?t('GitHub integration needs administrator setup','ربط GitHub محتاج إعداد من مدير AEGIS'):t('Connection needs attention','في مشكلة في الاتصال')}</strong><p>{blocked?t('AEGIS cannot start the GitHub App connection yet. An administrator must configure the app securely on the server. Your site and findings are unaffected.','AEGIS مش قادر يبدأ ربط GitHub حاليًا. لازم مدير النظام يجهز GitHub App على السيرفر بأمان. موقعك ونتائج الفحص مش متأثرين.'):error}</p></div></div>}
  <div className="ops-two-col">
   <section className="ops-section">
    <div className="ops-section-title"><span className="ops-section-num">01</span><div><h3>{t('Link your code, only if needed','اربط الكود عند الحاجة فقط')}</h3><p>{t('GitHub is optional. You can fix hosting settings or ask a developer without linking any source code.','GitHub مش إجباري. ممكن تصلح من إعدادات الاستضافة أو تسلّم الخطوات للمطوّر من غير ربط الكود.')}</p></div></div>
    {canWrite?<div className="ops-content">
     <label className="ops-consent"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/><span>{t('I authorize AEGIS to request access to repositories I select and to prepare proposals for my review.','أوافق على طلب الوصول للمستودعات اللي أحددها فقط وتجهيز اقتراحات للمراجعة.')}</span></label>
     <div className="ops-actions">
      <button className="primary" disabled={busy||!consent} onClick={()=>run(async()=>{const r=await api(`/organizations/${org}/github/start`,'POST',{accepted:true});if(!r?.url)throw new Error('GitHub connection URL was not returned.');window.location.assign(r.url)})}><GitBranch size={16}/>{t('Connect GitHub securely','ربط GitHub بأمان')}</button>
      {callback&&<button disabled={busy} onClick={()=>run(async()=>{await api(`/organizations/${org}/github/complete`,'POST',callback);setCallback(null);window.history.replaceState({},'',window.location.pathname)})}>{t('Finish secure connection','إكمال الاتصال الآمن')}</button>}
     </div>
     {hasConnection&&<label>{t('Connected account','الحساب المرتبط')}<select value={connection} onChange={e=>{setConnection(e.target.value);void loadRepositories(e.target.value,1)}}>
      <option value="">{t('Choose an authorized account','اختار حسابًا مصرحًا')}</option>{connections.filter(c=>!c.revoked).map(c=><option key={c.id} value={c.id}>{c.login} · {t('expires','ينتهي')} {new Date(c.expires*1000).toLocaleDateString()}</option>)}</select></label>}
     {connection&&<div className="ops-inline-actions"><button disabled={busy||fetchingRepos} onClick={()=>void loadRepositories(connection,repoPage)}><RefreshCw size={14}/>{fetchingRepos?t('Loading repositories…','جاري التحميل…'):t('Refresh repositories','تحديث المستودعات')}</button><button disabled={busy} onClick={()=>run(async()=>{await api(`/github/connections/${connection}`,'DELETE');setConnection('');setRepos([]);setRepository('')})}>{t('Disconnect','فصل الاتصال')}</button></div>}
    </div>:<p className="ops-muted">{t('Only the workspace owner or admin can connect repositories.','ربط المستودعات متاح لمالك مساحة العمل أو المدير فقط.')}</p>}
    <div className="ops-alternative"><FileCode2 size={20}/><div><strong>{t('No GitHub? You can still remediate.','مش عندك GitHub؟ عادي.')}</strong><p>{t('Review FastFix guidance in Findings, change approved hosting settings yourself, or share a developer handoff. No repository is needed for every fix.','راجع إرشادات FastFix في النتائج، أو عدّل إعدادات الاستضافة بموافقتك، أو ابعت التعليمات لمطورك. مش كل إصلاح محتاج مستودع.')}</p>
     {onOpenFindings&&<button onClick={onOpenFindings}>{t('Open findings and guidance','افتح النتائج والإرشادات')} <ArrowRight size={14}/></button>}</div></div>
   </section>
   <section className="ops-section">
    <div className="ops-section-title"><span className="ops-section-num">02</span><div><h3>{t('Prepare one precise proposal','جهّز اقتراحًا محددًا')}</h3><p>{t('Only the supported hosting configuration changes are eligible.','فقط تعديلات إعدادات الاستضافة المدعومة متاحة للاقتراح.')}</p></div></div>
    {canWrite&&connection?<div className="ops-content">
      <label>{t('Repository','المستودع')}<select disabled={fetchingRepos} value={repository} onChange={e=>setRepository(e.target.value)}><option value="">{t('Select a repository','اختر المستودع')}</option>{repos.map(r=><option key={r.name} value={r.name}>{r.name}</option>)}</select></label>
      <div className="ops-inline-actions">
       <button disabled={busy||fetchingRepos||repoPage===1} onClick={()=>void loadRepositories(connection,repoPage-1)}>{t('Previous','السابق')}</button><small>{t('Page','صفحة')} {repoPage}</small><button disabled={busy||fetchingRepos||repos.length===0||repoPage===100} onClick={()=>void loadRepositories(connection,repoPage+1)}>{t('Next','التالي')}</button>
      </div>
      <label>{t('Hosting platform','منصة الاستضافة')}<select value={adapter} onChange={e=>setAdapter(e.target.value)}><option value="vercel">Vercel — vercel.json</option><option value="netlify">Netlify — static netlify.toml</option></select></label>
      <label>{t('Finding with a remediation request','ملاحظة لها طلب إصلاح')}<select value={request} onChange={e=>setRequest(e.target.value)}><option value="">{t('Choose a request','اختار طلب إصلاح')}</option>{requests.map(r=><option key={r.id} value={r.id}>{r.finding_title||r.id}</option>)}</select></label>
      {!requests.length&&<p className="ops-muted">{t('No remediation requests yet. Start from a finding first.','مفيش طلبات إصلاح لسه. ابدأ من إحدى نتائج الفحص أولًا.')}</p>}
      <label className="ops-consent"><input type="checkbox" checked={proposalConsent} onChange={e=>setProposalConsent(e.target.checked)}/><span>{t('I authorize this specific repository and finding to be analyzed for a reviewable proposal. Changing the selection requires new consent.','أوافق على مراجعة هذا المستودع وهذه الملاحظة فقط لتجهيز اقتراح. تغيير الاختيار يحتاج موافقة جديدة.')}</span></label>
      <button className="primary" disabled={!canPropose} onClick={()=>run(async()=>{await api('/repository-patches','POST',{connection_id:connection,repository,adapter,remediation_id:request,accepted:true})})}><Code2 size={16}/>{t('Prepare reviewable change','جهّز تعديلًا للمراجعة')}</button>
    </div>:<div className="ops-empty"><LockKeyhole size={24}/><strong>{t('Repository not selected yet','لسه مفيش مستودع محدد')}</strong><p>{t('Connect an authorized account first. This step will unlock only after explicit consent.','اربط حسابًا مصرحًا أولًا. المرحلة دي مش هتتفعل إلا بعد موافقتك.')}</p></div>}
   </section>
  </div>
  <section className="ops-section ops-proposals"><div className="ops-section-title"><span className="ops-section-num">03</span><div><h3>{t('Review and approve proposed changes','راجع واقبل التعديلات المقترحة')}</h3><p>{t('A draft PR is never an automatic merge or deployment. Every accepted change still requires validation and a separate authorized retest.','الـDraft PR مش دمج ولا نشر تلقائي. لازم اختبار التعديل وإعادة فحص بتصريح جديد.')}</p></div></div>
  {!patches.length&&<div className="ops-empty"><GitPullRequest size={24}/><strong>{t('No code proposals yet','مفيش اقتراحات كود حتى الآن')}</strong><p>{t('That is normal. You can complete manual remediations without linking a repository.','ده طبيعي. تقدر تكمل إصلاحات يدوية من غير ربط مستودع.')}</p></div>}
  {patches.map(p=><article key={p.id} className="ops-proposal-card">
   <div className="ops-proposal-head"><div><strong>{p.repository}</strong><small>{t('Proposal status','حالة الاقتراح')}: {p.status.replaceAll('_',' ')}</small></div><span className="ops-status">{p.status.replaceAll('_',' ')}</span></div>
   <details><summary><FileCode2 size={15}/>{t('Review exact code diff and tests','راجع التغيير والاختبارات بالتفصيل')}</summary><pre className="code">{p.diff}</pre><pre className="code">{JSON.stringify(p.tests,null,2)}</pre></details>
   {canWrite&&<RecoveryPanel api={api} patchId={p.id} onChanged={refresh}/>}
   {canWrite&&p.status==='review_required'&&<div className="ops-approval">
    <label className="ops-consent"><input type="checkbox" checked={approved===p.id} onChange={e=>setApproved(e.target.checked?p.id:'')}/><span>{t('I reviewed this exact diff and approve only publishing a draft PR. No merge or deployment.','راجعت التغيير ده وبوافق فقط على إنشاء Draft PR، من غير دمج أو نشر.')}</span></label>
    <label>{t('Authenticator or recovery code','رمز المصادقة أو الاستعادة')}<input autoComplete="one-time-code" value={code} onChange={e=>setCode(e.target.value)}/></label>
    <button className="primary" disabled={busy||approved!==p.id||code.length<6} onClick={()=>run(async()=>{await api(`/repository-patches/${p.id}/pull-request`,'POST',{accepted:true,mfa_code:code});setApproved('')})}><GitPullRequest size={15}/>{t('Publish approved draft PR','إنشاء Draft PR بعد الموافقة')}</button>
   </div>}
   {p.pull_number&&<button disabled={busy} onClick={()=>run(async()=>{await api(`/repository-patches/${p.id}/refresh`,'POST')})}><RefreshCw size={14}/>{t('Refresh pull request and CI','تحديث طلب الدمج والاختبارات')} #{p.pull_number}</button>}
   <p className="ops-muted"><ShieldCheck size={14}/>{t('A merged pull request does not close a finding. Record deployment evidence and authorize a separate retest.','حتى دمج Pull Request لا يغلق الملاحظة. لازم توثيق النشر والموافقة على إعادة فحص منفصلة.')}</p>
  </article>)}
  </section>
 </section>;
}
