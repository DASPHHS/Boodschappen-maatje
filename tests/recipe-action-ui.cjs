// Exercise the real app with its real catalog: cards, dialog, saved recipes and combined list.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'../docs');
const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/retailer-catalog.json')));
const elements=new Map();
const el=name=>{if(!elements.has(name))elements.set(name,{innerHTML:'',textContent:'',dataset:{},classList:{toggle(){}},addEventListener(){},showModal(){this.open=true},close(){this.open=false}});return elements.get(name)};
const actionDay=new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
class Clock extends Date {constructor(...args){super(...(args.length?args:[actionDay+'T12:00:00Z']))}static now(){return new Clock().getTime()}}
const ctx={console,URL,Intl,Date:Clock,Set,Map,WeakMap,Promise,parseFloat,parseInt,isNaN,
 document:{querySelector:el,querySelectorAll:()=>[],addEventListener(){}},
 location:{hash:'#vandaag'},localStorage:{getItem:()=>null,setItem(){}},
 fetch:async url=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(root,String(url).split('?')[0]),'utf8'))})};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['recipe-engine.js','favorites.js','product-matcher.js','price-integrity.js','price-observations.js','product-semantics.js','product-resolver.js','catalog-search.js','recipe-shop-options.js','recipe-ranking.js','recipe-presentation.js','publisher-selection.js','offer-identity.js','weekdeals-engine.js','recipe-products.js','recipe-discovery.js','source-freshness.js','app.js']){
 let source=fs.readFileSync(path.join(root,file),'utf8');
 if(file==='app.js')source=source.replace(/\}\)\(\);\s*$/,'window.testApp={state,render,recipes,catalog,offers,recipeActions,findRecipe,openRecipe};})();');
 vm.runInContext(source,ctx,{filename:file});
}
(async()=>{
 for(let i=0;i<60&&!el('#view-vandaag').innerHTML;i++)await new Promise(r=>setTimeout(r,20));
 const t=ctx.testApp;
 const index=t.state.publisherRecipes;
 const culinary=ctx.MaatjeRecipeProducts;
 const offersByStore=Object.fromEntries(['ah','jumbo','lidl'].map(s=>[s,t.offers(s)]));
 const rows=ctx.MaatjePublisherSelection.recipesForOffers({index,stores:['ah','jumbo','lidl'],offersByStore,engine:ctx.MaatjeRecipeDiscovery,day:actionDay});
 assert.ok(index.recipes.some(r=>r.source==='HelloFresh'&&r.ingredient_evidence==='publisher_recipe_schema'));
 assert.ok(index.recipes.some(r=>r.source==='Allerhande'&&r.ingredient_evidence==='publisher_recipe_schema'));
 for(const row of rows){
  assert.ok(row.matched.count>=2);
  assert.equal(new Set(row.matched.products.map(x=>x.family)).size,row.matched.count);
  assert.ok(row.matched.products.every(x=>culinary.recipeProfiles(row.recipe).some(p=>culinary.compatible(x.profile,p))));
  if(row.category==='vis')assert.ok(!row.matched.main.some(x=>x.family.startsWith('vega_')));
 }
 for(const s of ['ah','jumbo','lidl'])for(const r of t.catalog(s))assert.ok(t.recipeActions(r,s).length>=2);
 t.state.view='recepten';t.render();
 const page=el('#view-recepten').innerHTML;
 assert.ok(page.includes('Alle bronnen'));
 assert.ok(page.includes(rows.length?'actieproducten bij':'Geen recepten met minimaal twee'));
 assert.ok(page.includes('Allerhande')&&page.includes('HelloFresh'));
 assert.doesNotMatch(page,/Honig Bakplaat Mix|Jumbo Gevulde Eieren|Maza Hoemoes Paprika|Jumbo Champignons Knoflook/);
 t.state.recipeBasis='main';t.render();
 for(const store of ['ah','jumbo','lidl'])for(const r of t.catalog(store).filter(r=>t.recipeActions(r,store).some(x=>x.isMain)))assert.ok(t.recipeActions(r,store).length>=2);
 t.state.recipeBasis='all';
 assert.ok(!page.includes('undefined')&&!page.includes('[object Object]'));
 // Reproduce the mobile screenshot: Jumbo -> Kip -> exact product match.
 Object.assign(t.state,{store:'jumbo',kind:'kip',subtype:'alle',query:'',cookingQuery:'',cookingOffer:null,dealFilter:'confirmed',recipeBasis:'all'});
 t.render();
 const strict=el('#view-recepten').innerHTML;
 if(!strict.includes('data-open="')){
  assert.ok(strict.includes('Geen exacte productkoppelingen beschikbaar'));
  assert.ok(strict.includes('data-relax-deals="1"'));
  assert.ok(!strict.includes('publisher-recipe-card'),'Never relabel approximate matches as exact');
 }
 t.state.dealFilter='all';t.render();
 assert.ok(el('#view-recepten').innerHTML.includes('publisher-recipe-card'),'Relaxing only evidence keeps useful Jumbo chicken recipes');
 assert.ok(el('#view-recepten').innerHTML.includes('geen exacte merk-/EAN-koppeling'));
 // Saved originals remain readable when their promotions expire.
 const id='library|'+t.state.library[0].id;
 assert.ok(t.findRecipe('ah',id));t.openRecipe('ah|'+id);
 assert.ok(el('#dialog-content').innerHTML.includes(t.state.library[0].title));
 console.log('Real feed action UI: '+rows.length+' publisher recipes; sources '+[...new Set(rows.map(x=>x.recipe.source))].join(', '));
 console.log('First eight: '+rows.slice(0,8).map(x=>x.category+'/'+x.recipe.method+'/'+x.recipe.source).join(', '));
})().catch(e=>{console.error(e);process.exitCode=1});
