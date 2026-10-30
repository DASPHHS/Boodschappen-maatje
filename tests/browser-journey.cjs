// Real Chromium journey; unlike the VM smoke test, this clicks the actual rendered UI.
// Run against the checked-out site (local http.server) and the published Pages site.
'use strict';
const assert=require('node:assert/strict');
const { chromium }=require('playwright');
const base=process.env.BASE_URL||'http://127.0.0.1:8765/';
const start=base.endsWith('/')?base:base+'/';
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 const failures=[];
 page.on('pageerror',e=>failures.push(e.stack||e.message));
 try{
  const resp=await page.goto(start+'#vandaag',{waitUntil:'domcontentloaded',timeout:60000});
  assert.ok(resp&&resp.ok(),'Site HTTP status must be 200');
  await page.waitForFunction(()=>document.querySelector('#feed-status')?.textContent?.includes('Acties'),{timeout:60000});
  await page.waitForFunction(()=>getComputedStyle(document.querySelector('.topbar')).display==='flex',{timeout:30000});
  assert.equal(await page.locator('#view-vandaag .store-card').count(),3,'All three supermarkets must render');
  assert.equal(await page.locator('#view-vandaag:not(.hidden)').count(),1);
  assert.ok((await page.locator('#view-vandaag').innerText()).includes('Dit weekmenu'),'A current weekly plan must be published on the homepage');
  const weeklyCard=page.locator('#view-vandaag .recipe-card').filter({hasText:'Weekmenu'}).first();
  await weeklyCard.locator('[data-open]').click();
  await page.locator('#recipe-dialog').waitFor({state:'visible'});
  assert.ok((await page.locator('#dialog-content').innerText()).includes('Verpakkingsopties voor dit recept'),'Week ideas must show guarded shop options');
  assert.ok((await page.locator('#dialog-content').innerText()).includes('geen geverifieerd kassabedrag'),'Never invent a complete recipe price');
  await page.locator('#dialog-close').click();
  await page.locator('.sidebar button[data-view="aanbiedingen"]').click();
  await page.locator('#view-aanbiedingen .compare-table').waitFor();
  assert.ok(await page.locator('#view-aanbiedingen .compare-table tbody tr').count()>=15);
  const comparisonText=await page.locator('#view-aanbiedingen .compare-table').innerText();
  assert.doesNotMatch(comparisonText,/Kipfilet Americanos|Gerookte Kipfilet Plakjes|Kipfilet pepersaus|Blik brokjes zalm forel|Pureersoep pompoen|Knijpfruit Pompoen|groenteshot pompoen/i,'Wrong product classes must never appear in grocery comparisons');
  const milk=page.locator('#view-aanbiedingen .compare-table tbody tr').filter({hasText:'Houdbare volle melk voor cappuccino'});
  assert.equal(await milk.count(),1,'UHT full milk is an exact saved preference');
  for(const name of ['Lidl','Jumbo','Albert Heijn'])assert.ok((await page.locator('#view-aanbiedingen .compare-table').innerText()).includes(name));
  const sourceLinks=page.locator('#view-aanbiedingen .compare-source');
  assert.ok(await sourceLinks.count()>5,'Shelf price sources must be visible');
  await page.locator('[data-manage-watch]').click();
  await page.locator('#new-watch').fill('Ongebrande amandelen 200 g');
  await page.locator('[data-add-watch]').click();
  const customVariantCount=await page.locator('.compare-table tbody tr').filter({hasText:'Ongebrande amandelen 200 g'}).count();
  assert.ok(customVariantCount>=1,'The added query must show its eligible variants');
  await page.reload({waitUntil:'domcontentloaded'});
  await page.locator('.compare-table').waitFor();
  assert.equal(await page.locator('.compare-table tbody tr').filter({hasText:'Ongebrande amandelen 200 g'}).count(),customVariantCount,
    'A user-added product must persist across page reload');
  await page.locator('[data-offer-mode="all"]').click();
  await page.locator('#view-aanbiedingen .deal-card').first().waitFor();
  const before=Number((await page.locator('#product-favorites-count').innerText())||'0');
  await page.locator('#view-aanbiedingen .deal-card [data-fav-toggle]').first().click();
  const after=Number((await page.locator('#product-favorites-count').innerText())||'0');
  assert.equal(after,before+1,'Favorite heart must update count');
  await page.locator('.sidebar button[data-view="recepten"]').click();
  assert.ok(await page.locator('.recipe-source-link').count()>=4,'External originals are accessible');
  const external=page.locator('.recipe-source-link').first();
  assert.ok((await external.getAttribute('href')).startsWith('https://'));
  await page.locator('#view-recepten .recipe-card').first().waitFor();
  await page.locator('#view-recepten .recipe-card [data-recipe-save]').first().click();
  await page.locator('.sidebar button[data-view="mijn"]').click();
  assert.ok(await page.locator('#view-mijn .my-saved-card').count()>=1,'Saved recipe must appear');
  await page.locator('#view-mijn .my-saved-card [data-plan-recipe]').first().click();
  await page.locator('.sidebar button[data-view="lijst"]').click();
  assert.ok(await page.locator('#view-lijst .list-line').count()>=1,'Planning must produce shopping ingredients');
  await page.reload({waitUntil:'domcontentloaded'});
  await page.locator('#view-lijst .list-line').first().waitFor();
  const mobile=await browser.newPage({viewport:{width:390,height:844}});
  try{
   mobile.on('pageerror',e=>failures.push('Mobile: '+(e.stack||e.message)));
   await mobile.goto(start+'#vandaag',{waitUntil:'domcontentloaded',timeout:60000});
   await mobile.waitForFunction(()=>document.querySelector('#feed-status')?.textContent?.includes('Acties'));
   assert.equal(await mobile.locator('.sidebar').isVisible(),false,'Desktop sidebar must be hidden on mobile');
   assert.equal(await mobile.locator('.mobile-nav').isVisible(),true,'Mobile navigation must be visible');
   await mobile.locator('.mobile-nav [data-view="recepten"]').click();
   await mobile.locator('#view-recepten .recipe-source-link').first().waitFor();
   await mobile.locator('.mobile-nav [data-view="lijst"]').click();
   assert.equal(await mobile.locator('#view-lijst:not(.hidden)').count(),1,'Mobile shopping list must work');
  }catch(e){
   await mobile.screenshot({path:'browser-journey-mobile-failure.png',fullPage:true}).catch(()=>{});
   console.error('Mobile failed at '+mobile.url(),await mobile.locator('body').innerText().catch(()=>''));
   throw e;
  }finally{await mobile.close();}
  assert.deepEqual(failures,[],'Browser JavaScript exceptions found');
  console.log('Chromium verified: home, stores, shelf prices, custom products, persistence, live offers, hearts, recipe sources, saved recipes, shopping list, mobile navigation');
 }catch(e){
  await page.screenshot({path:'browser-journey-failure.png',fullPage:true}).catch(()=>{});
  console.error('BROWSER JOURNEY FAILED at '+page.url(),failures,e);
  process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
