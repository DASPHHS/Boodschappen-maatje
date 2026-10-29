const assert=require('node:assert/strict'),fs=require('node:fs');
const weekly=JSON.parse(fs.readFileSync('docs/data/weekly.json','utf8'));
const lib=JSON.parse(fs.readFileSync('docs/data/library.json','utf8')).recipes;
const local=process.env.DATE_OVERRIDE||new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
assert.ok(weekly.week_start<=local&&local<=weekly.week_end,'Weekly feed must be current, not silently stale');
assert.equal(weekly.editorial_status,'eigen_bewerkingen_niet_proefgekookt');
const kinds=['kip','vlees','vis','vega'];
for(const store of ['lidl','jumbo','ah']){
 const batch=weekly.stores[store],recipes=batch?.recipes||[];
 assert.equal(batch.status,'own_ideas_unverified');
 assert.equal(recipes.length,4,'Four balanced recipes per store');
 assert.deepEqual([...new Set(recipes.map(r=>r.category))].sort(),[...kinds].sort());
 for(const r of recipes){
  const source=lib.find(x=>x.id===r.source_library_id);
  assert.ok(source,'Recipe must come from known owned library');
  assert.equal(r.servings,4);
  assert.equal(r.quality_status,'uitgewerkt_niet_culinair_getest');
  assert.ok(r.quality_issues.includes('niet_proefgekookt'));
  assert.equal(r.recipe_week_start,weekly.week_start);
  assert.equal(r.recipe_week_end,weekly.week_end);
  assert.equal(r.cost,null);assert.equal(r.macros,null);
  assert.equal((r.offer_links||[]).length,0);
  assert.equal((r.offer_anchors||[]).length,0);
  assert.ok(r.ingredients.every(i=>i.pack_price===undefined),'Never synthesize shelf prices');
  assert.ok(r.instructions.length>=3);
  assert.equal(r.source_status,'algemene_inspiratie_bron_geen_1_op_1_recept');
 }
}
console.log('Weekmenu: 4 honest untested four-portion ideas per store, rotating by week and never priced as verified');
