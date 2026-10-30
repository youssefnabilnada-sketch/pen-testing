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

test('isolated workspace fixture supports primary navigation, reports and Arabic on each viewport',async({page})=>{
 // Explicit UI fixture: no real account, network assessment or customer finding is created.
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  const data=path==='/api/auth/me'?{id:'fixture-user',email:'fixture@example.test',verified:true,superadmin:false,csrf:'fixture',organizations:[{id:'fixture-org',name:'Isolated UI fixture',role:'viewer'}]}:path.endsWith('/dashboard')?{assets:0,verified_assets:0,completed:0,active:0,open_findings:0,resolved:0,severity:{},pending_remediation:0,trend:[],activity:[]}:path.endsWith('/remediation-page')||path.endsWith('/finding-page')?{items:[],total:0}:[];
  await route.fulfill({json:data});
 });
 await page.goto('/console');
 await expect(page.getByRole('heading',{name:'Your security, in focus.'})).toBeVisible();
 await page.getByRole('button',{name:'Reports',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Assessment reports'})).toBeVisible();
 await expect(page.getByText('No assessment reports yet.')).toBeVisible();
 await page.getByRole('button',{name:'التبديل إلى العربية'}).click();
 await expect(page.locator('.experience')).toHaveAttribute('dir','rtl');
 await page.getByRole('button',{name:'النتائج والإصلاحات',exact:true}).click();
 await expect(page.getByText('طريق واضح لإصلاح تم التحقق منه')).toBeVisible();
 await page.getByRole('button',{name:/الأدوات والإعدادات/}).click();
 await expect(page.getByRole('button',{name:'أمان الحساب',exact:true})).toBeVisible();
 expect(await page.locator('body').evaluate(el=>el.scrollWidth<=window.innerWidth)).toBe(true);
});
