import {test,expect} from '@playwright/test';

test('public SmartVerify tutorials are reachable without an account on desktop and mobile',async({page})=>{
 const calls:string[]=[];
 page.on('request',request=>{if(request.url().includes('/api/'))calls.push(request.url());});
 await page.goto('/guides');
 await expect(page.getByRole('heading',{name:/Verify your website/})).toBeVisible();
 await expect(page.getByRole('button',{name:'WordPress'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Shopify'})).toBeVisible();
 await page.getByRole('button',{name:'WordPress'}).click();
 await expect(page.locator('.guides-mp4 video source')).toHaveAttribute('src','/guides/videos/wordpress-en.mp4');
 await page.getByRole('button',{name:'التبديل إلى العربية'}).click();
 await expect(page.locator('.guides-mp4 video source')).toHaveAttribute('src','/guides/videos/wordpress-ar.mp4');
 await expect(page.locator('.guides-mp4 video track')).toHaveAttribute('srclang','ar');
 await page.getByRole('button',{name:'Switch to English'}).click();
 await expect(page.getByText(/Open your WordPress administrator dashboard/)).toBeVisible();
 await page.getByRole('button',{name:'Verification method'}).click();
 await expect(page.getByText('Verify with an HTML meta tag')).toBeVisible();
 await page.getByRole('button',{name:'Next'}).click();
 await expect(page.getByText(/Paste it in the public homepage HTML head/)).toBeVisible();
 expect(calls).toHaveLength(0);
 expect(await page.locator('body').evaluate(el=>el.scrollWidth>window.innerWidth+2)).toBe(false);
});

test('all 28 hosted localized narrated MP4s and captions are available before login',async({request})=>{
 const names=['file','dns','meta','wordpress','shopify','wix','squarespace','cloudflare','vercel','netlify','github','cpanel','google','unsure'];
 for(const name of names){
  for(const lang of ['en','ar']){
   const id=name+'-'+lang;
   const response=await request.get('/guides/videos/'+id+'.mp4');
   expect(response.status(),id+' missing video').toBe(200);
   expect(response.headers()['content-type']).toContain('video/mp4');
   const data=await response.body();
   expect(data.length).toBeGreaterThan(10000);
   expect(data.subarray(4,8).toString('ascii')).toBe('ftyp');
   const captions=await request.get('/guides/videos/'+id+'.vtt');
   expect(captions.status(),id+' missing captions').toBe(200);
   expect(await captions.text()).toMatch(/^WEBVTT/);
  }
 }
});
