import {getApps,initializeApp,FirebaseOptions} from 'firebase/app';
import {initializeAuth,inMemoryPersistence,browserPopupRedirectResolver,GoogleAuthProvider,signInWithPopup,signInWithEmailAndPassword,createUserWithEmailAndPassword,sendEmailVerification,sendPasswordResetEmail,signOut} from 'firebase/auth';
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
