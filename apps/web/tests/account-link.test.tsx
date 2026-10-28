import {it,expect} from 'vitest';
import {accountLink} from '../lib/account-link';
it('opens only known token actions without performing an account mutation',()=>{
 const token='a'.repeat(32);
 expect(accountLink('#verify='+token)).toEqual({mode:'verify',token});
 expect(accountLink('#reset='+token)).toEqual({mode:'reset',token});
});
it('rejects ambiguous, injected or malformed link parameters',()=>{
 for(const value of ['#redirect=https://evil.example','#verify=short','#verify='+'a'.repeat(32)+'&reset='+'b'.repeat(32),'#reset=%3Cscript%3E','#verify='+'a'.repeat(151)])expect(accountLink(value)).toBeNull();
});
