'use client';
import {useEffect,useState} from 'react';
import type {FirebaseWebConfig} from '../../lib/firebase-client';
type API=(path:string,method?:string,data?:unknown)=>Promise<any>;
export default function FirebasePanel({api,account=false,onComplete}:{api:API;account?:boolean;onComplete:()=>Promise<void>}){
 const [config,setConfig]=useState<FirebaseWebConfig|null>(null),[linked,setLinked]=useState(false),[mode,setMode]=useState('login'),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[localPassword,setLocalPassword]=useState(''),[mfaCode,setMfaCode]=useState(''),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('');
 useEffect(()=>{let active=true;api('/auth/firebase/config').then(r=>{if(active&&r.enabled)setConfig(r.config)}).catch(()=>{if(active)setError('Firebase configuration is unavailable. Local sign-in remains available.')});if(account)api('/auth/firebase/status').then(r=>{if(active)setLinked(r.linked)}).catch(()=>{if(active)setError('Unable to load linked identity.')});return()=>{active=false}},[api,account]);
 async function run(fn:()=>Promise<void>){setBusy(true);setError('');setMessage('');try{await fn()}catch(e){const {friendlyError}=await import('../../lib/firebase-client');setError(friendlyError(e))}finally{setBusy(false);setPassword('');setLocalPassword('');setMfaCode('')}}
 async function signIn(provider:'google'|'email'){
  if(!config)return;
  await run(async()=>{
   const {authenticate}=await import('../../lib/firebase-client');
   await authenticate(config,provider,email,password,mode==='create'&&!account,async id_token=>{
    if(account){await api('/auth/firebase/link','POST',{id_token,current_password:localPassword,...(mfaCode?{mfa_code:mfaCode}:{})});setLinked(true);setMessage('Linked. Website ownership and workspace permissions are unchanged.')}
    else{
     if(mode==='create')await api('/auth/firebase/register','POST',{id_token,recovery_password:localPassword});
     await api('/auth/firebase/login','POST',{id_token,...(mfaCode?{mfa_code:mfaCode}:{})});await onComplete();
    }
   });
  });
 }
 if(!config)return account?<p role="status">{error||'Firebase is not configured on this server. Your local account remains available.'}</p>:error?<p role="status">{error}</p>:null;
 return <section aria-label="Firebase identity" className="glass panel" style={{marginTop:20}}><h3>{account?'Connected identity':'Continue with Firebase'}</h3><p className="subtle">{account?'Link your current account after confirming your AEGIS password.':'Existing AEGIS users: sign in locally first, then link from Account security. New users: select Create account.'}</p>{error&&<p role="alert" className="error">{error}</p>}{message&&<p role="status">{message}</p>}
 {<label className="form">Authenticator or recovery code (if enabled)<input autoComplete="one-time-code" maxLength={64} value={mfaCode} onChange={e=>setMfaCode(e.target.value)}/></label>}{!account&&<label className="form">Firebase action<select value={mode} disabled={busy} onChange={e=>setMode(e.target.value)}><option value="login">Sign in to linked account</option><option value="create">Create a new AEGIS account</option></select></label>}
 {(account||mode==='create')&&<label className="form">{account?'Current AEGIS password':'New AEGIS recovery password · minimum 12 characters'}<input type="password" value={localPassword} minLength={12} maxLength={128} autoComplete={account?'current-password':'new-password'} onChange={e=>setLocalPassword(e.target.value)}/></label>}
 {linked&&account?<><p>Firebase identity linked.</p><button disabled={busy||localPassword.length<12} onClick={()=>run(async()=>{await api('/auth/firebase/link','DELETE',{current_password:localPassword,...(mfaCode?{mfa_code:mfaCode}:{})});window.location.reload()})}>Unlink & sign out all sessions</button></>:<><button disabled={busy||((account||mode==='create')&&localPassword.length<12)} onClick={()=>signIn('google')}>{busy?'Please wait…':account?'Link Google identity':'Continue with Google'}</button><details><summary>Use Firebase email and password</summary><form className="form" onSubmit={e=>{e.preventDefault();signIn('email')}}><label>Firebase email<input type="email" required value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email"/></label><label>Firebase password<input type="password" required minLength={mode==='create'?12:1} value={password} onChange={e=>setPassword(e.target.value)} autoComplete={mode==='create'?'new-password':'current-password'}/></label><button disabled={busy||((account||mode==='create')&&localPassword.length<12)}>Continue with email</button><button type="button" disabled={busy||!email} onClick={()=>run(async()=>{const {resetFirebasePassword}=await import('../../lib/firebase-client');await resetFirebasePassword(config,email);setMessage('If eligible, a Firebase password-reset email will arrive. This does not change your AEGIS recovery password.')})}>Reset Firebase password</button></form></details></>}
 <p className="subtle">A Firebase identity does not authorize website assessments or changes. AEGIS sessions last 15 minutes; tokens are not saved in browser storage.</p></section>
}
