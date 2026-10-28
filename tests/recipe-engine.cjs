/* Lightweight repeatable checks of the recipe-ideas engine. */
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const ctx={window:{}};
vm.runInNewContext(fs.readFileSync('docs/recipe-engine.js','utf8'),ctx);
const engine=ctx.window.BoodschapRecipeEngine;
assert.ok(engine&&typeof engine.build==='function');
const mk=(id,name,category)=>({id,name,category,price:2.99,pack_label:'500 g',source:{url:'https://example.com/offer'}});
const fixture=[
mk('a','AH Scharrel kipfilet 2 stuks','kip'),
mk('b','Knorr Good noodles kip','kip'),
mk('c','Vivera Zachte Tofu 550 g','vega'),
mk('d','Jumbo Gemengd Gehakt 2 x 500g','vlees'),
mk('e','AH Zalmfilet 500g','vis'),
mk('f','Johma Kip-kerrie salade','kip'),
mk('g','Olvarit Wortel kip rijst','kip')
];
const recipes=engine.build('jumbo',fixture);
assert.ok(recipes.length>=15, 'verwacht meerdere echte cuisines');
assert.ok(!recipes.some(x=>/knorr|olvarit|johma/i.test(x.offer_anchor_name)));
assert.ok(new Set(recipes.map(r=>r.id)).size===recipes.length);
for(const r of recipes){
assert.equal(r.servings,4);
assert.equal(r.vegetables_g_per_portion,300);
assert.ok(r.ingredients.filter(x=>x.department==='Groente & fruit').reduce((n,i)=>n+i.quantity,0)>=1200);
assert.equal(r.cost,null);
assert.equal(r.macros,null);
assert.ok(r.offer_anchor_id);
assert.ok(r.instructions.length>=3);
}
console.log('Receptmotor: '+recipes.length+' actiebasis-ideeën gevalideerd.');
