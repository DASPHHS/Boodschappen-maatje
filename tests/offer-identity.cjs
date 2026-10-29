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
