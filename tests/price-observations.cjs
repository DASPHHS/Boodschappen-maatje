const assert=require('node:assert/strict');
const price=require('../docs/price-observations.js');
const mock={};new Function('window',require('node:fs').readFileSync('docs/favorites.js','utf8'))(mock);
const fav=mock.MaatjeFavorites;
const day='2026-10-29';
const milk={store:'ah',group:'volle_melk',name:'AH Verse volle melk 1 L',price:1.39,
 quantity:1000,unit:'ml',status:'official_regular_observed',checked_date:'2026-10-28',
 url:'https://www.ah.nl/producten/product/wi1524/volle-melk'};
const fakeBundle={id:'ah-three',name:'AH Verse volle melk 3 stuks',pack_label:'3 stuks',price:5.67,
 start_date:'2026-10-27',end_date:'2026-11-03',verified:true,source:{url:'https://www.ah.nl/bonus'}};
assert.equal(price.pack(fakeBundle),null,'unknown 3-pack content cannot be normalized');
assert.equal(price.unitCost(fakeBundle),null,'no inferred litre price for bundle');
let ah=price.collect('ah','volle_melk',[milk],[fakeBundle],day);
assert.equal(ah.length,1,'3-stuks must never displace 1-litre fresh milk');
assert.equal(ah[0].o.price,1.39);
assert.equal(ah[0].unit.unit,'L');
assert.equal(ah[0].unit.price,1.39);
assert.ok(ah[0].label.includes('2026-10-28'));
assert.equal(price.collect('lidl','volle_melk',[milk],[fakeBundle],day).length,0);
const stale=price.inspect({...milk,checked_date:'2026-10-01'},'ah',day);
assert.equal(stale.fresh,false,'old price must not be called current');
assert.equal(stale.status,'oud');
assert.ok(stale.label.includes('2026-10-01'));
assert.equal(price.pack({pack_label:'6 × 330 ml'}).amount,1.98);
assert.equal(price.pack({pack_label:'6x300ml'}).amount,1.8);
assert.equal(price.unitCost({pack_label:'6x330ml',price:8.61}).price,4.35);
assert.equal(price.unitCost({pack_label:'750 g',price:4.99}).price,6.65);
assert.equal(price.unitCost({pack_label:'ca. 350 g',price:4.49}),null);
assert.equal(price.unitCost({pack_label:'5 dozen, variabele tabletaantallen',price:37.98}),null);
assert.equal(price.matchesWatch(fakeBundle,'volle_melk'),false);
assert.equal(price.matchesWatch(milk,'volle_melk'),true);
const future={...fakeBundle,pack_label:'1 L',start_date:'2026-11-01',end_date:'2026-11-03'};
assert.equal(price.collect('ah','volle_melk',[],[future],day).length,0);
const unknown={name:'Page Vochtig Toiletpapier',pack_label:'inhoud onbekend',price:0.99,
 source_provider:'PrijsProfeet',start_date:'2026-10-26',end_date:'2026-11-01',source:{url:'https://www.prijsprofeet.nl'}};
assert.equal(price.unitCost(unknown),null);
const obs=price.inspect(unknown,'jumbo',day);
assert.equal(obs.label.startsWith('externe actiemelding'),true);
const regular={store:'ah',name:'La Chouffe Blond',pack_label:'0,33 l',price:1.75,
 status:'official_regular_observed',checked_date:'2026-10-28',url:'https://www.ah.nl/producten/product/wi12345/beer'};
const favorite={store:'ah',name:'La Chouffe Blond',pack_label:'330 ml'};
const rows=price.favoriteRows('ah',[favorite],[regular],[],fav,day);
assert.equal(rows.length,1,'show known regular price also when no promotion is active');
assert.equal(rows[0].exact,true);
assert.equal(rows[0].unit.price,5.3);
assert.equal(fav.dedupe([favorite,regular]).length,1);
assert.equal(fav.same({name:'Texels Skuumkoppe Bier Fles 6x300ml',pack_label:'6x300ml',store:'jumbo'},
 {name:'Texels Skuumkoppe Bier Blik 6x300ml',pack_label:'6x300ml',store:'jumbo'},'jumbo'),false);
console.log('Personal-price coverage, milk bundle mismatch, historical dates, exact packs and regular favorites validated');
