// Actual static-app render smoke test: no browser package or mocked product prices.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.join(__dirname,'../docs');
const elements=new Map();
function element(name){
 if(!elements.has(name))elements.set(name,{
  name,innerHTML:'',textContent:'',dataset:{},
  classList:{toggle() {},add(){},remove(){}},
  addEventListener(){},querySelector(){return element('#fallback')},
  focus(){},setSelectionRange(){},
 });
 return elements.get(name);
}
const failures=[];
process.on('unhandledRejection',err=>failures.push(err));
const context={
 console, URL, Intl, Date, Set, Map, Promise, parseFloat, parseInt, isNaN,
 document:{
  querySelector:element,
  querySelectorAll(){return []},
  addEventListener(){},
 },
 location:{hash:'#aanbiedingen'},
 navigator:{clipboard:{writeText:()=>Promise.resolve()}},
 localStorage:{getItem(){return null},setItem(){}},
 alert(){},
 fetch:async function(url){
  const local=String(url).split('?')[0];
  const filename=path.resolve(ROOT,local);
  if(!filename.startsWith(ROOT+path.sep)||!fs.existsSync(filename))return {ok:false,status:404};
  return {ok:true,status:200,json:async()=>JSON.parse(fs.readFileSync(filename,'utf8'))};
 },
};
context.window=context;
vm.createContext(context);
for(const src of [
 'recipe-engine.js','favorites.js','product-matcher.js','price-integrity.js',
 'price-observations.js','product-resolver.js','catalog-search.js',
 'recipe-ranking.js','offer-identity.js','source-freshness.js','app.js']){
 vm.runInContext(fs.readFileSync(path.join(ROOT,src),'utf8'),context,{filename:src});
}
(async()=>{
 for(let i=0;i<30&&(!element('#view-aanbiedingen').innerHTML||failures.length);i++)
  await new Promise(resolve=>setTimeout(resolve,50));
 assert.equal(failures.length,0,failures.map(String).join('\n'));
 const html=element('#view-aanbiedingen').innerHTML;
 assert.ok(html.includes('compare-table'),"Expected compact comparison table");
 assert.ok(html.includes('Houdbare volle melk voor cappuccino'));
 assert.ok(html.includes('Lidl')&&html.includes('Jumbo')&&html.includes('Albert Heijn'));
 assert.ok(!html.includes('Broncontrole aanvragen via GitHub'),'Do not burden user with source-issue tickets');
 assert.ok(!html.includes('289 aanvullende treffers'),'The irrelevant promo feed must stay out of personal view');
 assert.ok(html.includes('Houdbare volle melk'),'Exact product should be shown');
 const dataset=JSON.parse(fs.readFileSync(path.join(ROOT,'data/retailer-catalog.json'),'utf8'));
 const fresh=context.MaatjeCatalogSearch.valid(dataset,new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'}));
 if(fresh){
  const p=context.MaatjeCatalogSearch;
  const q=JSON.parse(fs.readFileSync(path.join(ROOT,'data/watchlist.json'),'utf8')).items.find(x=>x.key==='volle_melk');
  for(const store of ['lidl','jumbo','ah']){
   const prices=p.candidates(q,store,dataset,context.MaatjeObservations,context.MaatjeResolver,dataset.source_date);
   assert.ok(prices.length,'Expected a verified variant match from the snapshot for '+store);
   assert.ok(html.includes(prices[0].o.name),'Missing product '+prices[0].o.name);
  }
 }
 assert.ok(html.length<200000,"Personal view should not render hundreds of cards");
 console.log('End-to-end static render: real catalog, 3 stores, no issue-ticket wall, focused UI verified');
})().catch(err=>{console.error(err);process.exitCode=1});
