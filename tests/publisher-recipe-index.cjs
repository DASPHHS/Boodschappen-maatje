'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const index=JSON.parse(fs.readFileSync('docs/data/publisher-recipes.json','utf8'));
const e=require('../docs/recipe-discovery.js');
assert.ok(index.recipes.length>=35,'At least 35 verified recipe page candidates from publishers');
const urls=new Set(),families=new Set(),methods=new Set();
for(const r of index.recipes){
 assert.ok(!urls.has(r.url),'Canonical recipe URLs must be unique: '+r.url);urls.add(r.url);
 assert.match(r.title,/\S{5}/);
 assert.ok((r.source==='Allerhande'&&r.url.startsWith('https://www.ah.nl/allerhande/'))||
  (r.source==='Jumbo'&&r.url.startsWith('https://www.jumbo.com/recepten/')),'Trusted publishing host only');
 assert.ok(['handmatig_gevonden_bij_uitgever','publisher_metadata_verified'].includes(r.review_status));
 assert.ok(Array.isArray(r.families)&&r.families.length>0);
 r.families.forEach(x=>families.add(x));if(r.method)methods.add(r.method);
 assert.ok(!r.instructions&&!r.recipeInstructions&&!r.image,'Do not copy recipe text or images');
}
assert.ok(families.size>=18,'Broad ingredient coverage');
for(const [name,type] of [['Runderriblappen','riblappen'],['Kikkererwten','kikkererwten'],
 ['Broccoli','broccoli'],['Zalmfilet','zalm'],['Tofu naturel','tofu'],['Pompoen','pompoen'],
 ['Spinazie','spinazie'],['Pindakaas','pindakaas']]){
 const offer={name,category:type==='zalm'?'vis':type==='riblappen'?'vlees':'groente'};
 const r=e.publisherMatches(offer,index,12);
 assert.ok(r.length>0,'Published recipe list lacks matches for '+name);
 assert.ok(r.every(x=>x.recipe.families.includes(type)));
}
const mixed=e.offerRecipeHighlights([{name:'Zalmfilet',category:'vis'},
 {name:'Broccoli',category:'groente'},{name:'Kikkererwten',category:'vega'},
 {name:'Tofu',category:'vega'}],index,12);
assert.ok(mixed.length>=8,'Broad deals should yield a range of recipes');
assert.ok(new Set(mixed.map(x=>x.family)).size>=3,'Do not recommend only one ingredient');
assert.ok(!mixed.some(x=>/google.com\/search/.test(x.recipe.url)),'No more search engine result links');
const example=e.publisherMatches({name:'Runderriblappen',category:'vlees'},index,10);
assert.ok(example.some(x=>/rendang/i.test(x.recipe.title)));
console.log('Publisher index:',index.recipes.length,'curated real links,',families.size,'ingredient families, ranked and diversified');
