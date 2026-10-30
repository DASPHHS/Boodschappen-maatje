/* Per-ingredient shopping OPTIONS from dated external shelf observations.
 * Never write prices to a recipe, and never imply a complete verified basket. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeRecipeShopOptions=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const normalize=x=>String(x||'').toLocaleLowerCase('nl-NL').normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const forbidden=[
  'saus','soep','mix','maaltijd','burger','schnitzel','gerookt','gemarineerd',
  'gekruid','vulling','salade','pizza','chips','kruiden','dressing','baby','gepaneerd'
 ];
 const variants={
  'kipfilet':{all:['kipfilet'],none:['haasjes','reepjes','blokjes','diepvries']},
  'magere kwark':{all:['magere','kwark'],none:['drank','high protein','lactosevrij']},
  'mager rundergehakt':{all:['mager','rundergehakt'],none:['gemengd']},
  'kabeljauwfilet':{all:['kabeljauwfilet'],none:['vissticks','gerookt']},
  'zalmfilet':{all:['zalmfilet'],none:['gerookt','kruiden','gravad','burger']},
  'broccoli':{all:['broccoli'],none:['rijst','puree','schotel','wokmix','saus','diepvries']},
  'boerenkool':{all:['boerenkool'],none:['stamppot','gekruid','schotel']},
  'paprika':{all:['paprika'],none:['poeder','pasta','saus','chips','mix','puntpaprika']},
  'diepvries sperziebonen':{all:['sperziebonen'],any:['diepvries','bevroren']},
  'magere yoghurt':{all:['magere','yoghurt']},
  'tofu':{all:['tofu'],none:['gerookt']},
  'stevige tofu':{all:['tofu'],none:['gerookt','zijde']},
  'tempeh':{all:['tempeh']},
  'tomatenblokjes':{all:['tomatenblokjes']},
  'tomatenpuree':{all:['tomatenpuree']},
  'paksoi':{all:['paksoi'],none:['wokmix']},
  'courgette':{all:['courgette'],none:['gevuld']},
  'venkel':{all:['venkel'],none:['thee']},
  'wortel':{all:['wortel'],none:['taart','sap']},
  'spitskool':{all:['spitskool'],none:['maaltijd']},
  'harissa':{all:['harissa'],none:['kruidenmix']}
 };
 // Explicit ingredient aliases preserve preparation and product type.
 const aliases={
 'broccoli met eetbare stronk':'broccoli','verse paprika':'paprika',
 'volkoren pasta droog':'volkoren pasta','volkoren couscous droog':'volkoren couscous',
 'volkoren noedels droog':'volkoren noedels','zilvervliesrijst droog':'zilvervliesrijst',
 'orzo droog':'orzo','rode linzen droog':'rode linzen','hamlappen dun gesneden':'hamlappen',
 'biefstuk dun gesneden':'biefstuk','verse tomaten':'tomaten','olie':'zonnebloemolie',
 'kipdijfilet zonder huid':'kipdijfilet','zalmfilet zonder huid':'zalmfilet',
 'witvisfilet zonder huid':'kabeljauwfilet','haver':'havermout','za atar':'zaatar'
 };
 const simple=['champignons','cottage cheese','paprikapoeder','gerookt paprikapoeder',
 'zonnebloemolie','mosterd','prei','volkoren pasta','kerriepoeder','volkoren couscous',
 'rozemarijn','komkommer','volkoren noedels','sojasaus','knoflook','ras el hanout',
 'kaneel','zilvervliesrijst','groene currypasta','kokosmelk','pindakaas','orzo',
 'hamlappen','gember','biefstuk','sperziebonen','ui','eieren','havermout','tomaten',
 'komijn','Italiaanse kruiden','varkenshaas','spinazie','appel','dille','gepelde garnalen',
 'rode linzen','edamame','tahin','zaatar','aubergine','miso','sesamzaad','chipotle',
 'sambal','bloemkool','sumak','kipdijfilet','citroengras','limoensap','citroensap',
 'oregano','bosui','vissaus','munt','bospeen','witte kool','tauge'];
 const extraExclusions=['sap','saus','soep','salade','maaltijd','pizza','chips','burger',
 'dressing','snoep','chocolade','cake','taart','brood','wafels','baby','groentehapje',
 'supplement','capsules','thee','shampoo','zeep','creams','schoonmaak','bouillon',
 'pesto','borsin','boursin','boter','worst','aardappel','naanbrood','snack','borrel',
 'gevuld','gekruid','gemarineerd','gerookt','poeder','kruiden','mix','kant en klaar'];
 for(const name of simple){
  const key=normalize(name);
  if(!variants[key])variants[key]={all:[key],none:extraExclusions.filter(x=>!(' '+key+' ').includes(' '+x+' '))};
 }
 // Sauces/spices are ingredients themselves; exclusions must not reject their own type.
 function ingredientRule(name){
  const key=normalize(name),canonical=aliases[key]||key;
  return {key:canonical,rule:variants[canonical]};
 }
 // A word match alone also finds pet food, flavored snacks and mixed meals.
 // Require every remaining word to describe a known brand or the ingredient itself.
 const commonWords=new Set(normalize('AH Jumbo Lidl Albert Heijn biologisch biologische bio Terra Verstegen Kania Ducros Bonduelle Hak Conimex Fairtrade Go Tan Koh Thai Le Phare Du Cap Bon Lemondor Polenghi Sebahat Golden Seafood Vemondo Freshona Milbona Chef Select Chtoura Al Fez Lassie Lezziz Mama s De Zaanse Hoeve Mill Mortar extra xxl voordeelverpakking grootverpakking kleinverpakking verpakking pak zak zakje pot fles naturel vers verse rauw rauwe ongekruid ongekruide gesneden fijngesneden fijn fijne grove groot grote klein kleine mini mild milde light naturel gemalen geperst gepeld gepelde scharrel halal bl beter leven nl nederlands nederlandse per stuks stuk st g kg ml cl l x').split(' '));
 const ingredientWords={
  kipfilet:'kipfilet filethaasjes',
  'kipdijfilet':'kipdijfilet reepjes blokjes',
  champignons:'witte kastanje kastanjechampignons',
  broccoli:'roosjes stronk stronken',
  wortel:'wortels wortelen winterpeen waspeen geraspt',
  spinazie:'gehakte bladspinazie deelblokjes',
  bloemkool:'roosjes deelblokjes',
  boerenkool:'deelblokjes gesneden',
  sperziebonen:'gebroken heel hele',
  'diepvries sperziebonen':'gebroken heel hele diepvries bevroren',
  paprika:'rood rode geel gele groen groene oranje puntpaprika',
  tomaten:'tros trostomaten roma cherrytomaten kerstomaten',
  appel:'appels elstar jonagold gala granny smith pink lady',
  ui:'uien geel gele rood rode wit witte',
  komkommer:'snoepgroente snoepkomkommer mini',
  zalmfilet:'wilde noorse atlantische zonder huid porties',
  kabeljauwfilet:'zonder huid filets',
  biefstuk:'rund rundvlees kogel ossenhaas',
  'magere kwark':'franse fransekwark magere mager',
  tofu:'stevige stevig firm zacht zachte zijden',
  'stevige tofu':'stevig firm',
  edamame:'sojabonen boontjes',
  'rode linzen':'gedroogde',
  'zilvervliesrijst':'droog droge',
  'volkoren pasta':'spaghetti penne fusilli macaroni',
  'volkoren noedels':'noodles mie',
  tahin:'sesampasta',
  miso:'pasta rood rode wit witte',
  harissa:'pasta',
  sambal:'oelek badjak',
  'groene currypasta':'curry pasta',
  kokosmelk:'romig romige vet',
  eieren:'ei eieren vrije uitloop maten maat m l xl s',
  havermout:'vlokken volkoren',
  pindakaas:'pinda pindas pinda s pinda’s stukjes',
  'Italiaanse kruiden':'italiaanse italiaans kruiden kruidenmix',
 };
 const freshProduce=new Set(['paprika','tomaten','knoflook','gember','citroengras','wortel','courgette','komkommer','aubergine','venkel','prei','ui','bosui','paksoi','appel']);
 function plainIngredient(name,key,rule){
  const allowed=new Set([...commonWords,...normalize(key).split(' '),
   ...(rule.all||[]).flatMap(x=>normalize(x).split(' ')),
   ...(rule.any||[]).flatMap(x=>normalize(x).split(' ')),
   ...normalize(ingredientWords[key]||'').split(' ')]);
  if((freshProduce.has(key)||['sperziebonen','broccoli','bloemkool','spinazie','boerenkool'].includes(key))&&/\bhak\b/.test(normalize(name)))return false;
  if(freshProduce.has(key)&&/\b(gemalen|poeder|gedroogd|gedroogde|gepeld|gepelde|gezeefd|gezeefde|blik|pot)\b/.test(normalize(name)))return false;
  if(key==='stevige tofu'&&/\b(zacht|zachte|zijde|zijden|silken)\b/.test(normalize(name)))return false;
  return normalize(name).split(' ').every(word=>/^\d+(?:g|kg|ml|cl|l|st|stuks)?$/.test(word)||allowed.has(word));
 }
 function measuredPack(row,pricing,unit){
  const parsed=pricing.pack({name:row[0],pack_label:row[2]});
  if(parsed)return parsed;
  if(unit!=='stuk')return null;
  const label=normalize(row[2]);
  const match=label.match(/^(\d+) (?:stuks?|st)$/);
  if(match)return {amount:Number(match[1]),unit:'stuk',approximate:false};
  if(/^(?:per stuk|1 stuk|stuk)$/.test(label))return {amount:1,unit:'stuk',approximate:false};
  return null;
 }
 const indexes=new WeakMap();
 function candidates(catalog,store,rule){
  let stores=indexes.get(catalog);if(!stores){stores=new Map();indexes.set(catalog,stores)}
  let index=stores.get(store);
  if(!index){index=new Map();for(const row of catalog.stores[store]){
   if(!Array.isArray(row))continue;
   for(const token of new Set(normalize(row[0]).split(' '))){
    if(!index.has(token))index.set(token,[]);index.get(token).push(row);
   }
  }stores.set(store,index)}
  const lists=(rule.all||[]).flatMap(term=>normalize(term).split(' ')).map(token=>index.get(token)||[]);
  return lists.length?lists.reduce((a,b)=>a.length<=b.length?a:b):[];
 }
 function recommend(recipe,store,catalog,pricing,resolver,today){
  const ingredients=Array.isArray(recipe?.ingredients)?recipe.ingredients:[];
  const blank={rows:[],matched:0,required:ingredients.length,source_date:catalog?.source_date||null,
   source:'Checkjebon',available:false};
  if(!['lidl','jumbo','ah'].includes(store)||!catalog||!pricing?.pack||!pricing?.inspect||
   !resolver?.matching||!(/^\d{4}-\d\d-\d\d$/.test(today))||
   !Array.isArray(catalog.stores?.[store])||!catalog.source_date)return blank;
  const age=Math.round((Date.parse(today+'T12:00:00Z')-Date.parse(catalog.source_date+'T12:00:00Z'))/86400000);
  if(!Number.isFinite(age)||age<0||age>3)return blank;
  const rows=[];
  for(const ing of ingredients){
   const label=normalize(ing?.name),q=Number(ing?.quantity);
   const requiredUnit=({g:'kg',kg:'kg',ml:'L',l:'L',L:'L',st:'stuk',stuk:'stuk'})[ing?.unit]||null;
   const {key,rule}=ingredientRule(label);
   if(!rule||!requiredUnit||!Number.isFinite(q)||q<=0)continue;
   const required=q/(['g','ml'].includes(ing.unit)?1000:1),profile={match:{all:rule.all,any:rule.any||[],none:[...forbidden.filter(x=>!(' '+key+' ').includes(' '+x+' ')),...(rule.none||[])]}};
   let chosen=null;
   for(const row of candidates(catalog,store,rule)){
    if(!Array.isArray(row)||typeof row[0]!=='string'||!Number.isFinite(row[1])||row[1]<=0||
      typeof row[2]!=='string'||row[2].length>80)continue;
    const name=row[0];
    if(!plainIngredient(name,key,rule))continue;
    if(resolver.matching({name,pack_label:row[2]},profile,pricing).status!=='match')continue;
    const p=measuredPack(row,pricing,requiredUnit);
    if(!p||p.approximate||p.unit!==requiredUnit||p.amount<=0||p.amount>(requiredUnit==='stuk'?60:15))continue;
    const count=Math.ceil((required-1e-9)/p.amount);
    if(count<1||count>12)continue;
    const item={name,price:row[1],pack_label:row[2],store,
     status:'external_regular_observed',source_provider:'Checkjebon',
     checked_date:catalog.source_date,url:row[3]||catalog.source_url};
    const inspected=pricing.inspect(item,store,today);
    if(!inspected?.current||inspected.conflict)continue;
    const total=Math.round(count*row[1]*100)/100;
    if(!Number.isFinite(total)||total<=0||total>300)continue;
    if(!chosen||total<chosen.purchase_total-0.001||
      (Math.abs(total-chosen.purchase_total)<0.001&&count<chosen.pack_count)){
     chosen={ingredient:ing.name,quantity:q,unit:ing.unit,product:name,
      pack_label:row[2],pack_count:count,unit_price:Math.round(row[1]*100)/100,
      purchase_total:total,consumption_total:Math.round(required/p.amount*row[1]*100)/100,url:item.url,source_date:catalog.source_date};
    }
   }
   if(chosen)rows.push(chosen);
  }
  return {rows,matched:rows.length,required:ingredients.length,source_date:catalog.source_date,
   source:'Checkjebon',available:true};
 }
 function estimate(recipe,store,catalog,pricing,resolver,today){
  const options=recommend(recipe,store,catalog,pricing,resolver,today);
  const rows=options.rows,missing=(recipe?.ingredients||[]).filter(i=>!rows.some(r=>r.ingredient===i.name)).map(i=>i.name);
  const partial=Math.round(rows.reduce((sum,r)=>sum+r.purchase_total,0)*100)/100;
  const complete=options.required>0&&missing.length===0;
  return {...options,state:complete?'catalog_estimate':rows.length?'partial':'unpriced',
   total:complete?partial:null,partial,missing,priced_count:rows.length,
   oldest_date:options.source_date,unverified:true,
   consumption_total:Math.round(rows.reduce((sum,r)=>sum+r.consumption_total,0)*100)/100};
 }
 return {recommend,estimate};
});
