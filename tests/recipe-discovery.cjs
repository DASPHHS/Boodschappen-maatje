'use strict';
const assert=require('node:assert/strict');
const discover=require('../docs/recipe-discovery.js');
const rib={id:'sale-rib',name:'Runderriblappen 750 g',category:'vlees',price:8.99,
 start_date:'2026-11-01',end_date:'2026-11-07'};
const klassiek=discover.classify(rib);
assert.equal(klassiek.key,'riblappen');
assert.deepEqual(klassiek.tags.slice(0,2),['rendang','hachee']);
assert.ok(klassiek.links.some(x=>x.title.includes('Rendang')&&x.url.includes('ah.nl/allerhande/recept/')));
assert.ok(klassiek.links.some(x=>x.title.includes('Hachee')));
assert.ok(klassiek.links.some(x=>x.url.includes('jumbo.com/recepten/')));
const stroef=discover.matchRecipe(rib,{id:'r1',title:'Runderstoof met spitskool',minutes:165,
 quality_status:'uitgewerkt_niet_culinair_getest',ingredients:[{name:'runderriblappen',quantity:800,unit:'g'}]});
assert.ok(stroef,'A riblap stew must be suggested');
assert.equal(discover.matchRecipe(rib,{id:'fast',title:'Biefstukreepjes kort gebakken',minutes:20,
 ingredients:[{name:'biefstuk',quantity:800,unit:'g'}]}),null,'Never substitute quick steak');
assert.equal(discover.matchRecipe(rib,{id:'fast',title:'Snelle runderpan',minutes:20,
 ingredients:[{name:'runderriblappen',quantity:800,unit:'g'}]}),null,'Tough meat cannot become fast stir-fry');
for(const [name,category,key] of [
 ['Jumbo Kipfilet naturel 800 g','kip','kip'],
 ['AH Zalmfilet 500 g','vis','zalm'],
 ['Lidl Kabeljauwfilet 400 g','vis','witvis'],
 ['AH Tofu Naturel 500g','vega','tofu'],
 ['Jumbo Kikkererwten 400 g','vega','kikkererwten'],
 ['Lidl Broccoli 500 g','groente','broccoli'],
 ['Jumbo Bloemkoolroosjes 500 g','groente','bloemkool'],
 ['AH Courgette 1 stuk','groente','courgette'],
 ['Lidl Paprika rood','groente','paprika'],
 ['AH Eieren 6 stuks','vega','eieren'],
 ['Jumbo Pindakaas Naturel','voorraad','pindakaas'],
 ['AH Champignons 400 g','groente','champignons']]){
  assert.equal(discover.classify({name,category})?.key,key,name+' should generate recipe ideas');
}
for(const [name,category] of [
 ['Runderburger 300 g','vlees'],['Olvarit Babyvoeding met broccoli','groente'],
 ['Whiskas met zalmfilet kattenvoer','vis'],['Kipfilet in champignonroomsaus','kip'],
 ['Vega runder-riblappen','vlees'],['Runder riblappen marinade saus','vlees'],
 ['Dreft vaatwastabletten','huishouden'],['Texels speciaalbier','bier'],['Cola Zero','dranken'],
 ['Gerookte zalmfilet','vis'],['Spinazie à la crème ovenschotel','groente']]){
  assert.equal(discover.classify({name,category}),null,name+' is not proven suitable for raw recipe replacement');
}
const good={title:'Kabeljauwstoof',minutes:35,
 ingredients:[{name:'kabeljauwfilet',quantity:600,unit:'g'}],quality_status:'uitgewerkt_niet_culinair_getest'};
const bad={title:'Ovenvis concept',minutes:45,
 ingredients:[{name:'kabeljauwfilet',quantity:600,unit:'g'}],quality_status:'concept_niet_culinair_getest'};
assert.deepEqual(discover.localMatches({name:'Kabeljauwfilet',category:'vis'},[bad,good]).map(x=>x.recipe.title),['Kabeljauwstoof'],
 'Do not highlight incomplete, unreviewed recipe drafts');
assert.deepEqual(discover.localMatches({name:'Dreft vaatwastabletten',category:'huishouden'},[good]),[]);
const more=discover.publisherSearch(rib);
assert.equal(more.length,2);
assert.ok(more[0].url.startsWith('https://www.google.com/search?q='));
assert.ok(decodeURIComponent(more[0].url).includes('site:ah.nl/allerhande/recept/'));
console.log('Cooking from deals: riblappen => rendang/hachee/stoof; 12 additional food types; rejects processed, pet, unrelated & fake fast recipes');
