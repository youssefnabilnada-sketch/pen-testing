import React from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import PremiumWelcome from '../app/console/PremiumWelcome';
import {Experience} from '../app/console/Experience';

afterEach(()=>{cleanup();localStorage.clear()});
const props={name:'',setName:vi.fn(),busy:false,verified:true,onCreate:vi.fn(e=>e.preventDefault()),onVerify:vi.fn(async()=>{}),accountTools:<p>Advanced settings loaded</p>};

it('focuses a signed-in new customer on the workspace rather than authentication settings',()=>{
 render(<Experience><PremiumWelcome {...props}/></Experience>);
 expect(screen.getByRole('heading',{name:'Create your workspace'})).toBeTruthy();
 expect(screen.getByRole('button',{name:/Create my workspace/})).not.toHaveProperty('disabled',true);
 expect(screen.queryByText('Advanced settings loaded')).toBeNull();
 expect(screen.getByText('No payment required. Nothing will be scanned or changed automatically.')).toBeTruthy();
 expect(screen.getByText('Verify ownership')).toBeTruthy();
});

it('permits email verification in-place and keeps workspace creation disabled until verified',async()=>{
 const verify=vi.fn(async()=>{});
 render(<Experience><PremiumWelcome {...props} verified={false} onVerify={verify}/></Experience>);
 expect((screen.getByRole('button',{name:/Create my workspace/}) as HTMLButtonElement).disabled).toBe(true);
 const input=screen.getByLabelText('Email verification token') as HTMLInputElement;
 fireEvent.change(input,{target:{value:'owned-test-token-with-at-least-20-characters'}});
 fireEvent.click(screen.getByRole('button',{name:'Verify email'}));
 await waitFor(()=>expect(verify).toHaveBeenCalledWith('owned-test-token-with-at-least-20-characters'));
});

it('supports the Arabic first-use journey without hiding the account options',()=>{
 render(<Experience><PremiumWelcome {...props}/></Experience>);
 fireEvent.click(screen.getByRole('button',{name:'التبديل إلى العربية'}));
 expect(screen.getByRole('heading',{name:'أنشئ مساحة عملك'})).toBeTruthy();
 expect(screen.getByText('إثبات الملكية')).toBeTruthy();
 expect(screen.getByText('الحساب والأمان والدعوات')).toBeTruthy();
});
