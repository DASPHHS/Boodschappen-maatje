'use strict';
/* Guard against a UI regression where catalog has actual prices but cards all say unknown.
   Reads the real published catalogue, not fabricated price fixtures. */
const fs=require('node:fs'),assert=require('node:assert/strict');
const shop=require('../docs/recipe-shop-options.js');
const resolver=require('../docs/product-resolver.js');
const pricing=require('../docs/price-observations.js');
const catalog=JSON.parse(fs.readFileSync('docs/data/retailer-catalog.json','utf8'));
const library=JSON.parse(fs.readFileSync('docs/data/library.json','utf8')).recipes;
const selected=library.filter(r=>r.quality_status==='uitgewerkt_niet_culinair_getest');
assert.ok(selected.length>=20,'Need enough developed recipes for a representative audit');
const day=catalog.source_date;
const report={source_date:day,developed_recipes:selected.length,stores:{}};
for(const store of ['lidl','jumbo','ah']){
 const byMissing=new Map();let knownRecipes=0,pricedIngredients=0,allIngredients=0,full=0,examples=[];
 for(const recipe of selected){
  const result=shop.estimate(recipe,store,catalog,pricing,resolver,day);
  allIngredients+=result.required;pricedIngredients+=result.priced_count;
  if(result.partial>0){knownRecipes++;if(examples.length<3)examples.push({recipe:recipe.title,known_packages:result.partial,priced:result.priced_count,total:result.required})}
  if(result.total!==null)full++;
  for(const name of result.missing)byMissing.set(name,(byMissing.get(name)||0)+1);
 }
 report.stores[store]={known_recipes:knownRecipes,total_recipes:selected.length,priced_ingredients:pricedIngredients,all_ingredients:allIngredients,complete_recipe_indications:full,examples,most_unpriced:[...byMissing.entries()].sort((a,b)=>b[1]-a[1]).slice(0,12)};
 assert.ok(knownRecipes>=Math.floor(selected.length*.45),store+' lost most real ingredient prices');
 assert.ok(pricedIngredients>=selected.length,store+' lost too many ingredient prices');
}
console.log('REAL_RECIPE_PRICE_COVERAGE '+JSON.stringify(report));
