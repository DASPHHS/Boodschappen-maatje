const assert=require('node:assert/strict');
const r=require('../docs/recipe-ranking.js');
const broccoli={confirmed:[{role:'groente',offer:{name:'Broccoli'}}],anchors:[]};
const salmon={confirmed:[],anchors:[{role:'eiwitbron',offer:{name:'Verse zalmfilet op huid'}}]};
assert.ok(r.score(salmon)>r.score(broccoli));
assert.equal(r.mainOffer(salmon).offer.name,'Verse zalmfilet op huid');
assert.equal(r.mainOffer(broccoli),null);
assert.equal(r.score({confirmed:[],anchors:[]}),0);
console.log('Recipe action ranking favors main ingredients, never nominal discounts');
