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
  if(m?.actionBenefit)return m.actionBenefit.score;
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

 // Editorial quality heuristics; never a nutritional approval or a taste test.
 // A recipe needs a usable method, vegetables, a protein component and a side.
 function culinaryScore(r){
  const ing=Array.isArray(r?.ingredients)?r.ingredients:[];
  const names=ing.map(i=>String(i.name||'').toLocaleLowerCase('nl-NL')).join(' ');
  const veg=ing.filter(i=>i.department==='Groente & fruit'&&i.unit==='g')
   .reduce((sum,i)=>sum+(Number(i.quantity)||0),0);
  const steps=Array.isArray(r?.instructions)?r.instructions.filter(s=>typeof s==='string'&&s.trim().length>25):[];
  let score=0;
  if(r?.quality_status==='concept_niet_culinair_getest')score-=30;
  score+=veg>=1000?16:veg>=700?9:veg>=400?3:0;
  score+=steps.length>=4?12:steps.length>=3?7:0;
  if(/\b(kip|rund|gehakt|varken|zalm|kabeljauw|koolvis|witvis|eieren|tofu|tempeh|linzen|kikkererwten|bonen|halloumi|feta)\b/.test(names))score+=8;
  if(/\b(volkoren|zilvervliesrijst|aardappelen|krieltjes|bulgur|couscous|parelgort|noedels)\b/.test(names))score+=6;
  if(/\b(citroen|limoen|azijn|mosterd|gember|komijn|ras el hanout|gerookt paprikapoeder|knoflook|oregano|koriander|dille|tijm)\b/.test(names))score+=5;
  if(r?.minutes>0&&r.minutes<=55)score+=4;
  return score;
 }
 function evidenceScore(info){
  const confirmed=info?.confirmed||[],anchors=info?.anchors||[];
  const main=x=>x.role==='eiwitbron';
  if(confirmed.some(main))return 110;
  if(anchors.some(main))return 92;
  if(confirmed.length)return 80;
  if(anchors.length)return 65;
  return 0; // An uncertain or merely similar offer never outranks real food quality.
 }
 function editorialScore(recipe,info){
  if(info?.actionBenefit)return info.actionBenefit.score*100+culinaryScore(recipe);
  return evidenceScore(info)*10+culinaryScore(recipe);
 }
 function recommend(rows,matchInfo,limit=12){
  const n=Math.max(1,Number(limit)||12);
  const sorted=[...(rows||[])].sort((a,b)=>
   editorialScore(b,matchInfo(b))-editorialScore(a,matchInfo(a))||
   (Number(a.minutes)||999)-(Number(b.minutes)||999)||
   String(a.title).localeCompare(String(b.title),'nl'));
  if(sorted.some(r=>matchInfo(r)?.actionBenefit)){
   const result=[],counts=new Map(),remaining=[...sorted];
   while(remaining.length){
    remaining.sort((a,b)=>editorialScore(b,matchInfo(b))-(counts.get(b.category)||0)*300-(editorialScore(a,matchInfo(a))-(counts.get(a.category)||0)*300));
    const r=remaining.shift();result.push(r);counts.set(r.category,(counts.get(r.category)||0)+1);
   }
   return result;
  }
  const backed=sorted.filter(r=>evidenceScore(matchInfo(r))>0);
  const inspiration=sorted.filter(r=>evidenceScore(matchInfo(r))===0);
  // Only a handful of supported offers at the top; the remaining positions
  // should inspire varied meals rather than inflate the apparent promotion count.
  const featured=diversify(backed).slice(0,Math.min(7,Math.ceil(n*.6)));
  const fresh=diversify(inspiration).slice(0,n-featured.length);
  const selected=new Set([...featured,...fresh]);
  return [...featured,...fresh,...diversify(sorted.filter(r=>!selected.has(r)))];
 }

 return {normalizeTitle,offerWeight,dedupeAcrossStores,diversify,culinaryScore,evidenceScore,editorialScore,recommend};
});
