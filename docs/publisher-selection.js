/* Recipe publisher selection: verified original links first, without copying instructions.
 * Pure, node-testable planner; link appearance never constitutes a meal-price claim. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjePublisherSelection=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const reviewed=new Set(['handmatig_gevonden_bij_uitgever','publisher_metadata_verified','publisher_page_title_verified']);
 const safeSources=new Set(['Allerhande','HelloFresh','Jumbo','Voedingscentrum','24Kitchen']);
 const offerIdentity=()=>typeof module==='object'&&module.exports?require('./offer-identity.js'):window.MaatjeOfferIdentity;
 const currentDay=()=>new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
 const candidateCache=new WeakMap();
 function actionProducts(recipe,offers,engine,day=currentDay()){
  if(!Array.isArray(offers)||!engine)return [];
  let cached=candidateCache.get(offers);
  if(!cached||cached.day!==day||cached.engine!==engine){
   const byFamily=new Map();
   for(const offer of offers){
    const evidence=offerIdentity().classify(offer,day);
    if(!['confirmed','reported'].includes(evidence)||offer.price_conflict)continue;
    const type=engine.classify(offer);
    if(!type)continue;
    const prior=byFamily.get(type.key);
    if(!prior||(evidence==='confirmed'&&prior.evidence!=='confirmed'))
     byFamily.set(type.key,{family:type.key,offer,offerName:offer.name,evidence});
   }
   cached={day,engine,candidates:[...byFamily.values()]};candidateCache.set(offers,cached);
  }
  const families=new Set(recipe?.ingredient_evidence==='publisher_recipe_schema'?recipe.ingredient_families||[]:[]);
  // Publisher tags require ingredient evidence; title/description tags never count.
  return cached.candidates.filter(item=>Array.isArray(recipe?.ingredients)?
   Boolean(engine.matchRecipe(item.offer,recipe)):families.has(item.family));
 }
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
    typeof r.title==='string'&&r.title.trim().length>=5&&Array.isArray(r.families)&&r.families.length>0&&
    engine?.trustedPublisherUrl?.(r.source,r.url));
 }
 function recipesForOffers({index,stores,offersByStore,engine,query='',ingredient=null,category='alle',source='all',day=currentDay()}){
  if(!engine||!Array.isArray(index?.recipes))return [];
  const requested=safeSources.has(source)?source:'all';
  const sources=(index.recipes||[]).filter(r=>valid(r,engine)&&(requested==='all'||r.source===requested));
  const queryText=norm(query);
  const matches=new Map();
  for(const recipe of sources){
   for(const store of stores||[]){
    const products=actionProducts(recipe,offersByStore?.[store],engine,day);
    if(products.length<2)continue;
    const previous=matches.get(recipe.url);
    if(!previous||products.length>previous.products.length)
     matches.set(recipe.url,{store,products,count:products.length,family:products[0].family});
   }
  }
  const target=ingredient?engine.classify(ingredient):null;
  const filtered=sources.filter(r=>{
   if(!matches.has(r.url))return false;
   if(category!=='alle'&&group(r)!==category)return false;
   if(target&&!(r.ingredient_families||[]).includes(target.key))return false;
   if(ingredient&&!target){
    const q=norm(ingredient.name);
    if(q&&!norm(r.title+' '+r.families.join(' ')).includes(q))return false;
   }
   if(queryText&&!norm(r.title+' '+r.families.join(' ')).includes(queryText))return false;
   return true;
  });
  const score=r=>{
   const m=matches.get(r.url),modes=r.method||'';
   return (m?100+m.count*8:0)+(r.review_status==='publisher_metadata_verified'?20:0)+
    (r.course==='hoofdgerecht'?12:0)+(r.servings===4?5:0)+
    (slow(r)?15:0)+Math.min(r.vegetable_families||0,3)*4+
    (Number(r.minutes)>0&&Number(r.minutes)<=50?5:0)+
    (modes==='anders'?-2:0);
  };
  filtered.sort((a,b)=>score(b)-score(a)||a.title.localeCompare(b.title,'nl'));
  const result=[],seenTitles=new Set(),groups=new Map(),methods=new Map(),publishers=new Map(),cuisines=new Map();
  // Re-evaluate diversity after every pick: alternate categories, methods and sources
  // when qualified alternatives exist, without ever relaxing the two-product gate.
  const remaining=[...filtered];
  while(remaining.length){
   const rank=r=>score(r)-(groups.get(group(r))||0)*35-
    (methods.get(r.method||'anders')||0)*20-(publishers.get(r.source)||0)*12-(r.cuisine?(cuisines.get(r.cuisine)||0)*15:0)-
    (result.at(-1)?.category===group(r)?35:0)-
    (result.at(-1)?.recipe.method===r.method?20:0);
   remaining.sort((a,b)=>rank(b)-rank(a)||a.title.localeCompare(b.title,'nl'));
   const r=remaining.shift(),title=norm(r.title);
   if(seenTitles.has(title))continue;
   seenTitles.add(title);
   groups.set(group(r),(groups.get(group(r))||0)+1);
   methods.set(r.method||'anders',(methods.get(r.method||'anders')||0)+1);
   publishers.set(r.source,(publishers.get(r.source)||0)+1);
   if(r.cuisine)cuisines.set(r.cuisine,(cuisines.get(r.cuisine)||0)+1);
   result.push({recipe:r,matched:matches.get(r.url),category:group(r),slow:slow(r),score:score(r)});
  }
  return result;
 }
 return {valid,group,slow,actionProducts,recipesForOffers};
});
