import {test,expect} from '@playwright/test';

test('SmartVerify is usable on desktop and mobile without creating a scan',async({page})=>{
 const requests:string[]=[];
 const fixture={id:'fixture-asset',origin:'https://owned.example.test',verified:false};
 await page.route('**/api/**',async route=>{
  const request=route.request();
  const path=new URL(request.url()).pathname;
  requests.push(request.method()+' '+path);
  let data:unknown=[];
  if(path==='/api/auth/me')data={id:'fixture-user',email:'fixture@example.test',verified:true,superadmin:false,csrf:'isolated-fixture',organizations:[{id:'fixture-org',name:'Fixture organization',role:'owner'}]};
  else if(path==='/api/organizations/fixture-org/assets')data=[fixture];
  else if(path.endsWith('/dashboard'))data={assets:1,verified_assets:0,completed:0,active:0,open_findings:0,resolved:0,severity:{},pending_remediation:0,trend:[],activity:[]};
  else if(path.endsWith('/remediation-page'))data={items:[],total:0};
  else if(path.endsWith('/verification-recommendation')||path.endsWith('/challenge'))data=null;
  await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
 });
 await page.goto('/console');
 await page.getByRole('button',{name:'My websites',exact:true}).click();
 await expect(page.getByText('https://owned.example.test')).toBeVisible();
 await page.getByRole('button',{name:'Configure'}).click();
 await expect(page.getByRole('region',{name:'Ownership guide'})).toBeVisible();
 await expect(page.getByText('Verification required')).toBeVisible();
 await page.getByRole('button',{name:'Shopify',exact:true}).click();
 await expect(page.getByText('Add a tag to your store theme')).toBeVisible();
 await page.getByRole('button',{name:'Use recommended method'}).click();
 await expect(page.getByRole('button',{name:/HTML meta tag/})).toHaveAttribute('aria-pressed','true');
 await expect(page.getByRole('button',{name:'Show my secure verification steps'})).toBeVisible();
 const overflow=await page.locator('body').evaluate(el=>el.scrollWidth>window.innerWidth+2);
 expect(overflow).toBe(false);
 expect(requests.every(req=>!req.includes('/assessments')&&!req.includes('/verify/'))).toBe(true);
});
