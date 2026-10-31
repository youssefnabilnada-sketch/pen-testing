import {test,expect} from '@playwright/test';

test('public SmartVerify tutorials are reachable without an account on desktop and mobile',async({page})=>{
 const calls:string[]=[];
 page.on('request',request=>{if(request.url().includes('/api/'))calls.push(request.url());});
 await page.goto('/guides');
 await expect(page.getByRole('heading',{name:/Verify your website/})).toBeVisible();
 await expect(page.getByRole('button',{name:'WordPress'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Shopify'})).toBeVisible();
 await page.getByRole('button',{name:'WordPress'}).click();
 await expect(page.getByText(/Open your WordPress administrator dashboard/)).toBeVisible();
 await page.getByRole('button',{name:'Verification method'}).click();
 await expect(page.getByText('Verify with an HTML meta tag')).toBeVisible();
 await page.getByRole('button',{name:'Next'}).click();
 await expect(page.getByText(/Paste it in the public homepage HTML head/)).toBeVisible();
 expect(calls).toHaveLength(0);
 expect(await page.locator('body').evaluate(el=>el.scrollWidth>window.innerWidth+2)).toBe(false);
});

test('all 14 hosted ownership MP4 tutorials are real files playable before login',async({request})=>{
 const names=['file','dns','meta','wordpress','shopify','wix','squarespace','cloudflare','vercel','netlify','github','cpanel','google','unsure'];
 for(const name of names){
  const response=await request.get('/guides/videos/'+name+'.mp4');
  expect(response.status(),name+' missing video').toBe(200);
  expect(response.headers()['content-type']).toContain('video/mp4');
  const data=await response.body();
  expect(data.length).toBeGreaterThan(10000);
  expect(data.subarray(4,8).toString('ascii')).toBe('ftyp');
 }
});
