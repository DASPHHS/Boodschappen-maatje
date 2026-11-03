'use strict';
const assert=require('node:assert/strict'),fs=require('fs'),p=require('../docs/recipe-products'),s=require('../docs/publisher-selection'),engine=require('../docs/recipe-discovery');
const index=JSON.parse(fs.readFileSync('docs/data/publisher-recipes.json'));
for(const meal of ['ontbijt','lunch'])assert.ok(index.recipes.filter(r=>r.meal_type===meal&&r.ingredient_profile_version===2).length>=4,'Verified real recipes for '+meal);
const day='2026-11-03',offer=(id,name)=>({id,name,price:2,pack_label:'400 g',source:{url:'https://www.prijsprofeet.nl/'},source_provider:'PrijsProfeet',promotion_status:'active',start_date:day,end_date:'2026-11-08'});
const deli=offer('deli','Jumbo Scharrel Kipfilet Voordeelverpakking 200 g'),tomato=offer('t','Tomaten');
const recipe={id:'fixture-lunch',title:'Broodje met kipfilet broodbeleg en tomaat',source:'Allerhande',url:'https://www.ah.nl/allerhande/recept/R-R123/test',review_status:'publisher_metadata_verified',ingredient_profile_version:2,ingredient_profiles:[p.profile(deli,{ingredient:true}),p.profile('tomaten',{ingredient:true})],meal_type:'lunch'};
assert.equal(s.actionProducts(recipe,[deli,tomato],engine,day).length,2);
assert.equal(s.actionProducts({...recipe,meal_type:'avondeten'},[deli,tomato],engine,day).length,1,'Deli cannot leak back into raw dinner matching');
assert.equal(s.recipesForOffers({index:{recipes:[recipe]},stores:['jumbo'],offersByStore:{jumbo:[deli,tomato]},engine,day,meal:'ontbijt'}).length,0);
assert.equal(s.recipesForOffers({index:{recipes:[recipe]},stores:['jumbo'],offersByStore:{jumbo:[deli,tomato]},engine,day,meal:'lunch'}).length,1);
assert.ok(!p.compatible(p.profile('Campina Magere Kwark vanille'),p.profile('magere kwark',{ingredient:true})),'Flavored dairy must not replace plain dairy');
assert.ok(!p.profile('Katja Yoghurtgums'));
assert.ok(p.profile('Campina Magere Milde Kwark Naturel 500 g'));
console.log('Breakfast/lunch verified source records, meal filters, yogurt variants and context-specific deli matching passed');

const own=JSON.parse(fs.readFileSync('docs/data/curated-recipes.json')).recipes.filter(r=>['ontbijt','lunch'].includes(r.meal_type));
assert.equal(own.length,4);
for(const r of own){assert.equal(r.servings,4);assert.ok(r.ingredients.every(i=>i.quantity>0&&i.name));assert.ok(r.instructions.length>=4);assert.equal(r.cost,null);assert.equal(r.macros,null);}

assert.ok(!p.compatible(p.profile('Jumbo Scharrel Kipfilet Gerookt 120 g',{ingredient:true}),p.profile('kipfilet broodbeleg',{ingredient:true})),'Smoked deli does not become plain deli');

for(const [name,meal] of [['magere kwark','ontbijt'],['kipfilet broodbeleg','lunch']]){
 const item={...offer('basis',name+' 500 g'),pack_label:'500 g',price:2};
 const r={meal_type:meal,servings:4,ingredients:[{name,quantity:1000,unit:'g'},{name:'tomaten',quantity:400,unit:'g'}]};
 const catalog={source_date:day,stores:{jumbo:[[name+' 500 g',1.5,'500 g','https://www.jumbo.com/producten/']]}};
 const products=s.actionProducts(r,[item,tomato],engine,day,{catalog,store:'jumbo'});
 assert.equal(products.find(x=>x.family!== 'tomaten')?.priceAssessment.status,'overpriced','Fresh shelf alternatives must include '+meal+' protein');
}
