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
  if(await page.locator('#view-vandaag .recipe-card').filter({hasText:'Weekmenu'}).count()){
  const weeklyCard=page.locator('#view-vandaag .recipe-card').filter({hasText:'Weekmenu'}).first();
  await weeklyCard.locator('[data-open]').click();
  await page.locator('#recipe-dialog').waitFor({state:'visible'});
  assert.ok((await page.locator('#dialog-content').innerText()).includes('Verpakkingsopties voor dit recept'),'Week ideas must show guarded shop options');
  assert.ok((await page.locator('#dialog-content').innerText()).includes('geen geverifieerd kassabedrag'),'Never invent a complete recipe price');
  await page.locator('#dialog-close').click();
  }
  await page.locator('.sidebar button[data-view="aanbiedingen"]').click();
  await page.locator('#view-aanbiedingen .compare-table').waitFor();
  assert.ok(await page.locator('#view-aanbiedingen .compare-table tbody tr').count()>=15);
  const comparisonText=await page.locator('#view-aanbiedingen .compare-table').innerText();
  assert.doesNotMatch(comparisonText,/Kipfilet Americanos|Gerookte Kipfilet Plakjes|Kipfilet pepersaus|Blik brokjes zalm forel|Pureersoep pompoen|Knijpfruit Pompoen|groenteshot pompoen/i,'Wrong product classes must never appear in grocery comparisons');
  const peanutRows=page.locator('#view-aanbiedingen .compare-table tbody tr').filter({hasText:'Pindakaas'});
  if(await peanutRows.count()>0){
   for(const row of await peanutRows.all()){
    const header=await row.locator('th').innerText();
    const content=await row.innerText();
    if(/Calvé Pindakaas met stukjes pinda/i.test(content))
     assert.ok(/met stukjes/i.test(header),'Calvé crunchy must be labelled as chunky, not generic peanut butter');
    if(/structuur niet vermeld/i.test(header))
     assert.ok(!/Calvé Pindakaas met stukjes pinda/i.test(content),'Chunky product must not appear in generic texture row');
   }
  }
  const milk=page.locator('#view-aanbiedingen .compare-table tbody tr').filter({hasText:'Houdbare volle melk voor cappuccino'});
  assert.ok(await milk.count()>=1,'UHT full milk must still be in the saved preferences');
  for(const row of await milk.all()){
   const text=await row.innerText();
   assert.ok(!/lactosevrije volle melk|verse volle melk/i.test(text),'UHT full milk must not contain fresh or lactose-free substitutes');
  }
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
  await page.locator('#offer-category').selectOption('vleeswaren');
  assert.ok(await page.locator('#view-aanbiedingen .deal-card').count()>0,'Deli products remain visible as their actual food type');
  assert.match(await page.locator('#view-aanbiedingen').innerText(),/Broodbeleg · geen rauwe kip/);
  assert.equal(await page.locator('#view-aanbiedingen [data-cook-offer]').count(),0,'Deli chicken never launches raw chicken recipe suggestions');
  await page.locator('#offer-category').selectOption('alle');
  assert.equal(await page.locator('[data-offer-week="now"]').count(),1,'Weekdeals: this week tab');
  await page.locator('[data-offer-week="next"]').click();
  assert.ok((await page.locator('#view-aanbiedingen').innerText()).includes('Vooruitblik'),
   'Weekdeals: next-week control must clearly distinguish upcoming promotions');
  assert.ok((await page.locator('#view-aanbiedingen').innerText()).includes('Albert Heijn'),
   'All three stores remain represented');
  await page.locator('[data-offer-week="now"]').click();
  await page.locator('#view-aanbiedingen .deal-card').first().waitFor();
  const cookingButtons=page.locator('#view-aanbiedingen .deal-card [data-cook-offer]');
  assert.ok(await cookingButtons.count()>0,'At least one currently discounted ingredient should suggest real recipes');
  await cookingButtons.first().click();
  await page.locator('#view-recepten #cooking-ideas').waitFor();
  assert.equal(await page.locator('#cooking-ideas a[href*="google.com/search"]').count(),0,
   'Offer suggestions must not require users to search publishers');
  await page.locator('.sidebar button[data-view="aanbiedingen"]').click();
  await page.locator('#view-aanbiedingen .deal-card').first().waitFor();
  const before=Number((await page.locator('#product-favorites-count').innerText())||'0');
  await page.locator('#view-aanbiedingen .deal-card [data-fav-toggle]').first().click();
  const after=Number((await page.locator('#product-favorites-count').innerText())||'0');
  assert.equal(after,before+1,'Favorite heart must update count');
  await page.locator('.sidebar button[data-view="recepten"]').click();
  if(await page.locator('#cooking-ideas [data-clear-cook]').count())await page.locator('#cooking-ideas [data-clear-cook]').click();
  await page.locator('#view-recepten [data-store="alle"]').click();
  const publisherCards=page.locator('#publisher-recipes-main .publisher-recipe-card');
  assert.ok(await publisherCards.count()>0,'Current offers must yield publisher recipes');
  assert.ok(await publisherCards.count()<=8,'First page is bounded');
  assert.equal(await page.locator('#publisher-recipes-main [data-publisher-source="all"]').getAttribute('aria-pressed'),'true');
  for(const card of await publisherCards.all()){
   assert.ok(await card.locator('.publisher-match li').count()>=2,'Every recipe shows two different actionable products');
   const text=await card.innerText();
   assert.match(text,/(?:passende )?actieproducten bij/);
   assert.doesNotMatch(text,/Honig Bakplaat Mix|Jumbo Gevulde Eieren|Maza Hoemoes Paprika|Jumbo Champignons Knoflook/);
   assert.ok(await card.locator('.publisher-match a[href^="https://"]').count()>=2);
  }
  await page.locator('#basis-filter').selectOption('main');
  for(const card of await publisherCards.all())assert.match(await card.innerText(),/eiwitbasis in actie/);
  await page.locator('#basis-filter').selectOption('all');
  const exactOption=page.locator('#deal-filter option[value="confirmed"]');
  if(await exactOption.isDisabled())assert.match(await exactOption.innerText(),/\(0\)/,'A zero-result exact option must say so and be disabled');
  assert.equal(await page.locator('#deal-filter option[value="anchor"]').count(),0,'No duplicate technical evidence filters');
  await page.locator('#recipe-find').fill('onvindbaar recept xyz');
  await page.locator('#recipe-find').press('End');
  assert.equal(await page.evaluate(()=>document.activeElement.id),'recipe-find','Recipe search must keep focus in its own visible field');
  await page.locator('[data-reset-recipes]').click();
  assert.ok(await publisherCards.count()>0,'Reset must restore useful recipes after an empty selection');
  for(const meal of ['ontbijt','lunch','avondeten']){
   await page.locator('#view-recepten [data-meal="'+meal+'"]').click();
   assert.equal(await page.locator('#view-recepten [data-meal="'+meal+'"]').getAttribute('aria-pressed'),'true');
   for(const card of await publisherCards.all())assert.ok(await card.locator('.publisher-match li').count()>=2,'Every meal keeps the two-action gate');
  }
  const firstCount=await publisherCards.count();
  if(await page.locator('#view-recepten [data-more-publishers]').count()){
   await page.locator('#view-recepten [data-more-publishers]').click();
   assert.ok(await publisherCards.count()>firstCount);
  }
  for(const source of ['Allerhande','HelloFresh']){
   await page.locator('#publisher-recipes-main [data-publisher-source="'+source+'"]').click();
   for(const card of await publisherCards.all())assert.equal(await card.locator('.tag').innerText(),source);
  }
  await page.locator('#publisher-recipes-main [data-publisher-source="all"]').click();
  await page.locator('#ingredient-discovery').fill('nieuwe onbekende groente 2027');
  await page.locator('[data-find-ideas]').click();
  assert.match(await page.locator('#cooking-ideas').innerText(),/productsoort niet voldoende herkend/);
  assert.equal(await publisherCards.count(),0,'Unknown ingredient must not create invented matches');
  await page.locator('[data-clear-cook]').click();
  await page.locator('#ingredient-discovery').fill('broccoli');
  await page.locator('[data-find-ideas]').click();
  for(const card of await publisherCards.all())assert.ok(await card.locator('.publisher-match li').count()>=2);
  await page.locator('[data-clear-cook]').click();
  if(await page.locator('[data-show-recipe-library]').count())await page.locator('[data-show-recipe-library]').click();
  const own=page.locator('#view-recepten .recipe-card:not(.publisher-recipe-card)');
  for(const card of await own.all())assert.match(await card.innerText(),/[2-9] actieproducten/);
  if(await own.count()){
   await own.first().locator('[data-recipe-save]').click();
   await page.locator('.sidebar button[data-view="mijn"]').click();
   assert.ok(await page.locator('#view-mijn .my-saved-card').count()>=1);
   await page.locator('#view-mijn .my-saved-card [data-plan-recipe]').first().click();
   await page.locator('.sidebar button[data-view="lijst"]').click();
   assert.ok(await page.locator('#view-lijst .list-line').count()>=1);
   await page.reload({waitUntil:'domcontentloaded'});
   await page.locator('#view-lijst .list-line').first().waitFor();
  }
  const mobile=await browser.newPage({viewport:{width:390,height:844}});
  try{
   mobile.on('pageerror',e=>failures.push('Mobile: '+(e.stack||e.message)));
   await mobile.goto(start+'#vandaag',{waitUntil:'domcontentloaded',timeout:60000});
   await mobile.waitForFunction(()=>document.querySelector('#feed-status')?.textContent?.includes('Acties'));
   assert.equal(await mobile.locator('.sidebar').isVisible(),false,'Desktop sidebar must be hidden on mobile');
   assert.equal(await mobile.locator('.mobile-nav').isVisible(),true,'Mobile navigation must be visible');
   await mobile.locator('.mobile-nav [data-view="recepten"]').click();
   await mobile.locator('#publisher-recipes-main .publisher-recipe-card').first().waitFor();
   assert.equal(await mobile.locator('#publisher-recipes-main [data-publisher-source="all"]').getAttribute('aria-pressed'),'true');
   for(const card of await mobile.locator('#publisher-recipes-main .publisher-recipe-card').all())
    assert.ok(await card.locator('.publisher-match li').count()>=2);
   for(const meal of ['ontbijt','lunch','avondeten']){
    await mobile.locator('#view-recepten [data-meal="'+meal+'"]').click();
    assert.equal(await mobile.locator('#view-recepten [data-meal="'+meal+'"]').getAttribute('aria-pressed'),'true');
    const cards=mobile.locator('#publisher-recipes-main .publisher-recipe-card');
    for(const card of await cards.all())assert.ok(await card.locator('.publisher-match li').count()>=2);
    if(await cards.count())assert.equal(await mobile.locator('#view-recepten .empty-state').count(),0,'Available source recipes must not be followed by a conflicting empty state');
   }
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
