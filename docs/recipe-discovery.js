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
  kip:{label:'Onbewerkte kip',search:'kipfilet kipdij curry oven',match:/\b(kipfilet|kipdijfilet|kippendijfilet|kippendijreepjes|kippendij|kipdij|kipfiletblokjes|kipfiletreepjes|kiphaasjes|kippenborst)\b/,tags:['kipcurry','ovenschotel','roerbak']},
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
  garnalen:{label:'Garnalen',search:'garnalen roerbak curry',match:/\b(garnalen|rauwe\s+garnalen|scampi)\b/,tags:['garnalencurry','garnalenroerbak']},
  forel:{label:'Forel',search:'forelfilet oven groenten',match:/\b(forelfilet|forel\s+filet)\b/,tags:['forel uit de oven','vispannetje']},
  makreel:{label:'Makreel',search:'makreel hoofdgerecht salade',match:/\b(makreelfilet|makreel)\b/,tags:['makreelsalade','vispannetje']},
  varkenshaas:{label:'Varkenshaas',search:'varkenshaas groenten oven',match:/\b(varkenshaas|varkenshaasje)\b/,tags:['varkenshaas uit de oven','varkenshaas met champignons']},
  hamlappen:{label:'Hamlappen',search:'hamlappen stoven stoofpot',match:/\b(hamlappen|varkenslappen|varkenslap)\b/,tags:['varkensstoof','hamlappen uit de pan']},
  bonen:{label:'Bonen',search:'zwarte bonen witte bonen curry',match:/\b(zwarte\s+bonen|witte\s+bonen|kidneybonen|bruine\s+bonen)\b/,tags:['bonenstoof','chili']},
  boerenkool:{label:'Boerenkool',search:'boerenkool stamppot soep',match:/\bboerenkool\b/,tags:['boerenkoolstamppot','boerenkoolschotel']},
  spitskool:{label:'Spitskool',search:'spitskool roerbak ovenschotel',match:/\bspitskool\b/,tags:['spitskool roerbak','spitskoolschotel']},
  paksoi:{label:'Paksoi',search:'paksoi noedels wok',match:/\bpaksoi\b/,tags:['paksoi roerbak','paksoicurry']},
  prei:{label:'Prei',search:'prei ovenschotel groenten',match:/\bprei\b/,tags:['preischotel','preiroerbak']},
  venkel:{label:'Venkel',search:'venkel oven vis',match:/\bvenkel\b/,tags:['venkel uit de oven','venkel met vis']},
  courgettebloem:{label:'Courgettebloem',search:'courgettebloem recepten',match:/\bcourgettebloem\b/,tags:['gevulde courgettebloemen']},
  pindakaas:{label:'Pindakaas',search:'pindakaas satésaus noedels',match:/\bpindakaas\b/,tags:['satésaus','pindasaus']},
  champignons:{label:'Champignons',search:'champignons hoofdgerecht risotto',match:/\b(champignons|kastanjechampignons)\b/,tags:['risotto','champignonpan']},
  wortel:{label:'Wortel',search:'wortel gezonde ovenschotel',match:/\b(wortelen|wortels|wortel|bospeen|winterpeen)\b/,tags:['wortelstoof','ovenschotel']}
 };
 // Each publisher has a strict HTTPS allowlist; never promote arbitrary domains.
 // Only factual metadata and links are displayed, not their copyrighted instructions.
 const publisherUrlPatterns={
  'Allerhande':/^https:\/\/(?:www\.)?ah\.nl\/allerhande\//,
  'Jumbo':/^https:\/\/(?:www\.)?jumbo\.com\/recepten\//,
  'Voedingscentrum':/^https:\/\/www\.voedingscentrum\.nl\/recepten\/gezond-recept\//,
  '24Kitchen':/^https:\/\/www\.24kitchen\.nl\/recepten\//,
  'HelloFresh':/^https:\/\/www\.hellofresh\.nl\/recipes\/(?!market\/)[a-z0-9_-]+-[0-9a-f]{24}$/
 };
 const trustedPublisherUrl=(source,url)=>typeof url==='string'&&Boolean(publisherUrlPatterns[source]?.test(url));
 const unsafe=/\b(katten|kattenvoer|honden|hondenvoer|puppy|kitten|olvarit|babyvoeding|baby|schnitzel|worst|burger|saus|soep|snack|chips|crackers|koekjes|chocolade|ijs|reep|repen|salade|pizza|maaltijd|kruidenmix|marinade|dressing|brood|rollade|gerookt|gerookte|gepaneerd|plantaardig|vegetarisch|vegan|vega|dessert|smaak|poeder|thee|supplement|kruiden)\b/;
 function classify(offer){
  const raw=norm(offer?.name),cat=offer?.category;
  if(!raw||['bier','huishouden','overige_dranken','dranken','snacks'].includes(cat))return null;
  const household=/\b(vaatwas|wasmiddel|toiletpapier|shampoo|zeep|reiniger)\b/;
  if(household.test(raw)||unsafe.test(raw)||/(?:saus|soep|schotel|puree|salade|curry|pasta|burger|schnitzel|wokmix|groentemix|kruidenmix|maaltijd|crouton|pizza|brood|taart|cake|chips)\b/.test(raw))return null;
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
 function publisherMatches(offer,index,limit=10){
  const type=classify(offer);
  if(!type||!Array.isArray(index?.recipes))return [];
  const seen=new Set(),matches=[];
  for(const r of index.recipes){
   if(!r||!Array.isArray(r.families)||!r.families.includes(type.key)||
      typeof r.title!=='string'||!r.title.trim()||!trustedPublisherUrl(r.source,r.url)||
      !['handmatig_gevonden_bij_uitgever','publisher_metadata_verified','publisher_page_title_verified','publisher_sitemap_title_only'].includes(r.review_status))continue;
   if(['riblappen','gehakt','kip','zalm','witvis','garnalen'].includes(type.key)&&
      /\b(veggie|vegan|vegetarisch|vegetarische|plantaardig|plantaardige)\b/i.test(r.title))continue;
   if(seen.has(r.url))continue;
   seen.add(r.url);
   // Put main courses and recipes for four people ahead of side dishes,
   // but do not suggest that the original publisher recipe is priced.
   const vegetableCount=Number.isInteger(r.vegetable_families)?r.vegetable_families:
     r.families.filter(x=>['broccoli','bloemkool','spinazie','pompoen','paprika','courgette','aubergine','sperziebonen','tomaten','champignons','wortel','paksoi','prei','spitskool','boerenkool','venkel'].includes(x)).length;
   const legume=r.has_legumes||r.families.some(x=>['kikkererwten','linzen','bonen'].includes(x));
   // Official sitemap title does not establish ingredients, portions or health.
   const score=(r.review_status==='publisher_sitemap_title_only'?0:r.review_status==='publisher_page_title_verified'?24:65)+
    (r.course==='hoofdgerecht'?25:0)+(r.servings===4?6:0)+
    Math.min(vegetableCount,3)*5+(legume?5:0)+
    (r.minutes&&r.minutes<=45?5:0)+
    (type.key==='riblappen'&&/rendang|hachee|boeuf|stoof/i.test(r.title)?8:0);
   matches.push({recipe:r,score,ingredient:type.label});
  }
  return matches.sort((a,b)=>b.score-a.score||a.recipe.title.localeCompare(b.recipe.title,'nl')).slice(0,limit);
 }
 function offerRecipeHighlights(offers,index,limit=12){
  const candidates=[],seen=new Set();
  for(const offer of offers||[]){
   const family=classify(offer);
   if(!family)continue;
   for(const m of publisherMatches(offer,index,12)){
    const identity=m.recipe.url;
    if(seen.has(identity))continue;
    seen.add(identity);
    candidates.push({...m,offer,family:family.key});
   }
  }
  candidates.sort((a,b)=>b.score-a.score||a.recipe.title.localeCompare(b.recipe.title,'nl'));
  const found=[],used=new Set(),counts=new Map(),methods=new Map();
  for(let step=0;step<2;step++){
   for(const item of candidates){
    if(found.length>=limit)break;
    if(used.has(item.recipe.url))continue;
    const method=item.recipe.method||(/curry/i.test(item.recipe.title)?'curry':/stoof|rendang|hachee/i.test(item.recipe.title)?'stoof':/oven/i.test(item.recipe.title)?'oven':/wok|roerbak/i.test(item.recipe.title)?'wok':'anders');
    const byFamily=counts.get(item.family)||0,byMethod=methods.get(method)||0;
    if(byFamily>=(step===0?2:4)||byMethod>=(step===0?3:6))continue;
    found.push(item);used.add(item.recipe.url);
    counts.set(item.family,byFamily+1);methods.set(method,byMethod+1);
   }
   if(found.length>=limit)break;
  }
  return found;
 }
 function publisherSearch(offer){
  const item=classify(offer);if(!item)return [];
  const q=item.search;
  return [
   {source:'Allerhande',url:'https://www.google.com/search?q='+encodeURIComponent('site:ah.nl/allerhande/recept/ '+q)},
   {source:'Jumbo recepten',url:'https://www.google.com/search?q='+encodeURIComponent('site:jumbo.com/recepten/ '+q)}
  ];
 }
 return {classify,matchRecipe,localMatches,publisherSearch,publisherMatches,offerRecipeHighlights,trustedPublisherUrl};
});
