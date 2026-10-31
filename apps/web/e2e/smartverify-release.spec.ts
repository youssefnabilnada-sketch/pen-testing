import {test,expect} from '@playwright/test';

test('the existing release console guides nontechnical website owners without starting a scan',async({page})=>{
 const writes:string[]=[];
 await page.route('**/api/**',async route=>{
  const request=route.request();
  const path=new URL(request.url()).pathname;
  const method=request.method();
  if(method!=='GET')writes.push(method+' '+path);
  if(path==='/api/auth/me')return route.fulfill({json:{
   id:'fixture-user',email:'fixture-owner@example.test',verified:true,superadmin:false,csrf:'isolated-fixture',
   organizations:[{id:'fixture-org',name:'Fixture Organization',role:'owner'}]
  }});
  if(path==='/api/organizations/fixture-org/assets')return route.fulfill({json:[{id:'asset-one',origin:'https://owned.example.test',verified:false}]});
  if(path==='/api/assets/asset-one/challenge'){
   if(method==='GET')return route.fulfill({json:null});
   const data=request.postDataJSON() as {method:string};
   return route.fulfill({json:{id:'proof',method:data.method,token:'fixture-proof',instruction:'Publish this exact AEGIS proof',expires:4102444800}});
  }
  if(path.endsWith('/dashboard'))return route.fulfill({json:{assets:1,verified_assets:0,completed:0,active:0,open_findings:0,resolved:0,severity:{},pending_remediation:0,trend:[],activity:[]}});
  if(path.endsWith('/remediation-page'))return route.fulfill({json:{items:[],total:0}});
  return route.fulfill({json:[]});
 });
 await page.goto('/console');
 await page.getByRole('button',{name:'My websites',exact:true}).click();
 await page.getByRole('button',{name:'Continue',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Verify your website, without the complexity.'})).toBeVisible();
 await page.getByRole('button',{name:'Watch animated guide'}).click();
 await expect(page.getByText('Any website')).toBeVisible();
 await page.getByRole('button',{name:'Verification method'}).click();
 await expect(page.getByText('Verify with a DNS TXT record')).toBeVisible();
 await page.getByRole('button',{name:'Next'}).click();
 await expect(page.getByText(/Add it to the DNS settings/)).toBeVisible();
 await page.getByRole('button',{name:'Hide lesson'}).click();
 await page.getByRole('button',{name:'Shopify'}).click();
 await page.getByRole('button',{name:'Watch animated guide'}).click();
 await expect(page.getByText('Shopify',{exact:true}).last()).toBeVisible();
 await page.getByRole('button',{name:'Verification method'}).click();
 await expect(page.getByText('Verify with an HTML meta tag')).toBeVisible();
 await page.getByRole('button',{name:'Hide lesson'}).click();
 await expect(page.getByText(/published theme in your Shopify Online Store/)).toBeVisible();
 await page.getByRole('button',{name:'Get verification instructions'}).click();
 await expect(page.getByText('Publish this exact AEGIS proof')).toBeVisible();
 expect(writes).toEqual(['POST /api/assets/asset-one/challenge']);
 const overflow=await page.locator('body').evaluate(el=>el.scrollWidth>window.innerWidth+2);
 expect(overflow).toBe(false);
});
