/* Real browser regression, run in quality.yml. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({headless:true});try{
 for(const width of [390,1280]){const page=await browser.newPage({viewport:{width,height:844}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto((process.env.BM_BASE_URL||'http://127.0.0.1:8765')+'/koopjes/');
 await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('resultaten'));
 for(const term of ['vaatwastabletten','wasmiddel','kipfilet','spinazie','skyr']){await page.locator('#q').fill(term);assert.match(await page.locator('#status').innerText(),/resultaten/);assert.ok(await page.locator('#results article').count()>0,term);}
 await page.locator('#q').fill('spinazie');await page.locator('#sale').check();for(const tag of await page.locator('#results .tag').allTextContents())assert.match(tag,/Nu in aanbieding/);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);await page.close();console.log('Browser '+width+'px: zoeken, aanbiedingen, overflow en runtime geslaagd');}
 }finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
