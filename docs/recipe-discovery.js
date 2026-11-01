/* Safe recipe discovery from currently observed grocery deals.
 * Match *culinary suitability*, not arbitrary substring overlaps or equal prices.
 * Publisher recipes are links, never copied into our recipe/feed data. */
(function(root,factory){
 const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeRecipeDiscovery=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const norm=x=>String(x||'').toLocaleLowerCase('nl-NL').normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const recipes={
  riblappen:{label:'Runder(rib)lappen om te stoven',search:'runderriblappen rendang hachee stoof',
   match:/\b(runder\s?rib\s?lappen|runder\s?lappen|riblappen|riblap|sukadelappen|sukadelap|stooflappen|stoofvlees)\b/,
   tags:['rendang','hachee','boeuf bourguignon','semur','stoofpot'],
   links:[
    {title:'Rendang met runderriblappen',source:'Allerhande',url:'https://www.ah.nl/allerhande/recept/R-R1194447/rendang'},
    {title:'Hachee met runderriblappen',source:'Allerhande',url:'https://www.ah.nl/allerhande/recepten/hachee'},
    {title:'Boeuf bourguignon uit de slowcooker',source:'Allerhande',url:'https://www.ah.nl/allerhande/recept/R-R1192994/boeuf-bourguignon-uit-de-slowcooker'},
    {title:'Riblappen: hachee, rendang en meer',source:'Jumbo',url:'https://www.jumbo.com/recepten/vlees/rundvlees/riblappen'}]},
  gehakt:{label:'Gehakt',search:'gehakt gehaktballen ovenschotel',match:/\b(rundergehakt|varkensgehakt|gemengd\s+gehakt|half\s+om\s+half\s+gehakt|mager\s+gehakt|gehakt)\b/,tags:['gehaktballen','chili','ovenschotel']},
  kip:{label:'Onbewerkte kip',search:'kipfilet kipdij curry oven',match:/\b(kipfilet|kipdijfilet|kipdij|kipfiletblokjes|kipfiletreepjes|kiphaasjes|kippenborst)\b/,tags:['kipcurry','ovenschotel','roerbak']},
  zalm:{label:'Zalmfilet',search:'zalmfilet oven groenten',match:/\b(zalmfilet|zalmzijde|zalm\s+filet)\b/,tags:['ovenzalm','pokebowl','zalm uit de oven']},
  witvis:{label:'Witvis',search:'kabeljauwfilet witvis oven',match:/\b(kabeljauwfilet|koolvisfilet|witvisfilet|heekfilet|pangasiusfilet|scholfilet|kabeljauw)\b/,tags:['visstoof','vis uit de oven']},
  tofu:{label:'Tofu en tempeh',search:'tofu tempeh vegetarische curry',match:/\b(tofu|tempeh|tempe)\b/,tags:['tofu curry','tempeh roerbak']},
  kikkererwten:{label:'Kikkererwten',search:'kikkererwten curry stoof',match:/\b(kikkererwten|chickpeas)\b/,tags:['curry','stoof','falafel']},
  linzen:{label:'Linzen',search:'linzen curry soep',match:/\b(linzen|linzenmix)\b/,tags:['dahl','linzenstoof']},
  broccoli:{label:'Broccoli',search:'broccoli gezonde hoofdgerechten',match:/\b(broccoli|broccoliroosjes)\b/,tags:['roerbak','pasta met broccoli']},
  bloemkool:{label:'Bloemkool',search:'bloemkool curry ovenschotel',match:/\b(bloemkool|bloemkoolroosjes)\b/,tags:['bloemkoolcurry','ovenschotel']},
  spinazie:{label:'Spinazie',search:'spinazie pasta curry',match:/\bspinazie\b/,tags:['spinaziecurry','pasta']},
  pompoen:{label:'Pompoen',search:'pompoen curry soep ovenschotel',match:/\b(pompoen|flespompoen)\b/,tags:['pompoencurry','pompoenstoof']},
  paprika:{label:'Paprika',search:'paprika gevulde paprika roerbak',match:/\bpaprika\b/,tags:['gevulde paprika','roerbak']},
  courgette:{label:'Courgette',search:'courgette ovenschotel pasta',match:/\bcourgette\b/,tags:['courgette ovenschotel','groentepan']},
  aubergine:{label:'Aubergine',search:'aubergine stoof ovenschotel',match:/\baubergine\b/,tags:['auberginestoof','moussaka']},
  sperziebonen:{label:'Sperziebonen',search:'sperziebonen hoofdgerecht',match:/\bsperziebonen\b/,tags:['sperziebonen curry','roerbak']},
  tomaten:{label:'Tomaten',search:'tomaten groente hoofdgerecht',match:/\b(tomaten|trostomaten|cherrytomaten|tomatenblokjes)\b/,tags:['tomatenstoof','pasta']},
  aardappelen:{label:'Aardappelen',search:'aardappelen gezonde ovenschotel',match:/\b(aardappelen|aardappel|krieltjes)\b/,tags:['aardappelgratin','ovenschotel']},
  eieren:{label:'Eieren',search:'eieren frittata omelet',match:/\b(eieren|scharreleieren|vrije\s+uitloop\s+eieren)\b/,tags:['frittata','omelet']},
  pindakaas:{label:'Pindakaas',search:'pindakaas satésaus noedels',match:/\bpindakaas\b/,tags:['satésaus','pindasaus']},
  champignons:{label:'Champignons',search:'champignons hoofdgerecht risotto',match:/\b(champignons|kastanjechampignons)\b/,tags:['risotto','champignonpan']},
  wortel:{label:'Wortel',search:'wortel gezonde ovenschotel',match:/\b(wortelen|wortels|wortel|bospeen|winterpeen)\b/,tags:['wortelstoof','ovenschotel']}
 };
 const unsafe=/\b(katten|kattenvoer|honden|hondenvoer|puppy|kitten|olvarit|babyvoeding|baby|schnitzel|worst|burger|saus|soep|snack|chips|crackers|koekjes|chocolade|ijs|reep|repen|salade|pizza|maaltijd|kruidenmix|marinade|dressing|brood|rollade|gerookt|gerookte|gepaneerd|plantaardig|vegetarisch|vegan|vega|dessert|smaak|poeder|thee|supplement|kruiden)\b/;
 function classify(offer){
  const raw=norm(offer?.name),cat=offer?.category;
  if(!raw||['bier','huishouden','overige_dranken','dranken','snacks'].includes(cat))return null;
  const household=/\b(vaatwas|wasmiddel|toiletpapier|shampoo|zeep|reiniger)\b/;
  if(household.test(raw)||unsafe.test(raw))return null;
  for(const [key,meta] of Object.entries(recipes)){
   if(meta.match.test(raw)){
    if(key==='riblappen'&&/\b(biefstuk|rundergehakt|ossenhaas|entrecote)\b/.test(raw))return null;
    return {key,label:meta.label,tags:meta.tags,search:meta.search,links:meta.links||[]};
   }
  }
  return null;
 }
 function matchRecipe(offer,recipe){
  const type=classify(offer);if(!type||!Array.isArray(recipe?.ingredients))return null;
  const meta=recipes[type.key];
  const ingredient=recipe.ingredients.find(i=>{
   const t=norm(i.name);
   if(unsafe.test(t))return false;
   if(type.key==='riblappen')return meta.match.test(t);
   return meta.match.test(t);
  });
  if(!ingredient)return null;
  // Slow cuts are never suitable for quick beef stir-fry just because both are red meat.
  if(type.key==='riblappen'&&Number(recipe.minutes)<95&&!/stoof|rendang|hachee|semur|riblappen/i.test(recipe.title))return null;
  return {recipe,ingredient:ingredient.name,match:'culinary_family',score:type.key==='riblappen'?15:12};
 }
 function localMatches(offer,list,limit=7){
  if(!classify(offer))return [];
  const seen=new Set(),matches=[];
  for(const recipe of list||[]){
   if(recipe.quality_status==='concept_niet_culinair_getest')continue;
   const result=matchRecipe(offer,recipe);
   if(!result)continue;
   const key=norm(recipe.title);
   if(seen.has(key))continue;seen.add(key);matches.push(result);
  }
  return matches.sort((a,b)=>b.score-a.score||(a.recipe.minutes||999)-(b.recipe.minutes||999)).slice(0,limit);
 }
 function publisherSearch(offer){
  const item=classify(offer);if(!item)return [];
  const q=item.search;
  return [
   {source:'Allerhande',url:'https://www.google.com/search?q='+encodeURIComponent('site:ah.nl/allerhande/recept/ '+q)},
   {source:'Jumbo recepten',url:'https://www.google.com/search?q='+encodeURIComponent('site:jumbo.com/recepten/ '+q)}
  ];
 }
 return {classify,matchRecipe,localMatches,publisherSearch};
});
