const assert=require('node:assert/strict');
const fs=require('node:fs');
const {basket}=require('../docs/price-integrity.js');
const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Amsterdam'}).format(new Date());
let historical=0,partial=0,active=0,total=0;
for(const file of ['daily','spotlight']){
 const d=JSON.parse(fs.readFileSync('docs/data/'+file+'.json','utf8'));
 for(const store of ['lidl','jumbo','ah']){
  for(const recipe of d.stores[store]?.recipes||[]){
   total++;const p=basket(recipe,today);
   const price=recipe.cost?.basket_total;
   if(typeof price==='number'){
    assert.equal(p.state!=='partial'&&p.state!=='unpriced',true,'Claimed total with missing ingredients: '+recipe.id);
    assert.ok(Math.abs(p.total-price)<0.02,'Declared basket is not the sum of complete packs: '+recipe.id);
    if(recipe.cost.verified_today===true)assert.equal(p.state,'today_confirmed','Bad live-price claim: '+recipe.id);
    if(p.state==='historical_estimate')historical++;
   }else if(p.state==='partial'){
    partial++;
    if(typeof recipe.minimum_known_spend==='number')
     assert.ok(Math.abs(p.partial-recipe.minimum_known_spend)<0.02,'Incomplete lower bound is wrong: '+recipe.id);
   }
   if(p.state==='today_confirmed')active++;
  }
 }
}
console.log('Real recipe data: '+total+' audited, '+historical+' historic basket estimates, '+partial+' incomplete carts, '+active+' today-confirmed carts');
assert.ok(total>=35);
