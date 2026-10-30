'use strict';
const assert=require('node:assert/strict'),fs=require('fs');
const resolver=require('../docs/product-resolver'),sem=require('../docs/product-semantics'),pricing=require('../docs/price-observations'),search=require('../docs/catalog-search');
const watch=JSON.parse(fs.readFileSync('docs/data/watchlist.json')).items;
const profile=key=>watch.find(w=>w.key===key);
const check=(key,name,pack='500 g',extra={})=>resolver.matching({name,pack_label:pack,...extra},profile(key),pricing);
for(const [key,name,pack] of [
 ['kipfilet','Kipfilet Americanos','500 g'],['kipfilet','Vergrill Gerookte Kipfilet Plakjes ca. 150 g','ca. 150 g'],
 ['kipfilet','AH Kipfilet pepersaus met wortel en doperwt','500 g'],
 ['vis','AH Blik brokjes zalm forel','415 g'],['vis','Whiskas zalmfilet','400 g'],
 ['pompoen','Pureersoep pompoen','528 g'],['pompoen','Olvarit 12+ Maanden Knijpfruit Pompoen Wortel Appel','100 g'],
 ['pompoen','AH 85% groenteshot pompoen gele wortel','125 ml'],['sperziebonen','Sperziebonen','720 ml'],
 ['pindakaas','Hero mueslireep pindakaas','100 g'],['sereh','Smoothiemix Citroengras','250 g']
])assert.notEqual(check(key,name,pack).status,'match',key+' must exclude '+name);
for(const [key,name,pack] of [['kipfilet','Jumbo Kipfilet','800 g'],['vis','Alaska koolvis XXL','1.1 kg'],['pompoen','AH Biologisch Flespompoen','1 kg'],['sperziebonen','AH Diepvries Gebroken sperziebonen','450 g']])
 assert.equal(check(key,name,pack).status,'match',name+' is a real base product');
for(const retailer of ['AH','Jumbo','Lidl'])for(const [key,noun] of [['kipfilet','kipfilet'],['vis','koolvis'],['pompoen','pompoen']]){
 for(const prefix of ['Babyvoeding','Hondenvoer','Kattenvoer','Puppy','Olvarit 12 maanden'])
  assert.notEqual(check(key,retailer+' '+prefix+' '+noun).status,'match','Audience rule must apply to new SKUs and brands');
 for(const suffix of ['pepersaus','salade','pureersoep','maaltijd','groentemix'])
  assert.notEqual(check(key,retailer+' '+noun+' '+suffix).status,'match','Prepared-food rule must apply generically');
}
assert.equal(check('kipfilet','Nieuwmerk Kipfilet Verrassing').status,'partial','Unrecognized descriptions require evidence, not an optimistic match');
const chicken=check('kipfilet','AH Kipfilet'),fish=check('vis','AH Koolvis'),salmon=check('vis','AH Zalmfilet');
assert.notEqual(fish.comparison_key,salmon.comparison_key,'Species must have separate comparison rows');
assert.equal(check('kipfilet','AH Gerookte Kipfilet').status,'reject');
assert.notEqual(check('kipfilet','AH Kipfilet','500 ml').status,'match');
const future={title:'Linzenpasta',match:{all:['linzenpasta']}};
assert.equal(resolver.matching({name:'AH Linzenpasta 500 g',pack_label:'500 g'},future,pricing).status,'match');
assert.equal(resolver.matching({name:'AH Linzenpasta maaltijd',pack_label:'500 g'},future,pricing).status,'partial');
const day='2026-10-30';
const fixture={schema_version:1,source_date:day,stores:{ah:[['AH Blik brokjes zalm forel',.75,'415 g','https://www.ah.nl/producten/product/wi1/pet','wi1'],['AH Koolvis',3,'400 g','https://www.ah.nl/producten/product/wi2/fish','wi2']]}};
assert.deepEqual(search.candidates(profile('vis'),'ah',fixture,pricing,resolver,day).map(x=>x.o.name),['AH Koolvis']);
console.log('Semantic policy: screenshot regressions, generated audience/form mutations, units, species and unseen products passed');

const branded={name:'Nieuwmerk Kipfilet',pack_label:'500 g',semantic_evidence:{verified_identity:true,brand:'Nieuwmerk',categories:['Verse kipfilet']}};
assert.equal(resolver.matching(branded,profile('kipfilet'),pricing).status,'match','A verified new brand does not need a SKU exception');
assert.equal(resolver.matching({...branded,name:'Nieuwmerk Kipfilet Verrassing'},profile('kipfilet'),pricing).status,'partial','Broad category evidence must not excuse an unexplained preparation');

assert.equal(check('sperziebonen','AH Gebroken sperziebonen','660 g').status,'partial','Jar net weight cannot be presumed to be fresh/frozen edible weight');
