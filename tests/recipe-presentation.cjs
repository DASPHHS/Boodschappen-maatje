'use strict';
const assert=require('node:assert/strict');
const p=require('../docs/recipe-presentation.js');
const cases=[
 {id:'a',store:'ah',title:'Rode-linzendahl',category:'vega'},
 {id:'b',store:'lidl',title:'Rode linzendahl',category:'vega'},
 {id:'c',store:'jumbo',title:'Citroenkip',category:'kip'},
 {id:'d',store:'ah',title:'Citroenkip',category:'kip'},
 {id:'e',store:'lidl',title:'Zalm in de oven',category:'vis'},
 {id:'f',store:'jumbo',title:'Runderstoof',category:'vlees'},
 {id:'g',store:'lidl',title:'Quinoasalade',category:'vega'},
 {id:'h',store:'lidl',title:'Groentecurry',category:'vega'}
];
const offers=r=>r.id==='a'?{confirmed:[1]}:r.id==='b'?{possible:[1]}:r.id==='d'?{anchors:[1]}:{};
const uniq=p.dedupeAcrossStores(cases,offers);
assert.equal(uniq.length,6,'No cross-retailer repetition of the same dish');
assert.ok(uniq.some(r=>r.id==='a'),'Confirmed offer wins over vague candidate');
assert.ok(uniq.some(r=>r.id==='d'),'Evidence-backed anchor wins over store order');
assert.ok(!uniq.some(r=>r.id==='b'||r.id==='c'),'Inferior duplicate retailer cards hidden');
const varied=p.diversify([
 {title:'A',category:'vega'},{title:'B',category:'vega'},{title:'C',category:'vega'},
 {title:'D',category:'kip'},{title:'E',category:'vis'},{title:'F',category:'vlees'}
]);
assert.deepEqual(varied.slice(0,4).map(x=>x.category),['vega','kip','vis','vlees'],
 'Mixed cooking categories appear within first four results');
assert.equal(new Set(varied.map(r=>r.title)).size,6,'Diversification must not drop entries');
assert.equal(p.normalizeTitle('Kip–broccoli mét rĳst').includes('kip broccoli'),true);
console.log('Cross-store deduplication, evidence priority and varied meal ordering validated');
