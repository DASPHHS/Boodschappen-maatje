/* Match real culinary variants, then rank the cost-driving main ingredient.
 * Every visible recipe still requires two distinct active products at one store. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.MaatjePublisherSelection=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const dependency=(file,browser)=>typeof module==='object'&&module.exports?require('./'+file):window[browser];
const identity=()=>dependency('offer-identity.js','MaatjeOfferIdentity');
const culinary=()=>dependency('recipe-products.js','MaatjeRecipeProducts');
const prices=()=>dependency('price-observations.js','MaatjeObservations');
const currentDay=()=>new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
const norm=x=>String(x||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
const reviewed=new Set(['handmatig_gevonden_bij_uitgever','publisher_metadata_verified','publisher_page_title_verified']);
const safeSources=new Set(['Allerhande','HelloFresh','Jumbo','Voedingscentrum','24Kitchen']);
const candidateCache=new WeakMap();
const group=r=>culinary().group(r);
const slow=r=>Number(r?.minutes)>=90||['stoof','hachee','rendang','tajine'].includes(r?.method);
function valid(r,engine){return Boolean(r&&safeSources.has(r.source)&&reviewed.has(r.review_status)&&typeof r.title==='string'&&r.title.trim().length>=5&&engine?.trustedPublisherUrl?.(r.source,r.url));}
function purchase(offer,profile,recipe){
 const pack=prices().pack(offer),servings=Number(recipe?.servings);
 let amount=Number(profile?.quantity),unit=profile?.unit;
 if(!amount||!servings||!pack||pack.approximate||profile.drained)return null;
 if(unit==='g'){amount/=1000;unit='kg'}else if(unit==='ml'){amount/=1000;unit='L'}
 if(unit!==pack.unit||amount<=0)return null;
 // Generic legume names do not establish dry/cooked/drained weight.
 if(['bonen','linzen','kikkererwten'].includes(profile.family)&&profile.form==='plain')return null;
 const packages=Math.ceil((amount*4/servings-1e-8)/pack.amount);
 if(packages<1||packages>30)return null;
 return {packages,total:Math.round(offer.price*packages*100)/100,portions:4};
}
function discount(offer,profile,recipe){
 const reference=Number(offer.regular_price),price=Number(offer.price);
 // Multipack/bundle reference prices can describe a different unit; never infer a saving.
 if(!Number.isFinite(reference)||reference<=price||Number(offer.multi_buy_quantity)>1||offer.price_conflict)return {perPack:null,forFour:null};
 const delta=Math.round((reference-price)*100)/100,cart=purchase(offer,profile,recipe);
 return {perPack:delta,forFour:cart?Math.round(delta*cart.packages*100)/100:null,packages:cart?.packages||null};
}
function actionProducts(recipe,offers,engine,day=currentDay()){
 if(!Array.isArray(offers)||!engine)return [];
 let cached=candidateCache.get(offers);
 if(!cached||cached.day!==day||cached.engine!==engine){
  const candidates=[];
  for(const offer of offers){
   const evidence=identity().classify(offer,day);
   if(!['confirmed','reported'].includes(evidence)||offer.price_conflict)continue;
   const type=engine.classify(offer);
   if(type?.profile)candidates.push({family:type.key,profile:type.profile,offer,offerName:offer.name,evidence});
  }
  cached={day,engine,candidates};candidateCache.set(offers,cached);
 }
 const profiles=culinary().recipeProfiles(recipe),chosen=new Map();
 for(const item of cached.candidates){
  const profile=profiles.find(p=>culinary().compatible(item.profile,p));
  if(!profile)continue;
  if(item.family==='riblappen'&&Number(recipe.minutes)<95&&!/stoof|rendang|hachee|semur/i.test(recipe.title))continue;
  const isMain=culinary().isMain(profile,recipe),saving=discount(item.offer,profile,recipe);
  const candidate={...item,ingredientProfile:profile,isMain,saving,purchase:purchase(item.offer,profile,recipe)};
  const prior=chosen.get(item.family);
  // Choose a sensible basket spend for the same variant. Never reward a large
  // advertised discount by buying a more expensive alternative for the recipe.
  const priceRank=x=>x.purchase?.total??(prices().unitCost(x.offer)?.price||Infinity);
  if(!prior||(candidate.purchase&&!prior.purchase)||(Boolean(candidate.purchase)===Boolean(prior.purchase)&&priceRank(candidate)<priceRank(prior))||
    (priceRank(candidate)===priceRank(prior)&&item.evidence==='confirmed'&&prior.evidence!=='confirmed'))chosen.set(item.family,candidate);
 }
 return [...chosen.values()].sort((a,b)=>Number(b.isMain)-Number(a.isMain)||(b.saving.forFour??b.saving.perPack??0)-(a.saving.forFour??a.saving.perPack??0));
}
function benefit(recipe,products){
 const main=products.filter(x=>x.isMain),extras=products.filter(x=>!x.isMain);
 const sum=(list,field)=>{const known=list.filter(x=>Number.isFinite(x.saving?.[field]));return known.length?Math.round(known.reduce((n,x)=>n+x.saving[field],0)*100)/100:null};
 const mainSaving=sum(main,'forFour'),extraSaving=sum(extras,'forFour');
 // Actual four-portion savings outweigh product counts. Unknown amounts never turn
 // into a fabricated meal saving; a main promotion still gets relevance credit.
 const score=(main.length?80:0)+(mainSaving||0)*100+(extraSaving||0)*30+
  main.reduce((n,x)=>n+(x.saving.forFour===null?(x.saving.perPack||0)*20:0),0)+Math.min(products.length,5)*2;
 return {hasMain:main.length>0,main,extras,mainSaving,extraSaving,score};
}
function recipesForOffers({index,stores,offersByStore,engine,query='',ingredient=null,category='alle',source='all',basis='all',sort='deals',day=currentDay()}){
 if(!engine||!Array.isArray(index?.recipes))return [];
 const target=ingredient?engine.classify(ingredient):null,q=norm(query),rows=[];
 for(const recipe of index.recipes){
  if(!valid(recipe,engine)||(safeSources.has(source)&&recipe.source!==source))continue;
  if(category!=='alle'&&group(recipe)!==category)continue;
  const profiles=culinary().recipeProfiles(recipe);
  if(ingredient&&!profiles.some(p=>target?(ingredient.search_only?p.family===target.key:culinary().compatible(target.profile,p)):norm(recipe.title).includes(norm(ingredient.name))))continue;
  if(q&&!norm(recipe.title+' '+(recipe.cuisine||'')+' '+profiles.map(x=>x.family).join(' ')).includes(q))continue;
  let best=null;
  for(const store of stores||[]){
   const products=actionProducts(recipe,offersByStore?.[store],engine,day);
   if(products.length<2)continue;
   const value=benefit(recipe,products);
   if(basis==='main'&&!value.hasMain)continue;
   const item={store,products,count:products.length,...value};
   if(!best||item.score>best.score)best=item;
  }
  if(best)rows.push({recipe,matched:best,category:group(recipe),slow:slow(recipe),score:best.score});
 }
 // A source, method or category never earns enough variety credit to hide a
 // meaningful difference in the main-ingredient discount.
 const result=[],seen=new Set(),groups=new Map(),methods=new Map(),sources=new Map(),cuisines=new Map(),remaining=[...rows];
 while(remaining.length){
  const rank=x=>x.score-(groups.get(x.category)||0)*3-(methods.get(x.recipe.method)||0)*2-(sources.get(x.recipe.source)||0)*2-(cuisines.get(x.recipe.cuisine)||0)*2-(result.at(-1)?.category===x.category?5:0)-(result.at(-1)?.recipe.method===x.recipe.method?3:0);
  remaining.sort((a,b)=>sort==='time'?(a.recipe.minutes||999)-(b.recipe.minutes||999)||rank(b)-rank(a):rank(b)-rank(a)||a.recipe.title.localeCompare(b.recipe.title,'nl'));
  const row=remaining.shift(),title=norm(row.recipe.title);
  if(seen.has(title))continue;seen.add(title);result.push(row);
  groups.set(row.category,(groups.get(row.category)||0)+1);methods.set(row.recipe.method,(methods.get(row.recipe.method)||0)+1);sources.set(row.recipe.source,(sources.get(row.recipe.source)||0)+1);if(row.recipe.cuisine)cuisines.set(row.recipe.cuisine,(cuisines.get(row.recipe.cuisine)||0)+1);
 }
 return result;
}
return {valid,group,slow,purchase,discount,actionProducts,benefit,recipesForOffers};
});
