// Regression guard: a workflow must not overwrite fresh product coverage with
// a report calculated before a concurrent catalog/offer update.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
for(const name of ['product-monitor','actiecatalogus','retailer-catalog']){
  const file='.github/workflows/'+name+'.yml';
  const yaml=fs.readFileSync(file,'utf8');
  assert.match(yaml,/group: boodschappen-data-publication/,
    file+' must share a publication lock with the other writers');
  const reset=yaml.lastIndexOf('git reset --hard origin/main');
  const rebuild=yaml.lastIndexOf('node scripts/build_product_resolution.cjs\n');
  const stage=yaml.lastIndexOf('git add ');
  assert.ok(reset!==-1&&rebuild>reset&&stage>rebuild,
    file+' must recalculate coverage after reset and before committing');
  assert.doesNotMatch(yaml,/cp [^\n]*product-resolution\.json/,
    file+' must not replay pre-reset product resolution from a temporary copy');
}
console.log('All three publication jobs rebuild fresh coverage under a shared lock');
