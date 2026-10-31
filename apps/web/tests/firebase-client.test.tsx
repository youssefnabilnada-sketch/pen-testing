import {beforeEach,it,expect,vi} from 'vitest';
const m=vi.hoisted(()=>({initAuth:vi.fn(()=>({})),popup:vi.fn(),out:vi.fn(),verify:vi.fn(),token:vi.fn(),email:vi.fn(),redirect:vi.fn(),redirectResult:vi.fn()}));
vi.mock('firebase/app',()=>({getApps:()=>[],initializeApp:()=>({})}));
vi.mock('firebase/auth',()=>({initializeAuth:m.initAuth,inMemoryPersistence:'memory',browserPopupRedirectResolver:'resolver',GoogleAuthProvider:class{setCustomParameters(){}},signInWithPopup:m.popup,signInWithRedirect:m.redirect,getRedirectResult:m.redirectResult,signOut:m.out,sendEmailVerification:m.verify,signInWithEmailAndPassword:m.email,createUserWithEmailAndPassword:vi.fn(),sendPasswordResetEmail:vi.fn()}));
import {authenticate,friendlyError} from '../lib/firebase-client';
beforeEach(()=>{vi.clearAllMocks();m.popup.mockResolvedValue({user:{emailVerified:true,getIdToken:m.token}});m.token.mockResolvedValue('token');m.out.mockResolvedValue(undefined)});
it('exchanges token in memory and signs SDK out even on API failure',async()=>{
 const exchange=vi.fn(async()=>{throw new Error('API unavailable')});
 await expect(authenticate({},'google','','',false,exchange)).rejects.toThrow('API unavailable');
 expect(m.initAuth).toHaveBeenCalledWith({},{persistence:'memory',popupRedirectResolver:'resolver'});expect(exchange).toHaveBeenCalledWith('token');expect(m.out).toHaveBeenCalledOnce();
});
it('unverified identity sends verification but cannot exchange',async()=>{
 m.popup.mockResolvedValue({user:{emailVerified:false,getIdToken:m.token}});const exchange=vi.fn();
 await expect(authenticate({},'google','','',false,exchange)).rejects.toThrow('Verification email sent');
 expect(m.verify).toHaveBeenCalledOnce();expect(exchange).not.toHaveBeenCalled();expect(m.out).toHaveBeenCalledOnce();
});

it('identifies an unauthorized Firebase website domain as an administrator configuration issue',()=>{
 const actual=friendlyError({code:'auth/unauthorized-domain'});
 expect(actual).toContain('aegis-pentest-eg.vercel.app');
 expect(actual).toContain('Authorized domains');
 expect(actual).toContain('Your email address is not the problem.');
});

it('opens the Google popup synchronously before a promise boundary',async()=>{
 const pending=authenticate({},'google','','',false,vi.fn(async()=>{}));
 expect(m.popup).toHaveBeenCalledOnce();
 await pending;
});
it('gives a Safari fallback when an in-app popup is blocked',()=>{
 const message=friendlyError({code:'auth/popup-blocked'});
 expect(message).toContain('Safari');
 expect(message).toContain('in-app browser');
 expect(message).toContain('AEGIS email and password');
});
