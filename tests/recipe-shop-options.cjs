const assert=require('node:assert/strict');
const options=require('../docs/recipe-shop-options.js');
const pricing=require('../docs/price-observations.js');
const resolver=require('../docs/product-resolver.js');
const today='2026-10-29',url='https://github.com/supermarkt/checkjebon/blob/main/data/supermarkets.json';
const catalog={schema_version:1,source_date:today,source_url:url,stores:{
 ah:[
 ['AH Broccoli 500 g',1.79,'500 g','https://www.ah.nl/producten/product/wi100/broccoli','wi100'],
 ['AH Broccoli 1 kg',2.99,'1 kg','https://www.ah.nl/producten/product/wi101/broccoli','wi101'],
 ['AH Broccoli soep 1 kg',0.5,'1 kg',null,'wi102'],
 ['AH Magere kwark 500 g',1.49,'500 g','https://www.ah.nl/producten/product/wi103/kwark','wi103'],
 ['AH Magere kwark drank 1 l',.49,'1 l',null,'wi104'],
 ['AH Courgette',.39,'per stuk',null,'wi105']
 ],jumbo:[],lidl:[]}};
const recipe={ingredients:[{name:'broccoli',quantity:800,unit:'g'},{name:'magere kwark',quantity:400,unit:'g'},{name:'courgette',quantity:600,unit:'g'},{name:'knoflook',quantity:10,unit:'g'}]};
const p=options.recommend(recipe,'ah',catalog,pricing,resolver,today);
assert.equal(p.available,true);assert.equal(p.required,4);assert.equal(p.matched,2);
const broccoli=p.rows.find(x=>x.ingredient==='broccoli');
assert.equal(broccoli.pack_label,'1 kg');
assert.equal(broccoli.pack_count,1);
assert.equal(broccoli.purchase_total,2.99,'One 1 kg pack cheaper than two 500 g packs');
const kwark=p.rows.find(x=>x.ingredient==='magere kwark');
assert.equal(kwark.purchase_total,1.49,'Real price must include whole purchased pack');
assert.equal('basket_total' in p,false,'Do not imply an actual or complete basket price');
assert.equal(options.recommend(recipe,'ah',{...catalog,source_date:'2026-10-20'},pricing,resolver,today).matched,0);
assert.equal(options.recommend(recipe,'lidl',catalog,pricing,resolver,today).matched,0);
console.log('Real external price options: whole packs, strict exclusion, stale source fallback and incomplete basket');
const fixture={...catalog,stores:{ah:[
 ['Zonnebloemolie',2,'1 l',null,'oil'],
 ['Paprikapoeder',1,'50 g',null,'spice'],
 ['Eieren',3,'6 stuks',null,'eggs'],
 ['Courgette',.50,'per stuk',null,'courgette'],
 ['Boursin knoflook',.10,'150 g',null,'wrong'],
 ['Knoflook',1.50,'150 g',null,'garlic']
]}};
const meal={ingredients:[{name:'zonnebloemolie',quantity:20,unit:'ml'},
 {name:'paprikapoeder',quantity:6,unit:'g'}, {name:'eieren',quantity:8,unit:'st'}]};
const full=options.estimate(meal,'ah',fixture,pricing,resolver,today);
assert.equal(full.state,'catalog_estimate');assert.equal(full.total,9);
assert.equal(full.rows.find(x=>x.ingredient==='eieren').pack_count,2);
assert.equal(full.rows.find(x=>x.ingredient==='zonnebloemolie').consumption_total,.04);
assert.equal(full.unverified,true,'External catalog prices must remain indications');
const incomplete=options.estimate({ingredients:[...meal.ingredients,{name:'courgette',quantity:600,unit:'g'}]},'ah',fixture,pricing,resolver,today);
assert.equal(incomplete.total,null,'Never invent a vegetable weight from a per-piece pack');
assert.equal(incomplete.partial,9);assert.deepEqual(incomplete.missing,['courgette']);
const garlic=options.estimate({ingredients:[{name:'knoflook',quantity:10,unit:'g'}]},'ah',fixture,pricing,resolver,today);
assert.equal(garlic.rows[0].product,'Knoflook','Garlic cheese is not garlic');
assert.equal(options.estimate(meal,'ah',{...fixture,source_date:'2026-11-01'},pricing,resolver,today).partial,0);
assert.equal(options.estimate(meal,'ah',{...fixture,source_date:'2026-10-20'},pricing,resolver,today).partial,0);
// Flavor words must not turn mixed foods, pet food, powders or soft tofu into raw ingredients.
for(const [ingredient,wrong,pack] of [
 ['knoflook','AH Knoflook croutons','100 g'],['knoflook','AH Knoflook gemalen','40 g'],
 ['paprika','Aviko Wavy blends paprika','600 g'],['verse paprika','AH Paprika mild gemalen','39 g'],
 ['wortel','AH Tuinerwten en wortel','500 g'],['prei','VP prei kerriesoep','500 g'],
 ['ras el hanout','Maza Hoemoes Ras el Hanout','200 g'],['appel','AH Rode kool met appel','500 g'],
 ['spinazie','AH Spinazie à la crème','500 g'],['dille',"Jumbo's Paté Kip en Dille Puppy",'150 g'],
 ['biefstuk','Redefine Meat Plantaardige Biefstuk','200 g'],['tahin','Chtoura Hummus Tahin','430 g'],
 ['miso','Nissin Demae ramen miso','100 g'],['stevige tofu','Vivera Zachte Tofu','550 g'],
 ['tomaten','Jumbo Tomaten Gepeld','400 g'],['zalmfilet','Wilde zalmfilet in blik','200 g']
]){
 const source={...catalog,stores:{ah:[[wrong,.10,pack,null,'wrong']]}};
 const result=options.estimate({ingredients:[{name:ingredient,quantity:100,unit:'g'}]},'ah',source,pricing,resolver,today);
 assert.equal(result.total,null,ingredient+' must not use '+wrong);
}
