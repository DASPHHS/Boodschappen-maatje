const assert=require('node:assert/strict');
const search=require('../docs/catalog-search.js');
const pricing=require('../docs/price-observations.js');
const resolver=require('../docs/product-resolver.js');
const fs=require('node:fs');
const watch=JSON.parse(fs.readFileSync('docs/data/watchlist.json','utf8')).items;
const today='2026-10-29';
const catalog={schema_version:1,source:'checkjebon-public-dataset',
  source_date:today,source_url:'https://github.com/supermarkt/checkjebon/blob/main/data/supermarkets.json',
  stores:{
    lidl:[['Houdbare volle melk',.98,'1 L',null,'128759'],['Verse volle melk',.94,'1 L',null,'00021']],
    jumbo:[['Jumbo Houdbare Volle Melk 1 L',.99,'1 L','https://www.jumbo.com/producten/jumbo-houdbare-volle-melk-1-l-49608STK','49608STK']],
    ah:[['AH Houdbare volle melk',1.29,'1 l','https://www.ah.nl/producten/product/wi450535/ah-houdbare-volle-melk','wi450535'],
      ['AH Lactosevrije houdbare volle melk',1.49,'1 l','https://www.ah.nl/producten/product/wi448315/lactosevrije-volle-melk','wi448315'],
      ['AH Verse volle melk',1.39,'1 l','https://www.ah.nl/producten/product/wi1524/volle-melk','wi1524'],
      ['AH Magere kwark',1.49,'500 g','https://www.ah.nl/producten/product/wi63453/ah-magere-kwark','wi63453'],
      ['AH Cottage cheese',.74,'200 g','https://www.ah.nl/producten/product/wi000001/ah-cottage','wi000001'],
      ['AH Bospeen',1.55,'per bos','https://www.ah.nl/producten/product/wi127590/ah-bospeen','wi127590']]
  }};
const milk=watch.find(x=>x.key==='volle_melk');
assert.ok(search.valid(catalog,today));
assert.equal(search.candidates(milk,'lidl',catalog,pricing,resolver,today)[0].o.price,.98);
assert.equal(search.candidates(milk,'jumbo',catalog,pricing,resolver,today)[0].o.price,.99);
assert.equal(search.candidates(milk,'ah',catalog,pricing,resolver,today)[0].o.price,1.29);
assert.equal(search.candidates(milk,'ah',catalog,pricing,resolver,today).length,2,
  'Lactose-free variation is distinguishable and may require stricter user intent');
const older=[{store:'ah',name:'AH Houdbare volle melk 1 L',pack_label:'1 L',
  group:'volle_melk',status:'external_regular_observed',price:.99,
  checked_date:today,url:'https://www.ah.nl/producten/product/wi450535/ah-houdbare-volle-melk'}];
const picked=search.combined(milk,'ah',catalog,older,[],pricing,resolver,today);
assert.equal(picked[0].o.price,1.29,'Newer catalog wins over stale seeded value of the same SKU');
assert.equal(picked.filter(x=>x.o.url===older[0].url).length,1,'Same product may not have two conflicting rows');
const kwark=watch.find(x=>x.key==='kwark');
const rows=search.candidates(kwark,'ah',catalog,pricing,resolver,today);
assert.equal(rows.length,1,'Cottage cheese is not magere kwark');
assert.equal(rows[0].o.price,1.49);
const bos=watch.find(x=>x.key==='bospeen');
assert.equal(search.candidates(bos,'ah',catalog,pricing,resolver,today)[0].o.name,'AH Bospeen');
assert.deepEqual(search.candidates(watch.find(x=>x.key==='bier'),'ah',catalog,pricing,resolver,today),[]);
assert.equal(search.valid({...catalog,source_date:'2026-10-20'},today),false);
const user={title:'Amandelen 200 g',match:{all:['amandelen'],pack:{amount:.2,unit:'kg'}}};
const more={...catalog,stores:{...catalog.stores,ah:[['AH Ongebrande amandelen',2.99,'200 g',
  'https://www.ah.nl/producten/product/wi000009/amandelen','wi000009']]}};
assert.equal(search.candidates(user,'ah',more,pricing,resolver,today)[0].o.price,2.99);
console.log('Real catalog: source dates, three stores, UHT milk, false cottage, updated SKU and future products verified');
