'use strict';
const assert=require('node:assert/strict'),products=require('../docs/recipe-products'),engine=require('../docs/recipe-discovery'),selector=require('../docs/publisher-selection');
const day='2026-11-02';
const offer=(id,name,price=2,regular=3,pack='400 g')=>({id,name,price,regular_price:regular,pack_label:pack,start_date:day,end_date:'2026-11-08',source_provider:'PrijsProfeet',promotion_status:'active',source:{url:'https://www.prijsprofeet.nl/'}});
const recipe=(id,source,ingredients)=>({id,title:id+' met groenten',source,url:source==='HelloFresh'?'https://www.hellofresh.nl/recipes/'+id+'-'+'a'.repeat(24):'https://www.ah.nl/allerhande/recept/R-R123/'+id,servings:4,minutes:35,review_status:'publisher_metadata_verified',ingredient_profile_version:products.VERSION,ingredient_profiles:ingredients.map(x=>products.profile(x,{ingredient:true})).filter(Boolean)});
const kip=recipe('kip','HelloFresh',['800 g kipfilet','600 g broccoli','600 g aubergine']);
const vis=recipe('zalm','Allerhande',['800 g zalmfilet','600 g broccoli','600 g aubergine']);
const offers=[offer('k','AH Kipfilet',4,7),offer('b','Broccoli',1.7,2),offer('a','Aubergine',1.7,2)];
let rows=selector.recipesForOffers({index:{recipes:[vis,kip]},stores:['ah'],offersByStore:{ah:offers},engine,day});
assert.equal(rows.length,2);assert.equal(rows[0].recipe.id,'kip','Main discount must outrank two small vegetable savings');
assert.equal(rows[0].matched.mainSaving,6,'800 g needs two 400 g packs, saving 6 euros');
assert.equal(rows[1].matched.hasMain,false,'A salmon recipe is not a main-ingredient deal when only vegetables are reduced');
assert.equal(selector.recipesForOffers({index:{recipes:[vis,kip]},stores:['ah'],offersByStore:{ah:offers},engine,day,basis:'main'}).length,1);
assert.equal(selector.recipesForOffers({index:{recipes:[kip]},stores:['ah'],offersByStore:{ah:[offers[0]]},engine,day}).length,0,'Never relax the two-product rule');
const wrong=[
 ['Honig Bakplaat Mix Aardappel, Broccoli & Vissticks 36g','600 g broccoli'],
 ['Honig Bakplaat Mix Aardappel, Bloemkool & Kip 36g','600 g bloemkool'],
 ['Vivera Vegetarische Spinazie Kaas Filet 2 Stuks 200 g','600 g spinazie'],
 ['Vivera Plantaardige Zalmfilet 2 Stuks 200 g','800 g zalmfilet'],
 ['Jumbo Gevulde Eieren Pittig 4 Stuks 105 g','4 eieren'],
 ['Maza Hoemoes Paprika & Oregano','600 g paprika'],
 ['Jumbo Champignons Knoflook 100 g','600 g champignons'],
 ['Jumbo Halfgedroogd Tomaten 130 g','400 g tomatenblokjes'],
 ['Jumbo Halfgedroogd Tomaten 130 g','600 g verse tomaten'],
 ['Vivera Zachte Tofu 550 g','800 g stevige tofu'],
 ['Jumbo Kipfilet 400 g','800 g kippendijfilet'],
 ['Jumbo Gemengd Gehakt 500 g','800 g mager rundergehakt'],
 ['Jumbo Scharrel Kipfilet 120 g','800 g kipfilet']
];
for(const [name,ingredient] of wrong){const r={title:'Hoofdgerecht',servings:4,ingredients:[{name:ingredient}]};assert.equal(selector.actionProducts(r,[offer(name,name)],engine,day).length,0,name+' must never stand in for '+ingredient);}
assert.ok(products.compatible(products.profile('Jumbo Tomatenblokjes 400 g'),products.profile('400 g tomatenblokjes',{ingredient:true})));
assert.ok(products.compatible(products.profile('Vivera Stevige Tofu 280 g'),products.profile('600 g stevige tofu',{ingredient:true})));
assert.equal(products.group(recipe('bout','HelloFresh',['2 kippenbouten','600 g aardappelen'])),'kip');
assert.equal(selector.discount({...offers[0],multi_buy_quantity:2},products.recipeProfiles(kip)[0],kip).forFour,null,'Bundle reference ambiguity cannot become a saving claim');
assert.equal(selector.discount(offers[0],{family:'kip'},kip).forFour,null,'Unknown recipe quantity must not create a four-portion saving');
assert.equal(selector.discount({...offers[0],pack_label:'ca. 400 g'},products.recipeProfiles(kip)[0],kip).forFour,null,'Approximate packs have no exact quantity saving');
assert.equal(selector.actionProducts(kip,[{...offers[0],end_date:'2026-11-01'}],engine,day).length,0);
console.log('Protein-basis ranking, four-portion pack savings and all 13 real wrong-product examples verified');

for(const name of ['Jumbo Scharrel Kipfilet','Jumbo Scharrel Kipfilet Voordeelverpakking 200 g','Jumbo Scharrelkipfilet 500 g'])assert.equal(products.profile({name}),null,'Sandwich meat stays excluded regardless of pack size');
assert.ok(products.profile({name:'Lidl Scharrelkipfilet 400 g'}));
assert.ok(products.profile({name:'Jumbo verse scharrel kipfilet 400 g'}));
const semantics=require('../docs/product-semantics');
assert.equal(semantics.classify({name:'Jumbo Scharrel Kipfilet Voordeelverpakking 200 g'}).form,'cooked');
