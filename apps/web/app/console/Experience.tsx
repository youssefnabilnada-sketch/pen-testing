'use client';
import {createContext,useContext,useEffect,useState,ReactNode} from 'react';
type Language='en'|'ar';
const Context=createContext({language:'en' as Language,t:(en:string,ar:string)=>en});
export function Experience({children}:{children:ReactNode}){
 const [language,setLanguage]=useState<Language>('en');
 useEffect(()=>{try{if(localStorage.getItem('aegis-language')==='ar')setLanguage('ar')}catch{}},[]);
 function change(){const next=language==='en'?'ar':'en';setLanguage(next);try{localStorage.setItem('aegis-language',next)}catch{}}
 return <Context.Provider value={{language,t:(en,ar)=>language==='ar'?ar:en}}><div dir={language==='ar'?'rtl':'ltr'} lang={language} className="experience"><button className="language-toggle" onClick={change} aria-label={language==='ar'?'Switch to English':'التبديل إلى العربية'}>{language==='ar'?'English':'العربية'}</button>{children}</div></Context.Provider>;
}
export const useExperience=()=>useContext(Context);
export function SafetyJourney(){const {t}=useExperience();return <aside className="workflow-guide" aria-label={t('How remediation works','خطوات الإصلاح')}><strong>{t('A clear path to a verified fix','طريق واضح لإصلاح تم التحقق منه')}</strong><ol>{[['Understand the evidence','افهم الدليل'],['Review the proposed change','راجع التعديل المقترح'],['Approve scope and rollback plan','وافق على النطاق وخطة التراجع'],['Engineer applies the approved change','المهندس ينفذ التعديل المعتمد'],['Retest the full supported profile','أعد الفحص الكامل للاختبارات المدعومة']].map(([en,ar])=><li key={en}>{t(en,ar)}</li>)}</ol><p>{t('These are workflow steps, not completed actions. A suggestion or approval does not mean a fix was applied.','هذه خطوات العمل وليست إجراءات مكتملة. الاقتراح أو الموافقة لا يعنيان تنفيذ الإصلاح.')}</p></aside>}
