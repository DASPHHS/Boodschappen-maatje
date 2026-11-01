/* Recipe publisher selection: verified original links first, without copying instructions.
 * Pure, node-testable planner; link appearance never constitutes a meal-price claim. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjePublisherSelection=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const reviewed=new Set(['handmatig_gevonden_bij_uitgever','publisher_metadata_verified','publisher_page_title_verified']);
 const safeSources=new Set(['Allerhande','HelloFresh']);
 const norm=x=>String(x||'').toLocaleLowerCase('nl-NL').normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const slow=r=>/hachee|rendang|stoof|sudderen|draadjes|boeuf|lasagne|tajine/i.test(r?.title||'')||
  ['stoof','hachee','rendang','lasagne','tajine'].includes(r?.method);
 function group(r){
  const t=norm(r?.title),f=new Set(r?.families||[]);
  if((/veggie|vegetarisch|vegan|plantaardig/.test(t))&&!/zonder veggie/.test(t))return 'vega';
  if(f.has('kip')||/\bkip\b|kipfilet|kippendij|kipsate/.test(t))return 'kip';
  if(f.has('zalm')||f.has('witvis')||f.has('garnalen')||/\bvis\b|zalm|koolvis|garnalen/.test(t))return 'vis';
  if(f.has('riblappen')||f.has('gehakt')||/hachee|rendang|rund|varkens|rookworst|gehakt/.test(t))return 'vlees';
  return 'vega';
 }
 function valid(r,engine){
  return Boolean(r&&safeSources.has(r.source)&&reviewed.has(r.review_status)&&
    typeof r.title==='string'&&r.title.trim().length>8&&Array.isArray(r.families)&&r.families.length>0&&
    engine?.trustedPublisherUrl?.(r.source,r.url));
 }
 function recipesForOffers({index,stores,offersByStore,engine,query='',ingredient=null,category='alle',source='all'}){
  if(!engine||!Array.isArray(index?.recipes))return [];
  const requested=['all','HelloFresh','Allerhande'].includes(source)?source:'HelloFresh';
  const sources=(index.recipes||[]).filter(r=>valid(r,engine)&&(requested==='all'||r.source===requested));
  const queryText=norm(query);
  // Only a known culinary family warrants a suggested deal pairing; never claim
  // price/pack compatibility on the basis of title tokens.
  const matches=new Map();
  for(const store of stores||[]){
   const uniqueFamilies=new Map();
   for(const offer of (offersByStore?.[store]||[])){
    const type=engine.classify(offer);
    if(type&&!uniqueFamilies.has(type.key))uniqueFamilies.set(type.key,offer);
   }
   for(const [family,offer] of uniqueFamilies){
    const hits=engine.publisherMatches(offer,index,150);
    for(const {recipe} of hits){
     if(!valid(recipe,engine)||(requested!=='all'&&recipe.source!==requested))continue;
     const match=matches.get(recipe.url);
     if(!match)matches.set(recipe.url,{store,family,offerName:offer.name});
    }
   }
  }
  const target=ingredient?engine.classify(ingredient):null;
  const filtered=sources.filter(r=>{
   if(category!=='alle'&&group(r)!==category)return false;
   if(target&&!r.families.includes(target.key))return false;
   if(ingredient&&!target){
    const q=norm(ingredient.name);
    if(q&&!norm(r.title+' '+r.families.join(' ')).includes(q))return false;
   }
   if(queryText&&!norm(r.title+' '+r.families.join(' ')).includes(queryText))return false;
   return true;
  });
  const score=r=>{
   const m=matches.get(r.url),modes=r.method||'';
   return (m?100:0)+(r.review_status==='publisher_metadata_verified'?20:0)+
    (r.course==='hoofdgerecht'?12:0)+(r.servings===4?5:0)+
    (slow(r)?15:0)+Math.min(r.vegetable_families||0,3)*4+
    (Number(r.minutes)>0&&Number(r.minutes)<=50?5:0)+
    (modes==='anders'?-2:0);
  };
  filtered.sort((a,b)=>score(b)-score(a)||a.title.localeCompare(b.title,'nl'));
  const queues=new Map(['Allerhande','HelloFresh'].map(source=>[source,filtered.filter(r=>r.source===source)]));
  const result=[],selected=new Set(),seenTitles=new Set(),groups=new Map();
  const take=source=>{
   const q=queues.get(source)||[];
   if(!q.length)return false;
   // Avoid three consecutive curries or three consecutive veggie dishes.
   let best=0;
   for(let i=0;i<q.length;i++){
    const method=q[i].method||'anders',g=group(q[i]);
    if((groups.get(g)||0)<2&&!(result.length&&result.at(-1).recipe.method===method)){
     best=i;break;
    }
   }
   const r=q.splice(best,1)[0];
   if(selected.has(r.url)||seenTitles.has(norm(r.title)))return take(source);
   seenTitles.add(norm(r.title));
   selected.add(r.url);groups.set(group(r),(groups.get(group(r))||0)+1);
   result.push({recipe:r,matched:matches.get(r.url)||null,category:group(r),slow:slow(r),score:score(r)});
   return true;
  };
  while(queues.get('Allerhande').length||queues.get('HelloFresh').length){
   if(!take('Allerhande')&&!queues.get('HelloFresh').length)break;
   take('HelloFresh');
  }
  return result;
 }
 return {valid,group,slow,recipesForOffers};
});
