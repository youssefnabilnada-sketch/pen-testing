'use client';
import {useEffect,useState} from 'react';
import {authenticate,resetFirebasePassword,friendlyError,googleRedirectReady,beginGoogleRedirect,finishGoogleRedirect} from '../../lib/firebase-client';
import type {GoogleRedirectIdentity} from '../../lib/firebase-client';
import type {FirebaseWebConfig} from '../../lib/firebase-client';
import {useExperience} from './Experience';
type API=(path:string,method?:string,data?:unknown)=>Promise<any>;
export default function FirebasePanel({api,account=false,allowCreate=true,compact=false,initialMode='login',onComplete}:{api:API;account?:boolean;allowCreate?:boolean;compact?:boolean;initialMode?:'login'|'create';onComplete:()=>Promise<void>}){
 const {t}=useExperience();
 const [config,setConfig]=useState<FirebaseWebConfig|null>(null),[linked,setLinked]=useState(false),[mode,setMode]=useState(initialMode),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[localPassword,setLocalPassword]=useState(''),[mfaCode,setMfaCode]=useState(''),[busy,setBusy]=useState(false),[showRecovery,setShowRecovery]=useState(false),[redirectIdentity,setRedirectIdentity]=useState<GoogleRedirectIdentity|null>(null),[message,setMessage]=useState(''),[error,setError]=useState('');
 useEffect(()=>{let active=true;api('/auth/firebase/config').then(r=>{if(active&&r.enabled){
  setConfig(r.config);
  if(googleRedirectReady(r.config)){
   void finishGoogleRedirect(r.config).then(identity=>{
    if(active&&identity)setRedirectIdentity(identity);
   }).catch(e=>{if(active)setError(friendlyError(e))});
  }
 }}).catch(()=>{if(active)setError('Firebase sign-in settings could not be checked because the account API is unavailable. This does not mean Firebase credentials are missing.')});if(account)api('/auth/firebase/status').then(r=>{if(active)setLinked(r.linked)}).catch(()=>{if(active)setError('Unable to load linked identity.')});return()=>{active=false}},[api,account]);
 async function run(fn:()=>Promise<void>){setBusy(true);setError('');setMessage('');try{await fn()}catch(e){setError(friendlyError(e))}finally{setBusy(false);setPassword('');setLocalPassword('');setMfaCode('')}}
 async function signIn(provider:'google'|'email'){
  if(!config)return;
  if(provider==='google'&&googleRedirectReady(config)){
   setError('');setMessage('');setBusy(true);
   try{await beginGoogleRedirect(config)}
   catch(e){setError(friendlyError(e));setBusy(false)}
   return;
  }
  await run(async()=>{
   // Keep popup creation on the user's activation turn, without lazy imports.
   await authenticate(config,provider,email,password,mode==='create'&&!account,async id_token=>{
    if(account){await api('/auth/firebase/link','POST',{id_token,current_password:localPassword,...(mfaCode?{mfa_code:mfaCode}:{})});setLinked(true);setMessage('Linked. Website ownership and workspace permissions are unchanged.')}
    else{
     if(mode==='create')await api('/auth/firebase/register','POST',{id_token,recovery_password:localPassword});
     await api('/auth/firebase/login','POST',{id_token,...(mfaCode?{mfa_code:mfaCode}:{})});await onComplete();
    }
   });
  });
 }
 async function completeRedirect(choice:'login'|'create'|'link'){
  if(!redirectIdentity)return;
  await run(async()=>{
   const id_token=redirectIdentity.idToken;
   if(choice==='link'){
    await api('/auth/firebase/link','POST',{id_token,current_password:localPassword,...(mfaCode?{mfa_code:mfaCode}:{})});
    setRedirectIdentity(null);setLinked(true);setMessage('Google identity linked. Workspace permissions are unchanged.');
   }else{
    if(choice==='create')await api('/auth/firebase/register','POST',{id_token,recovery_password:localPassword});
    await api('/auth/firebase/login','POST',{id_token,...(mfaCode?{mfa_code:mfaCode}:{})});
    setRedirectIdentity(null);
    await onComplete();
   }
  });
 }
 if(redirectIdentity){
  return <div className="auth-google-redirect-result">
   <p role="status">{t('Google verified. Finish your AEGIS account action here without a popup.','تم التحقق من Google. أكمل دخول أو إنشاء حساب AEGIS هنا بدون نوافذ منبثقة.')}</p>
   {redirectIdentity.email&&<p className="auth-google-caption">{redirectIdentity.email}</p>}
   {!account&&<button type="button" disabled={busy} onClick={()=>void completeRedirect('login')}>{t('Sign in to linked AEGIS account','الدخول لحساب AEGIS المرتبط')}</button>}
   <label>{account?t('Current AEGIS password','كلمة مرور AEGIS الحالية'):t('New account recovery password · at least 12 characters','كلمة مرور استرداد الحساب الجديد · 12 حرفًا على الأقل')}
    <input type="password" autoComplete={account?'current-password':'new-password'} minLength={12} maxLength={128} value={localPassword} onChange={e=>setLocalPassword(e.target.value)}/>
   </label>
   {account&&<label>{t('Authenticator code (if enabled)','رمز المصادقة (إن كان مفعّلًا)')}<input type="text" autoComplete="one-time-code" value={mfaCode} onChange={e=>setMfaCode(e.target.value)}/></label>}
   <button type="button" disabled={busy||localPassword.length<12} onClick={()=>void completeRedirect(account?'link':'create')}>{account?t('Link Google identity','ربط حساب Google'):t('Create a new AEGIS account','إنشاء حساب AEGIS جديد')}</button>
   {error&&<p role="alert" className="error auth-feedback">{error}</p>}
   {message&&<p role="status" className="notice auth-feedback">{message}</p>}
   <p className="auth-google-caption">{t('Finish promptly. Google verification expires for this step after five minutes. No recovery password is saved in your browser.','أكمل خلال خمس دقائق من التحقق من Google. لن يتم حفظ كلمة مرور الاسترداد في المتصفح.')}</p>
  </div>;
 }
 if(compact){
  const isCreating=mode==='create'&&!account;
  const redirectAvailable=!!config&&googleRedirectReady(config);
  const googleMark=<svg aria-hidden="true" className="google-mark" width="19" height="19" viewBox="0 0 48 48" focusable="false">
     <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.75 9.5 24 9.5Z"/>
     <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.29 5.48-4.83 7.18l7.73 6C44.34 38.04 46.98 31.9 46.98 24.55Z"/>
     <path fill="#FBBC05" d="M10.53 28.59A14.41 14.41 0 0 1 9.75 24c0-1.6.27-3.14.76-4.59l-7.98-6.2A23.95 23.95 0 0 0 0 24c0 3.87.93 7.52 2.56 10.78l7.97-6.19Z"/>
     <path fill="#34A853" d="M24 48c6.47 0 11.9-2.13 15.86-5.8l-7.73-6C29.98 37.65 27.23 38.5 24 38.5c-6.25 0-11.57-4.22-13.47-9.91l-7.97 6.19C6.51 42.62 14.62 48 24 48Z"/>
    </svg>;
  return <div className="auth-google-signin">
   {config?<div className={isCreating?'auth-google-create':undefined}>
    {isCreating&&showRecovery&&!redirectAvailable&&<div className="auth-google-recovery">
     <label htmlFor="aegis-google-recovery-password">{t('Account recovery password','كلمة مرور استرداد الحساب')}
      <input id="aegis-google-recovery-password" type="password" autoComplete="new-password" minLength={12} maxLength={128} required value={localPassword} onChange={e=>setLocalPassword(e.target.value)} placeholder={t('At least 12 characters','12 حرفًا على الأقل')}/>
     </label>
     <p>{t('This password lets you recover your AEGIS account if Google is unavailable.','تساعدك كلمة المرور دي تسترد حساب AEGIS لو Google غير متاح.')}</p>
    </div>}
    <button type="button" className="google-signin-button" disabled={busy||(!redirectAvailable&&isCreating&&showRecovery&&localPassword.length<12)} aria-expanded={isCreating?showRecovery:undefined} onClick={()=>{
      if(isCreating&&!redirectAvailable&&!showRecovery){setShowRecovery(true);return;}
      void signIn('google');
    }}>
     {googleMark}
     <span>{busy?t('Connecting securely…','جاري الاتصال بأمان…'):isCreating&&showRecovery&&!redirectAvailable?t('Create account with Google','إنشاء حساب باستخدام Google'):isCreating?t('Continue with Google','المتابعة باستخدام Google'):t('Sign in with Google','تسجيل الدخول باستخدام Google')}</span>
    </button>
    {isCreating&&showRecovery&&!redirectAvailable?<button type="button" className="auth-google-back" disabled={busy} onClick={()=>{setShowRecovery(false);setLocalPassword('');setError('')}}>{t('Use email instead','التسجيل بالبريد بدلًا من Google')}</button>:null}
    <p className="auth-google-caption">{redirectAvailable?t('Google continues on this page without popup windows.','Google هيكمل على نفس الصفحة من غير نافذة منبثقة.'):isCreating?t('A recovery password is required for Google registration.','التسجيل باستخدام Google يتطلب كلمة مرور لاسترداد الحساب.'):t('For accounts linked to Google in Account security.','للحسابات المرتبطة بـGoogle من إعدادات أمان الحساب.')}</p>
   </div>:<p role="status" className="auth-google-unavailable">{error||t('Google sign-in is not available yet. Use your AEGIS password.','تسجيل الدخول باستخدام Google غير متاح حاليًا. استخدم كلمة مرور AEGIS.')}</p>}
   {config&&error&&<p role="alert" className="error auth-feedback">{error}</p>}
   {config&&message&&<p role="status" className="notice auth-feedback">{message}</p>}
  </div>;
 }
 if(!config)return account?<p role="status">{error||'Google identity is not configured on this server. Your AEGIS password remains available.'}</p>:error?<p role="status">{error}</p>:null;
 return <section aria-label="Firebase identity" className="glass panel" style={{marginTop:20}}><h3>{account?'Connected identity':'Continue with Firebase'}</h3><p className="subtle">{account?'Link your current account after confirming your AEGIS password.':allowCreate?'Existing AEGIS users: sign in locally first, then link from Account security. New users: select Create account.':'Only linked AEGIS accounts can use Firebase sign-in. Sign in with your AEGIS password first, then link Google in Account security.'}</p>{error&&<p role="alert" className="error">{error}</p>}{message&&<p role="status">{message}</p>}
 {<label className="form">Authenticator or recovery code (if enabled)<input autoComplete="one-time-code" maxLength={64} value={mfaCode} onChange={e=>setMfaCode(e.target.value)}/></label>}{!account&&allowCreate&&<label className="form">Firebase action<select value={mode} disabled={busy} onChange={e=>setMode(e.target.value==='create'?'create':'login')}><option value="login">Sign in to linked account</option><option value="create">Create a new AEGIS account</option></select></label>}
 {(account||mode==='create')&&<label className="form">{account?'Current AEGIS password':'New AEGIS recovery password · minimum 12 characters'}<input type="password" value={localPassword} minLength={12} maxLength={128} autoComplete={account?'current-password':'new-password'} onChange={e=>setLocalPassword(e.target.value)}/></label>}
 {linked&&account?<><p>Firebase identity linked.</p><button disabled={busy||localPassword.length<12} onClick={()=>run(async()=>{await api('/auth/firebase/link','DELETE',{current_password:localPassword,...(mfaCode?{mfa_code:mfaCode}:{})});window.location.reload()})}>Unlink & sign out all sessions</button></>:<><button disabled={busy||((account||mode==='create')&&localPassword.length<12)} onClick={()=>signIn('google')}>{busy?'Please wait…':account?'Link Google identity':'Continue with Google'}</button><details><summary>Use Firebase email and password</summary><form className="form" onSubmit={e=>{e.preventDefault();signIn('email')}}><label>Firebase email<input type="email" required value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email"/></label><label>Firebase password<input type="password" required minLength={mode==='create'?12:1} value={password} onChange={e=>setPassword(e.target.value)} autoComplete={mode==='create'?'new-password':'current-password'}/></label><button disabled={busy||((account||mode==='create')&&localPassword.length<12)}>Continue with email</button><button type="button" disabled={busy||!email} onClick={()=>run(async()=>{await resetFirebasePassword(config,email);setMessage('If eligible, a Firebase password-reset email will arrive. This does not change your AEGIS recovery password.')})}>Reset Firebase password</button></form></details></>}
 <p className="subtle">A Firebase identity does not authorize website assessments or changes. AEGIS sessions last 15 minutes; tokens are not saved in browser storage.</p></section>
}
