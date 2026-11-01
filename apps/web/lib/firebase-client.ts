import {getApps,initializeApp,FirebaseOptions} from 'firebase/app';
import {initializeAuth,inMemoryPersistence,browserPopupRedirectResolver,GoogleAuthProvider,signInWithPopup,signInWithRedirect,getRedirectResult,signInWithEmailAndPassword,createUserWithEmailAndPassword,sendEmailVerification,sendPasswordResetEmail,signOut} from 'firebase/auth';
import {connectAuthEmulator} from 'firebase/auth';
import {firstPartyFirebaseConfig} from './firebase-first-party';
export type FirebaseWebConfig=FirebaseOptions & {emulatorUrl?:string};
const connectedEmulators=new WeakSet<object>();
function configureEmulator(auth:ReturnType<typeof initializeAuth>,config:FirebaseWebConfig){
 if(!config.emulatorUrl)return;
 if(typeof window==='undefined'||!['localhost','127.0.0.1'].includes(window.location.hostname)||config.projectId!=='demo-aegis'||config.emulatorUrl!=='http://127.0.0.1:9099')throw new Error('Emulator is restricted to local development.');
 if(!connectedEmulators.has(auth)){connectAuthEmulator(auth,config.emulatorUrl);connectedEmulators.add(auth)}
}
function aegisAuth(config:FirebaseWebConfig){
 const siteConfig=firstPartyFirebaseConfig(
  config,
  typeof window==='undefined'?'':window.location.hostname,
  {NEXT_PUBLIC_AEGIS_FIREBASE_FIRST_PARTY:process.env.NEXT_PUBLIC_AEGIS_FIREBASE_FIRST_PARTY,
   NEXT_PUBLIC_AEGIS_FIREBASE_HELPER_PROJECT_ID:process.env.NEXT_PUBLIC_AEGIS_FIREBASE_HELPER_PROJECT_ID}
 );
 const app=getApps().find(a=>a.name==='aegis-web')||initializeApp(siteConfig,'aegis-web');
 // No asynchronous setup between the click and Google popup (critical on iOS).
 const auth=initializeAuth(app,{persistence:inMemoryPersistence,popupRedirectResolver:browserPopupRedirectResolver});
 configureEmulator(auth,config);
 return auth;
}
export async function authenticate(config:FirebaseWebConfig,provider:'google'|'email',email:string,password:string,create:boolean,exchange:(token:string)=>Promise<void>){
 const auth=aegisAuth(config);
 try{
  let credential;
  if(provider==='google'){
   const google=new GoogleAuthProvider();google.setCustomParameters({prompt:'select_account'});
   credential=await signInWithPopup(auth,google);
  }else if(create){
   try{credential=await createUserWithEmailAndPassword(auth,email,password)}catch(e){
    if((e as {code?:string}).code!=='auth/email-already-in-use')throw e;
    credential=await signInWithEmailAndPassword(auth,email,password);
   }
  }else{credential=await signInWithEmailAndPassword(auth,email,password)}
  if(!credential.user.emailVerified){
   await sendEmailVerification(credential.user);
   throw new Error('Verification email sent. Open its link, then return and repeat this action. Your AEGIS account has not been created or linked yet.');
  }
  await exchange(await credential.user.getIdToken(true));
 }finally{await signOut(auth)}
}
/**
 * When the first-party Firebase OAuth helper is configured, use same-page
 * redirects instead of opening browser popups. No credentials or AEGIS recovery
 * password are ever saved to localStorage/sessionStorage.
 */
export function googleRedirectReady(config:FirebaseWebConfig):boolean{
 if(typeof window==='undefined')return false;
 const patched=firstPartyFirebaseConfig(config,window.location.hostname,{
  NEXT_PUBLIC_AEGIS_FIREBASE_FIRST_PARTY:process.env.NEXT_PUBLIC_AEGIS_FIREBASE_FIRST_PARTY,
  NEXT_PUBLIC_AEGIS_FIREBASE_HELPER_PROJECT_ID:process.env.NEXT_PUBLIC_AEGIS_FIREBASE_HELPER_PROJECT_ID
 });
 return patched.authDomain===window.location.hostname&&patched.projectId===config.projectId;
}

export function beginGoogleRedirect(config:FirebaseWebConfig):Promise<never>{
 if(!googleRedirectReady(config))return Promise.reject(new Error('Google browser redirect is not configured yet.'));
 const auth=aegisAuth(config);
 const provider=new GoogleAuthProvider();
 provider.setCustomParameters({prompt:'select_account'});
 // This is called directly from the click handler without awaited setup.
 return signInWithRedirect(auth,provider) as Promise<never>;
}

export type GoogleRedirectIdentity={idToken:string,email:string};
let resumePromise:Promise<GoogleRedirectIdentity|null>|null=null;
export function finishGoogleRedirect(config:FirebaseWebConfig):Promise<GoogleRedirectIdentity|null>{
 if(!googleRedirectReady(config))return Promise.resolve(null);
 if(resumePromise)return resumePromise;
 const auth=aegisAuth(config);
 resumePromise=(async()=>{
  const credential=await getRedirectResult(auth);
  if(!credential)return null;
  try{
   if(!credential.user.emailVerified){
    await sendEmailVerification(credential.user);
    throw new Error('Verify your Google account email and then restart AEGIS sign-in.');
   }
   return {idToken:await credential.user.getIdToken(true),email:credential.user.email||''};
  }finally{
   await signOut(auth);
  }
 })();
 return resumePromise;
}

export async function resetFirebasePassword(config:FirebaseWebConfig,email:string){
 const auth=aegisAuth(config);
 await sendPasswordResetEmail(auth,email);
}
export function friendlyError(error:unknown){
 const code=(error as {code?:string})?.code;
 if(code==='auth/popup-closed-by-user')return 'Google sign-in was cancelled. You can try again.';
 if(code==='auth/popup-blocked')return 'Google sign-in popup was blocked. Open AEGIS directly in Safari or Chrome (not an in-app browser), allow pop-ups, and retry. You can also use your AEGIS email and password.';
 if(code==='auth/unauthorized-domain')return 'This website domain is not authorized for Firebase sign-in. An administrator must add aegis-pentest-eg.vercel.app under Firebase Console → Authentication → Settings → Authorized domains. Your email address is not the problem.';
 if(code==='auth/invalid-credential')return 'Email or password could not be verified.';
 if(code==='auth/too-many-requests')return 'Too many attempts. Please wait before trying again.';
 if(code)return 'Firebase sign-in could not complete. Check configuration and try again.';
 return error instanceof Error?error.message:'The identity service is unavailable.';
}
