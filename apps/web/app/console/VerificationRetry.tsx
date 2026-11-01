'use client';
import {useEffect,useRef,useState} from 'react';
import {useExperience} from './Experience';
type API=(path:string,method?:string,data?:unknown)=>Promise<any>;
export default function VerificationRetry({assetId,challengeId,api,onVerified,onRunning,disabled=false}:{assetId:string;challengeId:string;api:API;onVerified:()=>Promise<void>;onRunning:(running:boolean)=>void;disabled?:boolean}){
 const {t}=useExperience();const [running,setRunning]=useState(false),[attempts,setAttempts]=useState(0),[message,setMessage]=useState('');
 const generation=useRef(0),timer=useRef<ReturnType<typeof setTimeout>|null>(null);
 const latest=useRef({api,onVerified,onRunning});latest.current={api,onVerified,onRunning};
 useEffect(()=>()=>{generation.current++;if(timer.current)clearTimeout(timer.current);latest.current.onRunning(false)},[assetId,challengeId]);
 function stop(){generation.current++;if(timer.current)clearTimeout(timer.current);setRunning(false);latest.current.onRunning(false);setMessage(t('Automatic checks stopped.','تم إيقاف المحاولات التلقائية.'))}
 function start(){const id=++generation.current;setRunning(true);setAttempts(0);setMessage('');latest.current.onRunning(true);
  const schedule=(count:number)=>{timer.current=setTimeout(async()=>{
   if(id!==generation.current)return;setAttempts(count);let verified=false;
   try{await latest.current.api(`/assets/${assetId}/verify/${challengeId}`,'POST');if(id!==generation.current)return;verified=true;setRunning(false);latest.current.onRunning(false);setMessage(t('Ownership verified. No assessment was started.','تم إثبات الملكية. لم يبدأ أي فحص أمني.'));await latest.current.onVerified();}
   catch(error){if(id!==generation.current)return;if(verified){setMessage(t('Ownership verified, but workspace refresh failed. Refresh the page; no assessment was started.','تم إثبات الملكية لكن تعذّر تحديث مساحة العمل. حدّث الصفحة؛ لم يبدأ فحص أمني.'));return;}setMessage(error instanceof Error?error.message:t('Verification could not complete.','تعذّر إكمال التحقق.'));if(count<3)schedule(count+1);else{setRunning(false);latest.current.onRunning(false);}}
  },30000)};schedule(1);
 }
 return <div className="verification-retry"><p className="subtle">{t('Waiting for DNS? Opt in to at most 3 ownership checks, 30 seconds apart. Closing this page stops future attempts.','تنتظر انتشار DNS؟ يمكنك تشغيل 3 محاولات تحقق كحد أقصى، بفاصل 30 ثانية. إغلاق الصفحة يوقف المحاولات التالية.')}</p><button type="button" disabled={disabled&&!running} onClick={running?stop:start}>{running?t('Stop automatic checks','إيقاف التحقق التلقائي'):t('Retry ownership automatically','إعادة التحقق تلقائيًا')}</button>{running&&<p role="status">{t('Waiting for the next ownership check','انتظار محاولة التحقق التالية')} · {attempts}/3</p>}{message&&<p role="status">{message}</p>}</div>
}
