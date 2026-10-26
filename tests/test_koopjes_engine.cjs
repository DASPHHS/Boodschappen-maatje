const assert=require('node:assert/strict'),E=require('../docs/koopjes/engine.js');
assert.equal(E.status(null,'2026-11-01','2026-10-26'),'unknown');
assert.equal(E.status('2026-10-27','2026-11-01','2026-10-26'),'upcoming');
assert.equal(E.status('2026-10-01','2026-10-25','2026-10-26'),'expired');
assert.equal(E.day('2026-02-31'),null);
assert.deepEqual(E.measure('Wasmiddel 40 wasbeurten',1000,'ml'),{amount:40,unit:'wasbeurt'});
assert.deepEqual(E.measure('Vaatwastabletten 60 tabletten',60,'st'),{amount:60,unit:'tablet'});
assert.equal(E.measure('Toiletpapier 8 rollen',8,'st'),null);
assert.deepEqual(E.measure('Shampoo',250,'ml'),{amount:2.5,unit:'100 ml'});
const promo=(name,start,end)=>[name,2,500,'g',4,2,4,'1+1 gratis',end,'https://example.com/product',false,start];
const rows=E.catalog({stores:{ah:{ordinary:[['Spinazie',3,500,'g','https://example.com/s']],promotions:[promo('Spinazie','2026-10-26','2026-11-01'),promo('Toekomst','2026-11-02','2026-11-08'),promo('Onbekend',null,null)]}}},'2026-10-26');
assert.equal(rows.length,2);const sale=rows.find(x=>x.state==='active');assert.equal(sale.price,4);assert.equal(sale.packages,2);assert.equal(sale.unitPrice,4);assert.equal(sale.discount,50);
assert.equal(E.search(rows,{q:'spinazie',sale:true}).length,1);
assert.equal(E.search(rows,{q:'kipfilet'}).length,0);
console.log('Koopjes: datums, bundels, eenheden, zoeken en filters geslaagd');

assert.deepEqual(E.measure('Jumbo vaatwastabletten 40 x 19g',760,'g'),{amount:40,unit:'tablet'});
assert.deepEqual(E.measure('AH vaatwastabletten',60,'st'),{amount:60,unit:'tablet'});
