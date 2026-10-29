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
