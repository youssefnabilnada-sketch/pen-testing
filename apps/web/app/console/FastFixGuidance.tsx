'use client';
import {useExperience} from './Experience';
import {useEffect,useState} from 'react';
import {ArrowRight,CheckCircle2,Download,FileCode2,LockKeyhole,ShieldAlert,ShieldCheck,Wrench} from 'lucide-react';

type API=(p:string,m?:string,d?:unknown)=>Promise<any>;
type Guidance={
 mode:string;root_cause:string;recommended_action:string;platform_guidance:string;approval:string;
 method?:string;capabilities?:{reads_customer_source:boolean;generates_patch:boolean;deploys:boolean;};
 optional_supported_adapter?:{name:string;availability:string;limitations:string};
 compatibility_risks:string[];validation_required:string[];backup_scope:string;
};
const platforms=['unknown','github','netlify','gitlab','wordpress','woocommerce','joomla','drupal','php','laravel','python','django','fastapi','node','express','nextjs','react','vue','nuxt','java','spring','aspnet','rails','static','cpanel','plesk','cloud','shopify','wix','webflow','custom'];
export default function FastFixGuidance({api,findingId}:{api:API;findingId:string}){
 const {t}=useExperience();
 const [platform,setPlatform]=useState('unknown'),[plan,setPlan]=useState<Guidance|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(false),[opened,setOpened]=useState(false);
 useEffect(()=>{let active=true;setPlan(null);setError('');if(!opened)return;setLoading(true);api(`/findings/${findingId}/fastfix?platform=${platform}`).then(p=>{if(active)setPlan(p)}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[api,findingId,platform,opened]);
 function download(){if(!plan)return;const url=URL.createObjectURL(new Blob([JSON.stringify(plan,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='aegis-remediation-guidance.json';a.click();URL.revokeObjectURL(url)}
 const repoAdapter=Boolean(plan?.optional_supported_adapter);
 return <div className="fastfix-entry">
  <button type="button" className="fastfix-launch" onClick={()=>setOpened(v=>!v)}><Wrench size={15}/>{opened?t('Close FastFix guidance','إغلاق إرشادات الإصلاح'):t('Choose a remediation path','اختر طريقة الإصلاح')}<ArrowRight size={14}/></button>
  {opened&&<section aria-label="FastFix guidance" className="fastfix-guidance">
   <header><span className="fastfix-eyebrow"><ShieldCheck size={15}/> FASTFIX · {t('CONTROLLED REMEDIATION','إصلاح بموافقة')}</span>
    <h4>{t('What can AEGIS actually fix?','إيه اللي يقدر AEGIS يصلحه فعليًا؟')}</h4>
    <p>{t('An observed issue does not grant access to code, hosting or production. We show the required access before proposing a change.','اكتشاف المشكلة لا يمنحنا صلاحية كود الموقع أو الاستضافة أو الإنتاج. بنوضح الوصول المطلوب قبل اقتراح أي تعديل.')}</p>
   </header>
   <label>{t('Your platform (not automatically verified)','منصة موقعك (لم يتم التحقق منها تلقائيًا)')}
    <select value={platform} onChange={e=>setPlatform(e.target.value)}>{platforms.map(p=><option key={p} value={p}>{p==='unknown'?'Not sure':p}</option>)}</select>
   </label>
   {loading&&<p role="status">{t('Loading evidence-based guidance…','جاري تحميل إرشادات مبنية على الأدلة…')}</p>}
   {error&&<p role="alert">{error}</p>}
   {plan&&<>
    <div className="fastfix-truth"><ShieldAlert size={20}/><div><strong>{t('Guidance only · no change applied','إرشادات فقط · لم يُنفذ تعديل')}</strong>
     <p>{t('This endpoint does not read your source code, deploy a patch, or prove the issue resolved.','الخدمة دي لا تقرأ كود موقعك ولا تنشر تعديلًا ولا تثبت حل المشكلة.')}</p></div></div>
    <div className="fastfix-access-grid">
     <div><FileCode2 size={18}/><strong>{t('Does AEGIS have the source code?','هل AEGIS معاه كود الموقع؟')}</strong>
      <span>{plan.capabilities?.reads_customer_source?t('Access reported; scope must still be reviewed','يوجد وصول مُعلن؛ النطاق يحتاج مراجعة'):t('No source access through this guidance','لا يوجد وصول للكود من خلال الإرشادات دي')}</span></div>
     <div><Wrench size={18}/><strong>{t('Can it apply a change now?','هل يقدر ينفذ تعديل دلوقتي؟')}</strong>
      <span>{plan.capabilities?.deploys?t('Separate approval still required','الموافقة المنفصلة مطلوبة'):t('No · approval and an implementation path required','لا · لازم موافقة وطريقة تنفيذ فعلية')}</span></div>
     <div><ShieldCheck size={18}/><strong>{t('Fix verified by retest?','هل الإصلاح اتأكد بإعادة الفحص؟')}</strong>
      <span>{t('No · separately authorized retest required','لا · لازم إعادة فحص بتصريح منفصل')}</span></div>
    </div>
    <div className="fastfix-implementation">
     <h5>{t('Choose the real implementation route','حدد طريقة التنفيذ الحقيقية')}</h5>
     <div className="fastfix-route">
      <span>01</span><div><strong>{t('Hosting or CDN settings','إعدادات الاستضافة أو CDN')}</strong>
       <p>{t('For supported response-header issues, the owner can review a hosting configuration change without giving AEGIS the entire application source.','في مشاكل هيدرز الاستجابة المدعومة، صاحب الموقع يقدر يراجع تعديل إعدادات الاستضافة بدون تسليم كود التطبيق بالكامل.')}</p></div></div>
     <div className="fastfix-route">
      <span>02</span><div><strong>{t('Authorized repository & reviewed PR','ربط مستودع بتصريح وPull Request للمراجعة')}</strong>
       <p>{repoAdapter?t('This finding has a limited optional adapter. It can propose a specific reviewed configuration change only after separate repository connection, authorization and approval.','الملاحظة دي ليها مسار محدود لاقتراح تعديل إعدادات بمراجعة، لكن بعد ربط المستودع والتصريح والموافقة بشكل منفصل.'):t('No supported automatic patch adapter is established for this finding and platform. A connected repository does not by itself mean a safe fix exists.','لا يوجد مسار تعديل آلي مدعوم لهذه المشكلة والمنصة. ربط المستودع وحده لا يعني إن فيه إصلاح آمن جاهز.')}</p></div></div>
     <div className="fastfix-route">
      <span>03</span><div><strong>{t('Developer handoff','تسليم الإرشادات للمطوّر')}</strong>
       <p>{t('If code or server changes are needed, the authorized developer implements them after reviewing impact and backups, then AEGIS can retest only with fresh authorization.','لو المشكلة محتاجة كود أو تعديل سيرفر، المطور المخوّل ينفذها بعد مراجعة التأثير والنسخة الاحتياطية، وبعدها AEGIS يعيد الفحص بتصريح جديد.')}</p></div></div>
    </div>
    {repoAdapter&&<p className="fastfix-adapter"><LockKeyhole size={14}/>{plan.optional_supported_adapter?.availability} — {plan.optional_supported_adapter?.limitations}</p>}
    <section className="fastfix-proposal"><h5>{t('Evidence-based recommendation','اقتراح الإصلاح المبني على الأدلة')}</h5>
     <p>{plan.root_cause}</p><strong>{t('Recommended next action','الخطوة المقترحة')}</strong><p>{plan.recommended_action}</p>
     <strong>{t('Your selected platform','المنصة المختارة')}</strong><p>{plan.platform_guidance}</p>
     <p>{plan.approval}</p>
     <details className="evidence-detail"><summary>{t('Guidance provenance and limitations','مصدر الإرشادات وحدودها')}</summary><p>{plan.mode}</p></details>
    </section>
    <details className="evidence-detail fastfix-validation"><summary><CheckCircle2 size={14}/>{t('Required tests and rollback before marking fixed','الاختبارات والتراجع قبل تأكيد الإصلاح')}</summary>
     <h5>{t('Compatibility review','مراجعة التوافق')}</h5><ul>{(plan.compatibility_risks||[]).map(r=><li key={r}>{r}</li>)}</ul>
     <h5>{t('Required validation','التحقق المطلوب')}</h5><ul>{(plan.validation_required||[]).map(r=><li key={r}>{r}</li>)}</ul><p>{plan.backup_scope}</p>
    </details>
    <p className="fastfix-warning">{t('No fix has been applied or verified. Customer application tests and staging checks have not been performed by this guidance.','لم يتم تطبيق أو التحقق من أي إصلاح. إرشادات FastFix لا تختبر التطبيق أو بيئة التجربة تلقائيًا.')}</p>
    <button type="button" onClick={download} className="fastfix-download"><Download size={15}/>{t('Download developer handoff','تنزيل إرشادات المهندس')}</button>
   </>}
  </section>}
 </div>;
}
