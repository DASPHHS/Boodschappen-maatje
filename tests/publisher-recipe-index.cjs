'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const index=JSON.parse(fs.readFileSync('docs/data/publisher-recipes.json','utf8'));
const e=require('../docs/recipe-discovery.js');
assert.ok(index.recipes.length>=75,'At least 35 verified recipe page candidates from publishers');
const urls=new Set(),families=new Set(),methods=new Set();
for(const r of index.recipes){
 assert.ok(!urls.has(r.url),'Canonical recipe URLs must be unique: '+r.url);urls.add(r.url);
 assert.match(r.title,/\S{5}/);
 assert.ok((r.source==='Allerhande'&&r.url.startsWith('https://www.ah.nl/allerhande/'))||
  (r.source==='Jumbo'&&r.url.startsWith('https://www.jumbo.com/recepten/'))||
  (r.source==='Voedingscentrum'&&r.url.startsWith('https://www.voedingscentrum.nl/recepten/gezond-recept/'))||
  (r.source==='24Kitchen'&&r.url.startsWith('https://www.24kitchen.nl/recepten/'))||
  (r.source==='HelloFresh'&&/^https:\/\/www\.hellofresh\.nl\/recipes\/[a-z0-9_-]+-[0-9a-f]{24}$/.test(r.url)),'Trusted publishing host only');
 assert.ok(['handmatig_gevonden_bij_uitgever','publisher_metadata_verified','publisher_page_title_verified','publisher_sitemap_title_only'].includes(r.review_status));
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
// Each new publisher must be visible in the deal -> recipe matching mechanism.
for(const [name,category,source] of [
 ['Broccoli','groente','Voedingscentrum'],
 ['Kikkererwten','vega','24Kitchen'],
 ['Kabeljauwfilet','vis','Voedingscentrum'],
 ['Boerenkool','groente','Voedingscentrum']
]){
 const hits=e.publisherMatches({name,category},index,100);
 assert.ok(hits.some(x=>x.recipe.source===source),name+' should match '+source);
}
const forged={recipes:[{title:'Fictieve brochure',source:'Voedingscentrum',
 url:'https://www.voedingscentrum.nl.attacker.example/recepten/gezond-recept/fake',
 families:['broccoli'],review_status:'handmatig_gevonden_bij_uitgever'}]};
assert.deepEqual(e.publisherMatches({name:'Broccoli',category:'groente'},forged),[],
 'Reject lookalike publisher domains');
assert.ok(index.recipes.filter(x=>x.source==='HelloFresh').length>=6,'HelloFresh must appear as first-class curated publisher');
assert.ok(index.recipes.some(x=>x.source==='Allerhande'&&/rendang/i.test(x.title)),'Allerhande should include proper stews');
assert.ok(e.publisherMatches({name:'Kipfilet',category:'kip'},index,100).some(x=>x.recipe.source==='HelloFresh'),'HelloFresh chicken recipes should be searchable by an offer');
const spoof={recipes:[{source:'HelloFresh',title:'Fake',url:'https://www.hellofresh.nl.evil.example/recipes/kip-5e4a3e6bb19a1757fe76da26',families:['kip'],review_status:'publisher_page_title_verified'}]};
assert.deepEqual(e.publisherMatches({name:'Kipfilet',category:'kip'},spoof),[]);
const fakeVeg={recipes:[{source:'HelloFresh',
 title:'Masala-pasta met veggie gehakt',
 url:'https://www.hellofresh.nl/recipes/veggie-gehakt-pasta-6a16d7667200e2f203e8d767',
 families:['gehakt'],review_status:'publisher_page_title_verified'}]};
assert.deepEqual(e.publisherMatches({name:'Gemengd gehakt',category:'vlees'},fakeVeg),[],
 'Plant-based replacement cannot match animal mince offers');
console.log('Publisher index:',index.recipes.length,'curated real links,',families.size,'ingredient families, ranked and diversified');
