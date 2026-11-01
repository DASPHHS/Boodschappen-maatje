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
const inspired={title:'Eigen zalmgerecht',category:'vis',minutes:40,quality_status:'uitgewerkt_niet_culinair_getest',
 ingredients:[{name:'zalmfilet',quantity:700,unit:'g',department:'Eiwitbronnen'},
 {name:'prei',quantity:700,unit:'g',department:'Groente & fruit'},
 {name:'venkel',quantity:650,unit:'g',department:'Groente & fruit'},
 {name:'citroen',quantity:1,unit:'st',department:'Groente & fruit'},
 {name:'volkoren parelgort',quantity:280,unit:'g',department:'Kruiden & voorraad'}],
 instructions:['Gaar de vis en laat de huid krokant worden in de koekenpan.','Stoof de prei langzaam met de venkel in een diepe pan.','Kook de parelgort volledig volgens de verpakking en laat uitlekken.','Breng op smaak met citroen en serveer de vis erop.']};
const poor={title:'Niet uitgewerkte kip',category:'kip',ingredients:[{name:'kipfilet'}],
 quality_status:'concept_niet_culinair_getest',instructions:[]};
assert.ok(p.culinaryScore(inspired)>p.culinaryScore(poor),'Complete vegetable-rich recipes outrank empty concepts');
assert.equal(p.evidenceScore({possible:[{role:'eiwitbron'}]}),0,'Unproven candidates get no offer bonus');
assert.ok(p.evidenceScore({anchors:[{role:'eiwitbron'}]})>p.evidenceScore({anchors:[{role:'groente'}]}));
const recs=[{...poor,id:'p'}, {...inspired,id:'i'}, {...poor,id:'a',title:'Actiegerecht'},...Array.from({length:15},(_,j)=>({...poor,id:String(j),title:'Kip '+j}))];
const matches=r=>r.id==='a'?{anchors:[{role:'eiwitbron'}]}:{possible:[{role:'groente'}]};
const recommended=p.recommend(recs,matches,12);
assert.equal(recommended[0].id,'a','Confirmed action relevance beats unrelated, however new');
assert.ok(recommended.slice(0,12).includes(recs[1]),'Complete culinary recipe is promoted into top selection');
assert.equal(recommended.length,recs.length,'No recipes are permanently hidden by top selection');
console.log('Cross-store deduplication, evidence priority and varied meal ordering validated');
