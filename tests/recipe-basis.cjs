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
const deli={name:'Jumbo Scharrel Kipfilet Voordeelverpakking 200 g',pack_label:'200 g',price:1,ean:'same-ean',product_id:'same-id'};
const raw={name:'kipfilet',quantity:800,unit:'g',ean:'same-ean',product_id:'same-id',pack_price:1,price_status:'folder_current'};
const matcher=require('../docs/product-matcher'),resolver=require('../docs/product-resolver'),pricing=require('../docs/price-observations');
assert.equal(matcher.evaluate(deli,raw).status,'incompatible','EAN cannot override incompatible food preparation');
assert.equal(matcher.priceApplied(deli,raw),false,'Do not apply a sandwich-meat price to raw chicken');
assert.equal(matcher.culinaryOfferSuitability(deli,raw),false);
assert.notEqual(resolver.matching(deli,{title:'Rauwe kipfilet',match:{all:['kipfilet']}},pricing).status,'match');
assert.equal(resolver.matching(deli,{title:'Kipfilet broodbeleg',match:{all:['kipfilet']}},pricing).status,'match','Explicit sandwich-meat preferences remain possible');
assert.equal(products.displayCategory({...deli,category:'kip'}),'vleeswaren');
assert.equal(products.profile(deli,{ingredient:true}).form,'cooked','Old saved ingredient names must not turn deli meat into raw chicken');
console.log('Deli chicken is consistent in classification, exact IDs, price application, resolver and saved ingredient profiles');
// Main-ingredient priority is a hard invariant, even under inflated reference prices.
const inflated=[offers[0],{...offers[1],regular_price:99999},{...offers[2],regular_price:99999}];
const primary=selector.recipesForOffers({index:{recipes:[vis,kip]},stores:['ah'],offersByStore:{ah:inflated},engine,day});
assert.equal(primary[0].recipe.id,'kip');
const premium=offer('premium','Zalmfilet',30,90);
const spending=selector.recipesForOffers({index:{recipes:[vis,kip]},stores:['ah'],offersByStore:{ah:[...offers,premium]},engine,day});
assert.equal(spending[0].recipe.id,'kip','A huge advertised saving cannot beat lower actual protein spend');
const catalogNow={source_date:day,stores:{ah:[['AH Kipfilet',2,'400 g','https://www.ah.nl/producten/product/wi123/kip','123']]}};
const checked=selector.actionProducts(kip,offers,engine,day,{catalog:catalogNow,store:'ah'}).find(x=>x.isMain);
assert.equal(checked.priceAssessment.status,'overpriced');assert.equal(checked.priceAssessment.alternative.total,4);
const old={...catalogNow,source_date:'2026-10-01'};
assert.equal(selector.actionProducts(kip,offers,engine,day,{catalog:old,store:'ah'}).find(x=>x.isMain).priceAssessment.status,'unknown','Stale shelf prices never prove attractiveness');
assert.equal(selector.purchase({...offers[0],multi_buy_quantity:3,multi_buy_price:10},products.recipeProfiles(kip)[0],kip).total,10);
assert.equal(selector.purchase({...offers[0],multi_buy_quantity:3,multi_buy_price:10},products.recipeProfiles(kip)[0],kip).packages,3,'Pay for all required bundle units');
const tooBig=offer('big','AH Kipfilet',8,10,'1000 g'),smallPack=offer('small','AH Kipfilet',4,5,'400 g');
assert.equal(selector.actionProducts({...kip,ingredient_profiles:[products.profile('300 g kipfilet',{ingredient:true})]},[tooBig,smallPack],engine,day)[0].offer.id,'small','A lower kilo price can still cost more at checkout');
console.log('Main priority, actual protein spend, cheaper regular alternatives, stale evidence and mandatory bundles verified');

const independentlyRefreshed={source_date:'2026-10-01',stores:{ah:[['AH Kipfilet',99,'400 g','https://www.ah.nl/producten/product/wi123/kip','123',{status:'ok',verified_identity:true,checked_at:day,observed_price:2,product_pack:'400 g'}]]}};
assert.equal(selector.actionProducts(kip,offers,engine,day,{catalog:independentlyRefreshed,store:'ah'}).find(x=>x.isMain).priceAssessment.alternative.total,4,'Use a newly observed price, not the obsolete catalog price');
