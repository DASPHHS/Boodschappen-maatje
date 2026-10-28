const assert=require('node:assert/strict');
const p=require('../docs/price-integrity.js');
const base={cost:{basket_total:9.41,estimated:true,verified_today:false},ingredients:[
{name:'Tofu',pack_price:3.9,price_observed_at:'2026-10-27'},
{name:'Broccoli',pack_price:5.51,price_observed_at:'2026-10-28'}]};
const a=p.basket(base,'2026-10-28');
assert.equal(a.state,'historical_estimate');
assert.equal(a.total,9.41);
assert.equal(a.stale,true);
assert.equal(p.basket({...base,ingredients:[...base.ingredients,{name:'Paprika',pack_price:null}]},'2026-10-28').state,'partial');
assert.equal(p.basket({...base,cost:{basket_total:9,estimated:false,verified_today:true}},'2026-10-28').state,'historical_estimate');
assert.equal(p.basket({...base,cost:{basket_total:9.41,estimated:false,verified_today:true}},'2026-10-28').state,'historical_estimate');
assert.equal(p.basket({...base,cost:{basket_total:9.41,estimated:false,verified_today:true,verification_level:'retailer_product_pages'},store:'jumbo',ingredients:base.ingredients.map(i=>({...i,price_observed_at:'2026-10-28',price_status:'retailer_price_confirmed',source_url:'https://www.jumbo.com/producten/foo'}))},'2026-10-28').state,'today_confirmed');
assert.equal(p.basket({...base,cost:{basket_total:9.41,estimated:false,verified_today:true,verification_level:'retailer_product_pages'},store:'lidl',ingredients:base.ingredients.map(i=>({...i,price_observed_at:'2026-10-28',price_status:'retailer_price_confirmed',source_url:'https://www.jumbo.com/producten/foo'}))},'2026-10-28').state,'historical_estimate');
assert.equal(p.liquidLitres('6x330ML'),1.98);
assert.equal(p.liquidLitres('6 × 300 ml'),1.8);
assert.equal(p.unitCost({price:8.61,pack_label:'6x330ML'}).price,4.35);
assert.equal(p.unitCost({price:7.49,pack_label:'6x300ML'}).price,4.16);
assert.equal(p.liquidLitres('330 ml'),0.33);
assert.equal(p.unitCost({price:1.75,pack_label:'330 ml'}).price,5.3);
console.log('Cash basket status, missing ingredients, stale dates and beer pack prices verified');
