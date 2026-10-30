const assert=require('node:assert/strict');
const price=require('../docs/price-observations.js');
const mock={};new Function('window',require('node:fs').readFileSync('docs/favorites.js','utf8'))(mock);
const fav=mock.MaatjeFavorites;
const day='2026-10-29';
const milk={store:'ah',group:'volle_melk',name:'AH Houdbare volle melk 1 L',price:0.99,
 quantity:1000,unit:'ml',status:'official_regular_observed',checked_date:'2026-10-28',
 url:'https://www.ah.nl/producten/product/wi1524/volle-melk'};
const fakeBundle={id:'ah-three',name:'AH Verse volle melk 3 stuks',pack_label:'3 stuks',price:5.67,
 start_date:'2026-10-27',end_date:'2026-11-03',verified:true,source:{url:'https://www.ah.nl/bonus'}};
assert.equal(price.pack(fakeBundle),null,'unknown 3-pack content cannot be normalized');
assert.equal(price.unitCost(fakeBundle),null,'no inferred litre price for bundle');
assert.equal(price.pack({...fakeBundle,status:'official_regular_observed',quantity:1000,unit:'ml'}),null,'structured quantity cannot override explicit unknown bundle');
let ah=price.collect('ah','volle_melk',[milk],[fakeBundle],day);
assert.equal(ah.length,1,'3-stuks must never displace 1-litre fresh milk');
assert.equal(ah[0].o.price,0.99);
assert.equal(ah[0].unit.unit,'L');
assert.equal(ah[0].unit.price,0.99);
assert.ok(ah[0].label.includes('2026-10-28'));
assert.equal(price.collect('lidl','volle_melk',[milk],[fakeBundle],day).length,0);
const stale=price.inspect({...milk,checked_date:'2026-10-01'},'ah',day);
assert.equal(stale.fresh,false,'old price must not be called current');
assert.equal(stale.status,'oud');
assert.ok(stale.label.includes('2026-10-01'));
assert.equal(price.inspect({...milk,checked_date:'2026-10-30'},'ah',day),null);
assert.equal(price.pack({pack_label:'6 × 330 ml'}).amount,1.98);
assert.equal(price.pack({pack_label:'6x300ml'}).amount,1.8);
assert.equal(price.unitCost({pack_label:'6x330ml',price:8.61}).price,4.35);
assert.equal(price.unitCost({pack_label:'750 g',price:4.99}).price,6.65);
assert.equal(price.unitCost({pack_label:'ca. 350 g',price:4.49}),null);
assert.equal(price.unitCost({pack_label:'5 dozen, variabele tabletaantallen',price:37.98}),null);
assert.equal(price.matchesWatch(fakeBundle,'volle_melk'),false);
assert.equal(price.matchesWatch(milk,'volle_melk'),true);
assert.equal(price.matchesWatch({...milk,name:'AH Verse volle melk 1 L'},'volle_melk'),false);
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

assert.equal(price.unitCost({name:'Dreft vaatwascapsules',pack_label:'19 stuks',price:13.99}).unit,'stuk');
assert.equal(price.unitCost({name:'Dreft vaatwascapsules',pack_label:'19 stuks',price:13.99}).price,.74);
assert.equal(price.pack({name:'AH Bospeen',pack_label:'per bos'}).unit,'bos');

assert.equal(price.packLabel({name:'Jumbo Kipfilet 800 g',pack_label:''}),'800 g (volgens productnaam)');
assert.equal(price.packLabel({name:'Bier 6x330ml',pack_label:''}),'6 × 330 ml (volgens productnaam)');
assert.equal(price.packLabel({name:'Bospeen',pack_label:''}),'inhoud niet bevestigd');
for(const pack_label of ['250-295 g','250 – 300 g','0,5-1 kg'])assert.equal(price.pack({name:'Productvarianten',pack_label}),null,'Weight ranges are not exact packs');
