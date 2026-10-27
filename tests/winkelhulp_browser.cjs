/* Real mobile/desktop checks for the new, standalone shopping UI. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
(async()=>{
  const snapshot=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../docs/winkelhulp/data.json'),'utf8'));
  const asOf=new Date(snapshot.priced_for+'T12:00:00+01:00');
  const lastOffer=Object.values(snapshot.stores).flat().flatMap(r=>r.ingredients.map(x=>x.price?.valid_until)).filter(Boolean).sort().pop();
  const afterExpiry=new Date(Math.max(asOf.getTime(),Date.parse(lastOffer)||0)+30*86400000);
  let server,base=process.env.BM_BASE_URL;
  if(!base){
    const root=path.resolve(__dirname,'../docs');
    server=http.createServer((req,res)=>{
      let p=path.resolve(root,'.'+new URL(req.url,'http://local').pathname);
      if(!p.startsWith(root+path.sep)&&p!==root){res.writeHead(403);return res.end();}
      if(fs.existsSync(p)&&fs.statSync(p).isDirectory())p=path.join(p,'index.html');
      try{res.setHeader('Content-Type',({'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]||'text/plain');res.end(fs.readFileSync(p));}catch{res.writeHead(404);res.end();}
    });
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));base='http://127.0.0.1:'+server.address().port;
  }
  const browser=await chromium.launch({headless:true,
    ...(process.env.BM_CHROME?{executablePath:process.env.BM_CHROME,args:['--no-sandbox','--disable-gpu','--disable-dev-shm-usage']}:{} )});
  try{
    for(const width of [360,390,1280]){
      const context=await browser.newContext({viewport:{width,height:844}});
      const page=await context.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      await page.clock.install({time:asOf});
      await page.goto(base+'/');
      await page.waitForURL('**/winkelhulp/');
      await page.waitForSelector('#recipes article');
      for(const store of ['ah','jumbo','lidl']){
        await page.locator('[data-store="'+store+'"]').click();
        for(const category of ['kip','vlees','vis','vega']){
          await page.locator('[data-category="'+category+'"]').click();
          assert.equal(await page.locator('#recipes article').count(),10);
          assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
        }
      }
      await page.locator('[data-store="ah"]').click();
      await page.locator('[data-category="kip"]').click();
      await page.locator('.open-list').first().click();
      assert.equal(await page.locator('#shopping').evaluate(e=>e.open),true);
      assert.ok(await page.locator('#shopping-list input').count()>=5);
      await page.locator('#shopping-list input').first().check();
      await page.locator('[data-close="shopping"]').click();
      await page.locator('.open-list').first().click();
      assert.equal(await page.locator('#shopping-list input').first().isChecked(),true);
      await page.locator('.recipe-info summary').click();
      assert.match(await page.locator('#recipe-info').innerText(),/eigen vierportiesvariant/);
      assert.match(await page.locator('#recipe-info a').getAttribute('href'),/^https:\/\/drive.google.com\//);
      assert.equal(await page.evaluate(()=>document.querySelector('#shopping').scrollWidth>document.querySelector('#shopping').clientWidth),false);
      await page.keyboard.press('Escape');
      await page.locator('#sources-button').click();
      await page.locator('#sources details summary').click();
      assert.equal(await page.locator('#source-files li').count(),snapshot.source_files.length);
      assert.equal(await page.locator('#source-summary').innerText(),snapshot.coverage_note);
      await page.keyboard.press('Escape');
      if(process.env.BM_SCREENSHOT_DIR){
        await page.screenshot({path:process.env.BM_SCREENSHOT_DIR+'/winkelhulp-'+width+'.png',fullPage:true});
        await page.locator('.open-list').first().click();
        await page.screenshot({path:process.env.BM_SCREENSHOT_DIR+'/boodschappen-'+width+'.png'});
        await page.keyboard.press('Escape');
      }
      await page.route('**/data.json',route=>route.abort());
      await page.reload();await page.waitForSelector('#recipes article');
      assert.match(await page.locator('#freshness').innerText(),/bewaard overzicht/);
      await page.unroute('**/data.json');
      await page.clock.setSystemTime(afterExpiry);
      await page.reload();await page.waitForSelector('#recipes article');
      assert.match(await page.locator('#freshness').innerText(),/ouder dan 36 uur/);
      assert.equal(await page.locator('#recipes .tag.sale').count(),0,'expired actions are withdrawn');
      assert.deepEqual(errors,[]);
      await context.close();console.log('Winkelhulp '+width+'px: 12 categories, checklist, provenance, offline and expiry passed');
    }
  }finally{await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exit(1);});
