'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const r=JSON.parse(fs.readFileSync('docs/data/curated-recipes.json','utf8')).recipes;
const batches=r.filter(x=>x.batch_cook?.days===2);
const app=fs.readFileSync('docs/app.js','utf8');
const html=fs.readFileSync('docs/index.html','utf8');
assert.equal(r.length,30,'The six new dishes are added to the 24 existing originals');
assert.equal(batches.length,6,'Six full two-day recipes must be available');
assert.ok(batches.some(x=>/hachee/i.test(x.title)));
assert.ok(batches.some(x=>/rendang/i.test(x.title)));
assert.ok(batches.some(x=>/chili/i.test(x.title)));
assert.ok(batches.some(x=>/lasagne/i.test(x.title)));
for(const recipe of batches){
 const b=recipe.batch_cook;
 assert.equal(recipe.servings,4);
 assert.equal(b.days,2);
 assert.equal(b.people_per_day,2);
 assert.equal(b.total_portions,4);
 assert.equal(recipe.quality_status,'uitgewerkt_niet_culinair_getest');
 assert.ok(recipe.instructions.length>=8,'Batch cooking needs concrete preparation steps: '+recipe.title);
 assert.ok(recipe.instructions.every(step=>step.length>50),'No placeholder method: '+recipe.title);
 assert.ok(recipe.ingredients.length>=9);
 const greens=recipe.ingredients.filter(x=>x.department==='Groente & fruit'&&x.unit==='g')
  .reduce((total,x)=>total+x.quantity,0);
 assert.ok(greens>=1200,'At least 300 g vegetables per portion: '+recipe.title);
 for(const key of ['first_day','second_day','cooling','storage','reheat','source_url']){
  assert.ok(typeof b[key]==='string'&&b[key].length>=20,recipe.title+': '+key);
 }
 assert.match(b.cooling,/2 uur/);
 assert.match(b.storage,/4 °C/);
 assert.match(b.reheat,/één keer/);
 assert.match(b.storage,/2 dagen/);
 assert.match(b.source_url,/^https:\/\/www\.voedingscentrum\.nl\//);
 assert.equal(recipe.cost,null);
 assert.equal(recipe.macros,null);
}
const hachee=batches.find(x=>/hachee/i.test(x.title));
assert.equal(hachee.ingredients.filter(x=>/runderriblappen/i.test(x.name)).length,1);
assert.ok(hachee.ingredients.some(x=>/uien/.test(x.name)&&x.quantity>=500),'Hachee needs proper caramelised onions');
assert.ok(hachee.instructions.some(x=>/2½–3 uur/.test(x)),'Stewing time cannot be omitted');
assert.ok(hachee.batch_cook.second_day.includes('aardappelen'));
assert.ok(app.includes("data-batch-only=\"two\""),'A visible filter is mandatory');
assert.ok(app.includes("state.batchOnly&&"),'Filter must affect actual cards');
assert.ok(app.includes("In één keer koken, twee dagen eten"),'Full dialog must show day allocation');
assert.ok(app.includes("batch_cook:r.batch_cook||null"),'Saved/planned recipes must retain day-two instructions');
assert.ok(app.includes("(count*4)"),'Four portions are not the same as four days');
assert.ok(html.includes('app.js?v=20261102-two-actions'),'Browser must refresh updated interface');
console.log('Six detailed two-day recipes, 2 x 2 portions, food safety and saved-plan metadata verified');
