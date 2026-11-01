'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const selector=require('../docs/publisher-selection.js');
const engine=require('../docs/recipe-discovery.js');
const index=JSON.parse(fs.readFileSync('docs/data/publisher-recipes.json','utf8'));
const app=fs.readFileSync('docs/app.js','utf8');
const html=fs.readFileSync('docs/index.html','utf8');
const offersByStore={ah:[{name:'AH Runderriblappen 850 g',category:'vlees'},
 {name:'AH Bloemkool',category:'groente'},{name:'AH Zalmfilet',category:'vis'}],
 jumbo:[{name:'Jumbo kipfilet vers',category:'kip'}],lidl:[]};
const selection=()=>selector.recipesForOffers({index,stores:['ah','jumbo'],
 offersByStore,engine,query:'',category:'alle'});
const result=selection();
assert.ok(result.length>=12,'Publishers must provide a real browsable recipe selection');
assert.ok(result.slice(0,8).some(x=>x.recipe.source==='Allerhande'));
assert.ok(result.slice(0,8).some(x=>x.recipe.source==='HelloFresh'));
assert.equal(new Set(result.map(x=>x.recipe.url)).size,result.length,
 'Publisher results must be unique canonical pages');
assert.ok(result.every(x=>selector.valid(x.recipe,engine)),
 'Do not display unverifiable sitemap-only records as actual recipes');
assert.ok(result.some(x=>x.matched?.family==='riblappen'&&/hachee/i.test(x.recipe.title)),
 'A real riblap promotion should surface genuine AH hachee');
const hachee=selector.recipesForOffers({index,stores:['ah'],offersByStore,
 engine,query:'hachee',category:'alle'});
assert.ok(hachee.length>=3,'Hachee search should reveal more than one real Allerhande source');
assert.ok(hachee.every(x=>/hachee/i.test(x.recipe.title)));
assert.ok(hachee.every(x=>x.recipe.source==='Allerhande'));
assert.ok(hachee.some(x=>x.recipe.url.includes('R-R8302')),'Include verified classic hachee');
const fish=selector.recipesForOffers({index,stores:['ah'],offersByStore,
 engine,category:'vis'});
assert.ok(fish.length>0);
assert.ok(fish.every(x=>x.category==='vis'));
assert.ok(!result.some(x=>x.recipe.review_status==='publisher_sitemap_title_only'));
assert.ok(app.includes('data-show-recipe-library'),'Mechanical concepts must not dominate default viewport');
assert.ok(app.includes('batch-featured'),'Detailed two-day meals must appear in ordinary browsing');
assert.ok(app.includes('data-more-publishers'),'Many legitimate publisher recipes must be reachable');
assert.ok(html.includes('publisher-selection.js?v=20261101-publisher-first'),
 'Publisher selection must be loaded before the app');
console.log('Publisher-first discovery: '+result.length+' reviewed original recipes; AH hachee, HF, category, browsing and rights verified');
