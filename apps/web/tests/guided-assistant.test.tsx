import React from 'react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {cleanup,render,screen,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {Experience} from '../app/console/Experience';
import GuidedAssistant,{suggestedGuideStep} from '../app/console/GuidedAssistant';

afterEach(()=>{cleanup();localStorage.removeItem('aegis-language');vi.unstubAllGlobals()});
const setup=(props:React.ComponentProps<typeof GuidedAssistant>)=>render(<Experience><GuidedAssistant {...props}/></Experience>);

describe('AEGIS Guided Assistant',()=>{
 it('suggests the next real onboarding action without inventing progress',()=>{
  expect(suggestedGuideStep({guest:true})).toBe(0);
  expect(suggestedGuideStep({verified:false})).toBe(1);
  expect(suggestedGuideStep({verified:true})).toBe(2);
  expect(suggestedGuideStep({verified:true,hasOrg:true})).toBe(3);
  expect(suggestedGuideStep({verified:true,hasOrg:true,assets:1})).toBe(4);
  expect(suggestedGuideStep({verified:true,hasOrg:true,assets:1,verifiedAssets:1})).toBe(5);
  expect(suggestedGuideStep({verified:true,hasOrg:true,assets:1,verifiedAssets:1,completed:1})).toBe(6);
 });
 it('helps a guest sign up or open email verification without calling account APIs',async()=>{
  const user=userEvent.setup(),onAuthNavigate=vi.fn(),fetcher=vi.fn();
  vi.stubGlobal('fetch',fetcher);
  setup({guest:true,onAuthNavigate});
  await user.click(screen.getByRole('button',{name:/Guide me step by step/}));
  expect(screen.getByRole('heading',{name:'Create an AEGIS account'})).toBeTruthy();
  expect(screen.getByRole('progressbar',{name:'Walkthrough progress'}).getAttribute('aria-valuenow')).toBe('1');
  await user.click(screen.getByRole('button',{name:'Verify your email'}));
  expect(screen.getByText(/Resend verification email/)).toBeTruthy();
  await user.click(screen.getByRole('button',{name:'Open email verification'}));
  expect(onAuthNavigate).toHaveBeenCalledWith('verify');
  expect(fetcher).not.toHaveBeenCalled();
 });
 it('shows exactly where a Vercel proof file belongs and adapts to WordPress or cPanel',async()=>{
  const user=userEvent.setup();
  setup({verified:true,hasOrg:true,assets:1});
  await user.click(screen.getByRole('button',{name:/Guide me step by step/}));
  expect(screen.getByRole('heading',{name:'Prove website ownership'})).toBeTruthy();
  expect(screen.getByText('public/.well-known/')).toBeTruthy();
  expect(screen.getByText(/Do not rename it/)).toBeTruthy();
  expect((screen.getByRole('link',{name:/Watch platform tutorial/}) as HTMLAnchorElement).href).toContain('/guides?platform=vercel&method=file');
  await user.selectOptions(screen.getByRole('combobox',{name:'Website hosting platform'}),'wordpress');
  expect(screen.getByText(/inside the public homepage/)).toBeTruthy();
  expect(screen.queryByText('public/.well-known/')).toBeNull();
  await user.selectOptions(screen.getByRole('combobox',{name:'Website hosting platform'}),'cpanel');
  expect(screen.getByText(/public_html\/\.well-known/)).toBeTruthy();
 });
 it('navigates only after a real user click and never triggers assessments by itself',async()=>{
  const user=userEvent.setup(),onNavigate=vi.fn(),fetcher=vi.fn();
  vi.stubGlobal('fetch',fetcher);
  setup({verified:true,hasOrg:true,assets:1,verifiedAssets:1,onNavigate});
  await user.click(screen.getByRole('button',{name:/Guide me step by step/}));
  expect(screen.getByRole('heading',{name:'Approve and start a safe assessment'})).toBeTruthy();
  expect(onNavigate).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button',{name:'Open the relevant workspace screen'}));
  expect(onNavigate).toHaveBeenCalledWith('Assets');
  expect(fetcher).not.toHaveBeenCalled();
 });
 it('uses Arabic labels, correct RTL guidance and closes with Escape',async()=>{
  const user=userEvent.setup();
  setup({verified:true,hasOrg:true,assets:1});
  await user.click(screen.getByRole('button',{name:'التبديل إلى العربية'}));
  await user.click(screen.getByRole('button',{name:/ساعدني خطوة بخطوة/}));
  expect(screen.getByRole('heading',{name:'أثبت ملكية الموقع'})).toBeTruthy();
  const dialog=screen.getByRole('region',{name:'مساعد AEGIS التفاعلي'});
  expect(dialog.parentElement?.getAttribute('dir')).toBe('rtl');
  expect(within(dialog).getByText(/ارفع الملف كما هو داخل public/)).toBeTruthy();
  await user.keyboard('{Escape}');
  expect(screen.queryByRole('region',{name:'مساعد AEGIS التفاعلي'})).toBeNull();
 });
});
