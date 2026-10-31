import {beforeEach,it,expect,vi} from 'vitest';
const m=vi.hoisted(()=>({persist:vi.fn(),popup:vi.fn(),out:vi.fn(),verify:vi.fn(),token:vi.fn(),email:vi.fn()}));
vi.mock('firebase/app',()=>({getApps:()=>[],initializeApp:()=>({})}));
vi.mock('firebase/auth',()=>({getAuth:()=>({}),setPersistence:m.persist,inMemoryPersistence:'memory',GoogleAuthProvider:class{setCustomParameters(){}},signInWithPopup:m.popup,signOut:m.out,sendEmailVerification:m.verify,signInWithEmailAndPassword:m.email,createUserWithEmailAndPassword:vi.fn(),sendPasswordResetEmail:vi.fn()}));
import {authenticate,friendlyError} from '../lib/firebase-client';
beforeEach(()=>{vi.clearAllMocks();m.popup.mockResolvedValue({user:{emailVerified:true,getIdToken:m.token}});m.token.mockResolvedValue('token');m.out.mockResolvedValue(undefined)});
it('exchanges token in memory and signs SDK out even on API failure',async()=>{
 const exchange=vi.fn(async()=>{throw new Error('API unavailable')});
 await expect(authenticate({},'google','','',false,exchange)).rejects.toThrow('API unavailable');
 expect(m.persist).toHaveBeenCalledWith({},'memory');expect(exchange).toHaveBeenCalledWith('token');expect(m.out).toHaveBeenCalledOnce();
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
