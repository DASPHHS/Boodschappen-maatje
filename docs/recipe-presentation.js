/* Recipe presentation rules: one useful card per dish, not three duplicate retailer columns.
 * Ranked store choice is only preference; an unverified offer is not a sale claim. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeRecipePresentation=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const STORES=['lidl','jumbo','ah'];
 const normalizeTitle=s=>String(s||'').toLocaleLowerCase('nl-NL').normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 function offerWeight(m){
  if(m?.confirmed?.length)return 4;
  if(m?.anchors?.length)return 3;
  if(m?.possible?.length)return 1;
  return 0;
 }
 function dedupeAcrossStores(rows,matchInfo){
  const known=new Map();
  for(const r of rows||[]){
   if(!r?.title||!STORES.includes(r.store))continue;
   const key=normalizeTitle(r.title);
   const old=known.get(key);
   if(!old){known.set(key,r);continue;}
   const score=x=>offerWeight(matchInfo(x));
   if(score(r)>score(old)||(score(r)===score(old)&&STORES.indexOf(r.store)<STORES.indexOf(old.store)))
    known.set(key,r);
  }
  return [...known.values()];
 }
 function diversify(rows){
  const groups=new Map();
  for(const r of rows||[]){
   const key=STORES.includes(r.category)?'other':r.category||'other';
   if(!groups.has(key))groups.set(key,[]);
   groups.get(key).push(r);
  }
  const order=[...groups.keys()];
  const result=[];
  while(result.length<(rows||[]).length){
   for(const category of order){
    const queue=groups.get(category);
    if(queue.length)result.push(queue.shift());
   }
  }
  return result;
 }
 return {normalizeTitle,offerWeight,dedupeAcrossStores,diversify};
});
