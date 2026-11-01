import {test,expect} from '@playwright/test';
test('authorized health dashboard configures checks and displays real history',async({page},info)=>{
 test.skip(process.env.E2E_HEALTH!=='1','Requires controlled local health runner.');
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/console');
 await page.getByLabel('Email address',{exact:true}).fill('owner@example.test');
 await page.getByLabel('Password',{exact:true}).fill('Long-password123!');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await page.getByRole('navigation',{name:'Workspace navigation'}).getByRole('button',{name:'Monitoring',exact:true}).click();
 await page.getByRole('button',{name:'Add a monitor'}).click();
 await page.getByLabel('Verified website').selectOption({label:'https://example.test'});
 await page.getByLabel(/I authorize one bounded/).check();
 await page.getByRole('button',{name:'Authorize monitoring',exact:true}).click();
 await expect(async()=>{
  await page.getByRole('button',{name:'Refresh status'}).click();
  await expect(page.getByText('Latest result: up')).toBeVisible();
 }).toPass({timeout:15000});
 await page.getByRole('button',{name:'View observations'}).click();
 // Multiple successful samples are legitimate; verify visible history without
 // assuming the sample text appears exactly once.
 await expect(page.getByText(/HTTP 200/).first()).toBeVisible();
 await page.getByRole('button',{name:'Stop monitoring'}).click();
 await expect(page.getByText('Inactive')).toBeVisible();
 await page.screenshot({path:info.outputPath('health-dashboard.png'),fullPage:true});
 expect(errors).toEqual([]);
});
