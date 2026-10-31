import {test,expect} from '@playwright/test';

// Actual deployed HTTPS website; deliberately guest-only. Never supplies
// customer credentials or creates accounts, assets, scans, or FastFix jobs.
test('production account entry and Firebase controls are usable on desktop/mobile',async({page})=>{
 const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.name));
 const response=await page.goto('/console',{waitUntil:'domcontentloaded',timeout:30000});
 expect(response?.status()).toBe(200);
 await expect(page.getByRole('heading',{name:'Welcome back.'})).toBeVisible({timeout:20000});
 await expect(page.getByLabel('Email address')).toBeVisible();
 await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeEnabled();
 await expect(page.getByRole('button',{name:'Sign in with Google'})).toBeVisible({timeout:20000});
 await expect(page.locator('.google-signin-button .google-mark')).toHaveCount(1);
 await expect(page.getByText('Continue with Firebase')).toHaveCount(0);
 await expect(page.getByText('Account sign-in is temporarily unavailable',{exact:false})).toHaveCount(0);
 await expect(page.getByText('Firebase sign-in settings could not be checked',{exact:false})).toHaveCount(0);
 expect(await page.locator('body').evaluate(el=>el.scrollWidth<=window.innerWidth)).toBe(true);
 expect(errors).toEqual([]);
});

test('live guest account entry supports keyboard use and Arabic RTL',async({page})=>{
 await page.goto('/console',{waitUntil:'domcontentloaded'});
 const email=page.getByLabel('Email address');
 await expect(email).toBeVisible();
 await email.focus();
 await page.keyboard.type('fixture@example.test');
 await page.keyboard.press('Tab');
 await expect(page.locator('.auth-form input[autocomplete="current-password"]')).toBeFocused();
 await page.getByRole('button',{name:'التبديل إلى العربية'}).click();
 await expect(page.locator('.experience')).toHaveAttribute('dir','rtl');
 await expect(page.getByRole('heading',{name:'مرحبًا بعودتك.'})).toBeVisible();
 await expect(page.getByRole('button',{name:'تسجيل الدخول'})).toBeEnabled();
 expect(await page.locator('body').evaluate(el=>el.scrollWidth<=window.innerWidth)).toBe(true);
});
