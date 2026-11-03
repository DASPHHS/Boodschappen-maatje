const assert=require('node:assert/strict');
const m=require('../docs/offer-identity.js');

// Exact identities must respect quantity, alcohol content AND bottle versus can.
const a={id:'a',name:'Texels Skuumkoppe Bier Fles 6 × 300 ml',pack_label:'6 × 300 ml',price:7.04};
const sameBottle={id:'a2',name:'Texels Skuumkoppe Bier Fles 6x30cl',pack_label:'6x30cl',price:7.49};
const unspecified={id:'b',name:'Texels Skuumkoppe 6x300ML',pack_label:'6x300ML',price:7.49};
const size330={id:'c',name:'Texels Skuumkoppe 6x330ML',pack_label:'6x330ML',price:8.61};
const zero={id:'d',name:'Texels Skuumkoppe 0.0% 6x300ML',pack_label:'6x300ML',price:7.04};
const can={id:'e',name:'Texels Skuumkoppe Bier Blik 6x300ML',pack_label:'6x300ML',price:7.04};
const merged=m.merge([a,sameBottle,unspecified,size330,zero,can]);
assert.equal(merged.length,5,'untyped, bottle, can, 0.0 and other volumes stay distinct');
assert.ok(merged[0].price_conflict,'conflicting exact-bottle prices must be visible');
assert.equal(merged[1].price_conflict,undefined,'an unspecified container cannot falsely prove a conflict');
assert.notEqual(m.key(a),m.key(unspecified));
assert.notEqual(m.key(a),m.key(can));
assert.notEqual(m.key(a),m.key(size330));
assert.notEqual(m.key(a),m.key(zero));
assert.equal(m.pack({pack_label:'6 × 300 ml'}),m.pack({pack_label:'6x30cl'}));

const today='2026-10-29';
const offer={...a,start_date:'2026-10-26',end_date:'2026-11-01',
  verified:true,source:{url:'https://www.jumbo.com/aanbiedingen/test'}};
assert.equal(m.classify(offer,today),'excluded','Legacy verified boolean cannot confirm a promotion');
offer.promotion_evidence={status:'available',name:offer.name,pack_label:offer.pack_label,price:offer.price,start_date:offer.start_date,end_date:offer.end_date,checked_at:today,url:offer.source.url};
assert.equal(m.classify(offer,today),'excluded','An incomplete offer URL is insufficient');
offer.source.url='https://www.jumbo.com/aanbiedingen/texels/123456';
offer.promotion_evidence.url=offer.source.url;
assert.equal(m.classify(offer,today),'confirmed');
assert.equal(m.classify({...offer,price_conflict:'retailer disagrees with its kilo price'},today),'reported','conflict cannot be confirmed');
const explicit=m.merge([{...offer,id:'original'},{...offer,id:'duplicate',price_conflict:'AH product versus category price'}]);
assert.ok(explicit[0].price_conflict?.includes('AH product'),'a duplicate with the same price must propagate a known source conflict');
const sameId=m.merge([{...offer,id:'same'},{...offer,id:'same',price_conflict:'new daily evidence'}]);
assert.ok(sameId[0].price_conflict?.includes('new daily evidence'),'same ID from spotlight and daily must retain new conflict');
assert.equal(m.classify({...offer,source_provider:'PrijsProfeet',verified:false,promotion_status:'active'},today),'reported');
assert.equal(m.classify({...offer,source_provider:'Biernet',status:'third_party_price_observation'},today),'observation');
assert.equal(m.classify({...offer,variant:'alcoholvrij'},today),'excluded','incorrect alcohol flags are a blocker');
assert.equal(m.classify({...offer,name:'Texels Skuumkoppe 0.0 6x300ml',variant:'alcoholhoudend'},today),'excluded');
assert.equal(m.classify({...offer,end_date:'2026-10-28'},today),'excluded');
assert.equal(m.classify({...offer,source:{url:''}},today),'excluded');
assert.equal(m.classify({...offer,price:NaN},today),'excluded');
console.log('Promotion evidence gate and precise package/variant matching validated');

assert.equal(m.classify({id:'folderz-1',name:'Broccoli',price:.69,start_date:'2026-10-26',end_date:'2026-11-01',source_provider:'Folderz',verified:false,promotion_status:'active',source:{url:'https://www.folderz.nl/winkels/lidl/aanbiedingen/broccoli-aanbieding-123/'}},'2026-11-01'),'reported');

const current='2026-11-03',fs=require('fs');
const bad=JSON.parse(fs.readFileSync('docs/data/spotlight.json')).stores.jumbo.offers.find(x=>x.id==='jumbo-w44-kipblokjes');
assert.equal(m.classify(bad,current),'excluded');
assert.equal(m.classify({...bad,verified:true,promotion_status:'active'},current),'excluded','Reimporting the old true flag must not revive a generic landing-page action');
assert.equal(m.classify({...offer,promotion_evidence:{...offer.promotion_evidence,checked_at:'2026-10-20'}},today),'excluded');
assert.equal(m.classify({...offer,promotion_evidence:{...offer.promotion_evidence,price:1}},today),'excluded');
assert.equal(m.classify({...offer,promotion_status:'withdrawn'},today),'excluded');
const obs=require('../docs/price-observations');
assert.equal(obs.inspect({...bad,verified:true,promotion_status:'active'},'jumbo',current),null,'Comparison/favorites resolver must use the same gate');
const selector=require('../docs/publisher-selection'),engine=require('../docs/recipe-discovery');
const r={servings:4,ingredients:[{name:'kipfilet',quantity:360,unit:'g'},{name:'sperziebonen',quantity:400,unit:'g'}]};
assert.equal(selector.actionProducts(r,[bad],engine,current).length,0,'Rejected chicken cannot anchor any recipe');

assert.equal(m.classify({...bad,verified:false,promotion_status:'active',price_conflict:'unknown'},current),'excluded','A conflict flag is not positive promotion evidence');

// The evidence policy is independent of product family, retailer and vocabulary.
// Deliberately include non-food and an unfamiliar future product name.
const weekly=require('../docs/weekdeals-engine');
const names=['Kipfilet','Zalm','Tofu','Eieren','Kwark','Houdbare melk','Appels','Volkorenbrood','Rijst','Bier','Wasmiddel','Hondenvoer','Nieuw product zonder bekende familie'];
let cases=0;
for(const store of ['jumbo','ah','lidl'])for(const name of names){
 const url={jumbo:'https://www.jumbo.com/aanbiedingen/product/123456',ah:'https://www.ah.nl/producten/product/wi123456/product',lidl:'https://www.lidl.nl/p/product/p123456'}[store];
 const o={id:store+'-'+name,name,pack_label:'500 g',price:2,start_date:current,end_date:'2026-11-08',verified:true,source:{url}};
 o.promotion_evidence={status:'available',name,pack_label:o.pack_label,price:o.price,start_date:o.start_date,end_date:o.end_date,checked_at:current,url};
 assert.equal(m.classify(o,current),'confirmed');
 assert.equal(obs.inspect(o,store,current)?.isPromotion,true);
 assert.equal(weekly.eligible(o,store,current,'now'),true);
 const mutations=[
  {promotion_evidence:null},{promotion_status:'withdrawn'},{promotion_status:'disputed'},
  {source:{url:'https://www.'+({ah:'ah.nl',jumbo:'jumbo.com',lidl:'lidl.nl'}[store])+'/'}},
  {price:3},{pack_label:'1 kg'},{name:name+' andere variant'},{member_required:true},
  {requires_membership:true},{multi_buy_quantity:2,multi_buy_price:3},{loyalty_price:1},
  {loyalty_program:'Klantenkaart'},{date_estimated:true},{valid_until_estimated:true},
  {start_date:'2026-02-30'},{availability_status:'unavailable'},
  {promotion_evidence:{...o.promotion_evidence,checked_at:'2026-10-01'}},
  {promotion_evidence:{...o.promotion_evidence,end_date:'2026-12-31'}}
 ];
 for(const mutation of mutations){
  const bad={...o,...mutation};
  assert.equal(m.confirmedPromotion(bad,current),false,'The confirmation helper must also reject the same invalid evidence');
  assert.equal(m.classify(bad,current),'excluded',store+' '+name+' '+JSON.stringify(mutation));
  assert.ok(!obs.inspect(bad,store,current)?.isPromotion);
  assert.equal(weekly.eligible(bad,store,current,'now'),false);
  cases++;
 }
 const noProof={...o,verified:false,source_provider:'onbekende_bron'};
 assert.equal(m.classify(noProof,current),'excluded');
 assert.equal(obs.inspect(noProof,store,current),null,'Unknown source cannot bypass the gate through price comparisons');
 assert.equal(weekly.eligible(noProof,store,current,'now'),false);
}
assert.equal(m.validDay('2026-02-30'),false);
console.log('Universal evidence policy: '+cases+' invalid product/store cases rejected across offers, price comparisons and week previews');
