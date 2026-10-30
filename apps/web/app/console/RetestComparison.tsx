'use client';
import {useExperience} from './Experience';
type Comparison={resolved?:string[];unresolved?:string[];new?:string[];unverified?:{rule:string;reason:string}[]};
export default function RetestComparison({comparison}:{comparison:Comparison}){
 const {t}=useExperience();
 const fields:[keyof Comparison,string,string][]=[['resolved','Resolved by supported checks','لم تعد تظهر في الاختبارات المدعومة'],['unresolved','Still detected','ما زالت تظهر'],['new','New observations','ملاحظات جديدة'],['unverified','Not verified','لم يتم التحقق منها']];
 return <section aria-label={t('Retest comparison','مقارنة إعادة الفحص')}><div className="retest-comparison">{fields.map(([key,en,ar])=><div key={key} className={'comparison-card '+key}><span>{t(en,ar)}</span><strong>{Array.isArray(comparison[key])?comparison[key]!.length:'—'}</strong><small>{Array.isArray(comparison[key])?t('Recorded by reassessment','مسجلة في إعادة الفحص'):t('Result not available','النتيجة غير متاحة')}</small></div>)}</div><p className="subtle">{t('A resolved observation applies only to the tested scope and supported check. It is not a guarantee that the website has no other vulnerabilities.','اختفاء الملاحظة يخص النطاق والاختبار المدعوم فقط، ولا يضمن خلو الموقع من ثغرات أخرى.')}</p></section>
}
