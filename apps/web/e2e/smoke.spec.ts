import {test,expect} from '@playwright/test';
test('landing leads to real account form with no checkout',async({page})=>{
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'See the risk. Own the resolution.'})).toBeVisible();
 await page.getByRole('link',{name:'Start a free assessment'}).click();
 await expect(page.getByLabel('Email address')).toBeVisible();
 await expect(page.getByRole('button',{name:'Sign in →'})).toBeVisible();
 await expect(page.getByText('Testing access is free. Payments are disabled.')).toBeVisible();
 expect(await page.locator('body').evaluate(el=>el.scrollWidth<=window.innerWidth)).toBe(true);
});
test('reduced motion retains readable landing content',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/');
 await expect(page.getByLabel('Protective shield visualization')).toBeVisible();
 await expect(page.getByRole('link',{name:'Start a free assessment'})).toBeVisible();
});
