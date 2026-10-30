// Exercise the real app with its real catalog: cards, dialog, saved recipes and combined list.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'../docs');
const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/retailer-catalog.json')));
const elements=new Map();
const el=name=>{if(!elements.has(name))elements.set(name,{innerHTML:'',textContent:'',dataset:{},classList:{toggle(){}},addEventListener(){},showModal(){this.open=true},close(){this.open=false}});return elements.get(name)};
class Clock extends Date {constructor(...args){super(...(args.length?args:[catalog.source_date+'T12:00:00Z']))}static now(){return new Clock().getTime()}}
const ctx={console,URL,Intl,Date:Clock,Set,Map,WeakMap,Promise,parseFloat,parseInt,isNaN,
 document:{querySelector:el,querySelectorAll:()=>[],addEventListener(){}},
 location:{hash:'#vandaag'},localStorage:{getItem:()=>null,setItem(){}},
 fetch:async url=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(root,String(url).split('?')[0]),'utf8'))})};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['recipe-engine.js','favorites.js','product-matcher.js','price-integrity.js','price-observations.js','product-semantics.js','product-resolver.js','catalog-search.js','recipe-shop-options.js','recipe-ranking.js','offer-identity.js','source-freshness.js','app.js']){
 let source=fs.readFileSync(path.join(root,file),'utf8');
 if(file==='app.js')source=source.replace(/\}\)\(\);\s*$/,'window.testApp={state,render,recipePrice,priceQuality,findRecipe,openRecipe,normalize,currentSelections};})();');
 vm.runInContext(source,ctx,{filename:file});
}
(async()=>{
 for(let i=0;i<30&&!el('#view-vandaag').innerHTML;i++)await new Promise(r=>setTimeout(r,20));
 const t=ctx.testApp;
 t.state.catalog.generated_at=catalog.source_date+'T12:00:00Z';
 t.state.catalog.stores.ah.offers.unshift({id:'prepared-regression',name:'AH Ovenschotel kipfilet champignon room',category:'kip',price:6,pack_label:'430 g',start_date:catalog.source_date,end_date:catalog.source_date,source_provider:'PrijsProfeet',source:{url:'https://www.ah.nl/producten/product/wi620796/ah-ovenschotel-kipfilet-champignon-room'},verified:false});
 t.state._offersCache.clear();t.state._matchCache.clear();
 assert.ok(!el('#view-vandaag').innerHTML.includes('[object Object]'));
 for(const store of ['lidl','jumbo','ah']){
  const id='library|'+t.state.library[0].id;
  const recipe=t.findRecipe(store,id);assert.equal(recipe.store,store);assert.equal(recipe.id,id,'Library identifiers must survive opening, saving and planning');
  const price=t.recipePrice(recipe);assert.ok(price.partial>0,store+' must have a catalog estimate');
  const label=t.priceQuality(recipe);
  t.state.store=store;t.state.view='recepten';t.state.recipeQuality='all';t.render();
  assert.ok(el('#view-recepten').innerHTML.includes(label));
  t.openRecipe(store+'|'+id);assert.ok(el('#dialog-content').innerHTML.includes(label));
  assert.ok(!el('#dialog-content').innerHTML.includes('AH Ovenschotel kipfilet champignon room'),'A complete prepared meal must not be suggested as raw chicken');
  assert.ok(!el('#dialog-content').innerHTML.includes('Voor dit bibliotheekrecept zijn nog niet alle'));
  t.state.savedRecipes=[store+'|'+id];t.state.view='mijn';t.render();
  assert.ok(el('#view-mijn').innerHTML.includes(label));
  t.state.selected[store]=[id,'library|'+t.state.library[1].id];t.state.view='lijst';t.render();
  const picks=t.currentSelections(store),merged=new Map();
  for(const r of picks)for(const i of t.normalize(r)){
   const k=i.name.toLowerCase()+'|'+i.unit;
   if(merged.has(k))merged.get(k).quantity+=i.quantity;else merged.set(k,{...i});
  }
  const expected=ctx.MaatjeRecipeShopOptions.estimate({ingredients:[...merged.values()]},store,catalog,ctx.MaatjeObservations,ctx.MaatjeResolver,catalog.source_date);
  const money=x=>new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'}).format(x);
  assert.ok(el('#view-lijst').innerHTML.includes(money(expected.partial)),store+' combined list must use merged quantities');
  assert.ok(expected.partial<=picks.reduce((sum,r)=>sum+t.recipePrice(r).partial,0)+.01,'Shared pantry packs must not be purchased twice');
  assert.ok(!el('#view-lijst').innerHTML.includes('NaN'));
 }
 console.log('Real catalog price consistency verified on recipe cards, dialogs, saved recipes and merged shopping lists for all three stores');
})().catch(e=>{console.error(e);process.exitCode=1});
