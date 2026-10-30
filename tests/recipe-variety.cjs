'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const recipes=JSON.parse(fs.readFileSync('docs/data/library.json')).recipes;
assert.equal(new Set(recipes.map(r=>r.id)).size,recipes.length);
assert.equal(new Set(recipes.map(r=>r.title)).size,recipes.length);
for(const [category,minimum] of Object.entries({kip:16,vlees:16,vis:16,vega:24}))assert.ok(recipes.filter(r=>r.category===category).length>=minimum);
const added=recipes.filter(r=>r.id.startsWith('wereld-'));
assert.equal(added.length,24);
for(const r of added){
 assert.equal(r.servings,4);assert.ok(r.instructions.length>=3);
 assert.ok(r.ingredients.every(i=>i.name&&i.quantity>0&&['g','ml','st'].includes(i.unit)));
 assert.ok(r.ingredients.filter(i=>i.department==='Groente & fruit').reduce((n,i)=>n+i.quantity,0)>=1200);
 assert.ok(!r.cost&&!r.macros);assert.equal(r.quality_status,'uitgewerkt_niet_culinair_getest');
}
const vega=added.filter(r=>r.category==='vega');
for(const group of [/linzen/,/kikkererwten/,/eieren/,/halloumi/,/feta/,/tofu/,/tempeh/,/edamame/,/zwarte bonen/,/witte bonen/])assert.ok(vega.some(r=>r.ingredients.some(i=>group.test(i.name))),'Missing vega protein '+group);
console.log('72 unique recipes: 16 per animal category and 24 vega, including ten distinct vega protein groups');
