'use client';
import {useEffect,useState,type FormEvent} from 'react';
import Link from 'next/link';
import {ShieldCheck,LockKeyhole,CheckCircle2,Eye,EyeOff,ArrowRight,Mail,KeyRound} from 'lucide-react';
import {useExperience} from './Experience';
import FirebasePanel from './FirebasePanel';

type AuthMode='login'|'register'|'verify'|'reset'|'reset-request';
type API=(path:string,method?:string,data?:unknown)=>Promise<any>;
type Props={
 mode:string; email:string; password:string; mfaCode:string; token:string;
 busy:boolean;error:string;notice:string;
 setEmail:(value:string)=>void;setPassword:(value:string)=>void;
 setMfaCode:(value:string)=>void;setToken:(value:string)=>void;
 onNavigate:(mode:AuthMode)=>void;onSubmit:(event:FormEvent<HTMLFormElement>)=>void|Promise<void>;
 api:API;onComplete:()=>Promise<void>;
};
const headings:Record<AuthMode,[string,string]>={
 login:['Welcome back.','مرحبًا بعودتك.'],
 register:['Create your account.','أنشئ حسابك.'],
 verify:['Verify your email.','تحقق من بريدك الإلكتروني.'],
 reset:['Set a new password.','اختر كلمة مرور جديدة.'],
 'reset-request':['Recover your account.','استرد حسابك.']
};
export default function GuestAuth({
 mode,email,password,mfaCode,token,busy,error,notice,
 setEmail,setPassword,setMfaCode,setToken,onNavigate,onSubmit,api,onComplete
}:Props){
 const {t}=useExperience();
 const [showPassword,setShowPassword]=useState(false);
 const [registrationOpen,setRegistrationOpen]=useState(false);
 const [registrationChecked,setRegistrationChecked]=useState(false);
 useEffect(()=>{
  let active=true;
  api('/auth/registration-status')
   .then(status=>{if(active)setRegistrationOpen(status?.enabled===true)})
   .catch(()=>{if(active)setRegistrationOpen(false)})
   .finally(()=>{if(active)setRegistrationChecked(true)});
  return()=>{active=false};
 },[api]);
 const heading=headings[mode as AuthMode]||headings.login;
 const isLogin=mode==='login',isRegister=mode==='register',isVerify=mode==='verify',isReset=mode==='reset';
 const needsEmail=isLogin||isRegister||mode==='reset-request';
 const needsPassword=isLogin||isRegister||isReset;
 const go=(next:AuthMode)=>{setShowPassword(false);onNavigate(next)};
 return <main className="auth auth-modern">
  <section className="auth-intro" aria-label={t('About AEGIS Security Cloud','عن AEGIS Security Cloud')}>
   <Link className="brand auth-brand" href="/"><ShieldCheck aria-hidden="true"/> AEGIS <span>SECURITY CLOUD</span></Link>
   <span className="auth-eyebrow">{t('YOUR SECURITY WORKSPACE','مساحة عمل الأمان')}</span>
   <h1>{t('Security, made','الأمان، أصبح')}<span>{t('simple.','أسهل.')}</span></h1>
   <p className="auth-intro-lead">{t('One clear place to verify your websites, understand security findings and manage approved fixes.','مكان واحد لإثبات ملكية مواقعك وفهم نتائج الأمان ومتابعة الإصلاحات المعتمدة.')}</p>
   <div className="auth-assurance" aria-label={t('Security principles','مبادئ الأمان')}>
    <div><CheckCircle2 size={18} aria-hidden="true"/><span>{t('Verified ownership before any assessment','إثبات الملكية قبل أي فحص')}</span></div>
    <div><CheckCircle2 size={18} aria-hidden="true"/><span>{t('Every change requires your approval','كل تغيير يتطلب موافقتك')}</span></div>
    <div><LockKeyhole size={18} aria-hidden="true"/><span>{t('Your workspace is private by design','مساحة عملك خاصة ومحمية')}</span></div>
   </div>
   <Link href="/guides" className="auth-tutorials-link">{t('Watch website verification videos before signing in','شاهد فيديوهات إثبات الملكية قبل تسجيل الدخول')} <ArrowRight size={15}/></Link>
  </section>
  <section className="glass auth-card auth-card-modern" aria-label={t('Account access','الدخول للحساب')}>
   <header className="auth-card-head">
    <p className="eyebrow">{t('ACCOUNT ACCESS','دخول الحساب')}</p>
    <h2>{t(heading[0],heading[1])}</h2>
    <p>{isLogin
     ?t('Sign in to continue to your workspace.','سجّل دخولك للمتابعة إلى لوحة التحكم.')
     :isVerify
     ?t('Enter the one-time verification token from your new AEGIS email.','أدخل رمز التفعيل من رسالة AEGIS الجديدة.')
     :mode==='reset-request'
     ?t('We will email a recovery link if this account is eligible.','سنرسل رابط استرداد للحساب المؤهل.')
     :isReset
     ?t('Enter your reset token and choose a new password.','أدخل رمز الاستعادة واختر كلمة مرور جديدة.')
     :registrationOpen
     ?t('Create your AEGIS account securely. Verify your email before adding a website.','أنشئ حسابك بأمان، ثم فعّل بريدك قبل إضافة موقع.')
     :t('New accounts are currently available only during approved launch access.','إنشاء الحسابات متاح حاليًا بعد موافقة الإطلاق فقط.')}
    </p>
   </header>
   {isLogin&&<p className="auth-guidance">{t('Use your exact AEGIS account email, including any +alias.','استخدم بريد حساب AEGIS بالكامل، بما فيه +alias إن وُجد.')}</p>}
   {isRegister&&!registrationChecked&&<p className="auth-release-note" role="status">{t('Checking registration availability…','جاري التحقق من إتاحة التسجيل…')}</p>}
   {isRegister&&registrationChecked&&!registrationOpen&&<p className="auth-release-note" role="status">{t('Public registration is not open yet. Already have an account? Sign in instead.','التسجيل العام لم يُفتح بعد. لديك حساب بالفعل؟ سجّل الدخول بدلًا من ذلك.')}</p>}
   {error&&<div role="alert" className="error auth-feedback">{error}</div>}
   {notice&&<div role="status" className="notice auth-feedback">{notice}</div>}
   <form className="form auth-form" onSubmit={onSubmit}>
    {needsEmail&&<label>{t('Email address','البريد الإلكتروني')}<input type="email" required value={email} autoComplete="email" onChange={e=>setEmail(e.target.value)} placeholder="name@example.com"/></label>}
    {needsPassword&&<label>{isLogin?t('Password','كلمة المرور'):t('Password · at least 12 characters','كلمة المرور · 12 حرفًا على الأقل')}
     <span className="auth-password">
      <input type={showPassword?'text':'password'} minLength={12} maxLength={128} required value={password} autoComplete={isLogin?'current-password':'new-password'} onChange={e=>setPassword(e.target.value)}/>
      <button type="button" className="auth-password-toggle" aria-label={showPassword?t('Hide password','إخفاء كلمة المرور'):t('Show password','إظهار كلمة المرور')} onClick={()=>setShowPassword(v=>!v)}>{showPassword?<EyeOff size={19} aria-hidden="true"/>:<Eye size={19} aria-hidden="true"/>}</button>
     </span>
    </label>}
    {isLogin&&<details className="auth-optional">
     <summary>{t('Using an authenticator? Add your code','تستخدم المصادقة الثنائية؟ أضف الرمز')}</summary>
     <label>{t('Authenticator or recovery code (if enabled)','رمز المصادقة أو الاسترداد (إذا كان مفعّلًا)')}<input autoComplete="one-time-code" maxLength={64} value={mfaCode} onChange={e=>setMfaCode(e.target.value)}/></label>
     <p>{t('Leave this empty unless you have enabled MFA. This is not your email verification token.','اتركها فارغة ما لم تكن فعّلت المصادقة الثنائية. هذا ليس رمز تفعيل البريد.')}</p>
    </details>}
    {(isVerify||isReset)&&<label>{t('One-time token from email','الرمز المرسل بالبريد الإلكتروني')}<input required autoComplete="off" value={token} onChange={e=>setToken(e.target.value)}/></label>}
    <button disabled={busy||(isRegister&&!registrationOpen)} className="primary auth-submit" type="submit">
     {busy?t('Please wait…','يرجى الانتظار…'):isLogin?t('Sign in','تسجيل الدخول'):isVerify?t('Verify email','تفعيل البريد'):isReset?t('Reset password','تغيير كلمة المرور'):mode==='reset-request'?t('Send recovery email','إرسال بريد الاسترداد'):t('Continue','متابعة')}
     {!busy&&<ArrowRight size={18} aria-hidden="true"/>}
    </button>
   </form>
   <nav className="auth-quick-links" aria-label={t('Account help','مساعدة الحساب')}>
    {isLogin?<><button type="button" onClick={()=>go('verify')}><Mail size={15} aria-hidden="true"/>{t('Verify email','تفعيل البريد')}</button>
     <button type="button" onClick={()=>go('reset-request')}><KeyRound size={15} aria-hidden="true"/>{t('Forgot password?','نسيت كلمة المرور؟')}</button></>
     :<button type="button" onClick={()=>go('login')}>{t('Back to sign in','العودة لتسجيل الدخول')}</button>}
    {mode==='reset-request'&&<button type="button" onClick={()=>go('reset')}>{t('I have a reset token','لدي رمز الاستعادة')}</button>}
    {isReset&&<button type="button" onClick={()=>go('reset-request')}>{t('Request a reset email','طلب بريد الاستعادة')}</button>}
   </nav>
   {isRegister&&registrationOpen&&<section className="auth-google-section" aria-label={t('Create with Google','إنشاء حساب باستخدام Google')}>
    <div className="auth-divider"><span>{t('or','أو')}</span></div>
    <FirebasePanel api={api} allowCreate initialMode="create" onComplete={onComplete}/>
   </section>}
   {isLogin&&<section className="auth-google-section" aria-label={t('Sign in with Google','تسجيل الدخول باستخدام Google')}>
    <div className="auth-divider"><span>{t('or','أو')}</span></div>
    <FirebasePanel api={api} allowCreate={false} compact onComplete={onComplete}/>
   </section>}
   <footer className="auth-card-footer">
    {isLogin?<p>{t('New to AEGIS?','جديد على AEGIS؟')} <button type="button" onClick={()=>go('register')}>{t('Register','التسجيل')}</button> <span>{registrationChecked?(registrationOpen?t('· Registration open','· التسجيل متاح الآن'):t('· Limited launch access','· الدخول الجديد محدود خلال الإطلاق')):null}</span></p>:<p>{t('Already have an account?','عندك حساب بالفعل؟')} <button type="button" onClick={()=>go('login')}>{t('Sign in','تسجيل الدخول')}</button></p>}
    <p className="auth-privacy"><LockKeyhole size={13} aria-hidden="true"/>{t('Protected access · No payment required','دخول محمي · بدون دفع')}</p>
   </footer>
  </section>
 </main>;
}
