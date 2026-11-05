/* Culinary product identity shared by discovery, ranking and metadata import.
 * A recipe ingredient is a product type + variant + preparation, never a substring. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.MaatjeRecipeProducts=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const VERSION=2;
const norm=x=>String(x||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
const definitions=[
 ['kwark','vega',/\bkwark\b/],['yoghurt','vega',/\b(yoghurt|yogurt)\b/],
 ['havermout',null,/\bhavermout\b/],['brood',null,/\b(volkorenbrood|witbrood|meergranenbrood|brood)\b/],
 ['komkommer',null,/\bkomkommer\b/],['appel',null,/\b(appel|appels|appeltjes)\b/],['banaan',null,/\b(banaan|bananen)\b/],
 ['blauwe_bessen',null,/\bblauwe bessen\b/],['walnoten',null,/\bwalnoten\b/],
 ['kip','kip',/\b(kipfilet(?:blokjes|reepjes|haasjes)?|kiphaasjes|kippenborst|kip(?:pen)?dij(?:filet)?(?:reepjes|blokjes)?|kippen?bout(?:en)?|kippenpoten|drumsticks)\b/],
 ['riblappen','vlees',/\b(runder\s?rib\s?lappen|runderlappen|riblappen|riblap|sukadelappen|sukadelap|stooflappen|stoofvlees)\b/],
 ['gehakt','vlees',/\b(rundergehakt|varkensgehakt|gemengd gehakt|half om half gehakt|mager gehakt|gehakt)\b/],
 ['varkenshaas','vlees',/\bvarkenshaas(?:je|jes)?\b/],['hamlappen','vlees',/\b(hamlappen|varkenslappen|varkenslap)\b/],
 ['biefstuk','vlees',/\b(biefstuk(?:reepjes)?|entrecote|ossenhaas|rundvleesreepjes)\b/],
 ['zalm','vis',/\b(zalm(?:filet|zijde|blokjes)?|zalm filet)\b/],
 ['witvis','vis',/\b(kabeljauw(?:filet)?|koolvis(?:filet)?|witvisfilet|heek(?:filet)?|pangasius(?:filet)?|schol(?:filet)?)\b/],
 ['garnalen','vis',/\b(garnalen|scampi)\b/],['forel','vis',/\bforel(?:filet)?\b/],['makreel','vis',/\bmakreel(?:filet)?\b/],
 ['tofu','vega',/\b(tofu|tempeh|tempe)\b/],['kikkererwten','vega',/\b(kikkererwten|chickpeas)\b/],
 ['linzen','vega',/\b(rode linzen|groene linzen|linzen)\b/],['bonen','vega',/\b(zwarte bonen|witte bonen|kidneybonen|bruine bonen)\b/],
 ['eieren','vega',/\b(eieren|ei|scharreleieren|vrijeuitloopeieren|scharrelei)\b/],
 ['halloumi','vega',/\bhalloumi\b/],['feta','vega',/\b(feta|witte kaas)\b/],
 ['broccoli',null,/\b(broccoli|broccoliroosjes)\b/],['bloemkool',null,/\b(bloemkool|bloemkoolroosjes)\b/],
 ['spinazie',null,/\b(bladspinazie|spinazie)\b/],['pompoen',null,/\b(pompoen|flespompoen)\b/],
 ['paprika',null,/\b(paprika(?:s)?|puntpaprika(?:s)?)\b/],['courgette',null,/\bcourgette(?:s)?\b/],
 ['aubergine',null,/\baubergine(?:s)?\b/],['sperziebonen',null,/\b(sperziebonen|sperzieboontjes)\b/],
 ['tomaten',null,/\b(tomaten|tomaat|trostomaten|cherrytomaten|tomatenblokjes|tomatenpuree|gepelde tomaten)\b/],
 ['aardappelen',null,/\b(aardappelen|aardappel|krieltjes|stamppotaardappelen)\b/],
 ['champignons',null,/\b(champignons|kastanjechampignons|paddenstoelen)\b/],['wortel',null,/\b(wortel(?:en|s)?|bospeen|winterpeen|waspeen)\b/],
 ['paksoi',null,/\bpaksoi\b/],['prei',null,/\bprei(?:en)?\b/],['spitskool',null,/\bspitskool\b/],['witte_kool',null,/\bwitte kool\b/],
 ['boerenkool',null,/\bboerenkool\b/],['venkel',null,/\bvenkel\b/],['spruitjes',null,/\bspruitjes\b/],
 ['ui',null,/\b(uien|ui|sjalot(?:ten)?)\b/],['knoflook',null,/\bknoflook\b/],['citroen',null,/\bcitroen(?:en)?\b/],['limoen',null,/\blimoen(?:en)?\b/],
 ['pindakaas',null,/\bpindakaas\b/],['rijst',null,/\b(basmatirijst|jasmijnrijst|zilvervliesrijst|rijst)\b/],
 ['pasta',null,/\b(pasta|spaghetti|penne|fusilli|tagliatelle|orzo)\b/],['noedels',null,/\b(noedels|noodles|udonnoedels)\b/]
];
const baseWords='ah jumbo lidl albert heijn vivera vemondo freshona milbona bonduelle hak boni bio biologisch biologische scharrel halal beter leven bl vers verse rauw rauwe naturel ongekruid ongekruide neutraal extra fijne fijn fijngesneden gesneden heel hele gebroken roosjes stronk stronken gepeld gepelde zonder met vel huid op wit witte rood rode groen groene geel gele oranje mager magere gemengd half om droog droge uitgelekt uitlekgewicht blik pot zak pak zakje per bos net voordeel voordeelverpakking grootverpakking verpakking xxl xl stuks stuk st s g gram gr kg kilogram ml milliliter cl l liter x ca circa portie porties diepvries bevroren ingevroren gewassen schoon schoongemaakt in blokjes reepjes haasjes filets filet ASC MSC beterleven 1ster 2sterren 3sterren duurzaam hollandse nederlandse noorse atlantische wilde alaska vastkokend vastkokende kruimig kruimige stamppot pofmais pan ovengroente a la of en uit eigen keuken bereid houdbaar houdbare runder varkens rund';
const brands='campina kanzi elstar jonagold optimel arla quaker mild milde griekse greeks ongezoet halfvolle volle magere eiwitrijke volkoren 100 procent calve terra conimex blue elephant go tan koh thai fairtrade lassie grand italia gallo soubry perfect earth koro valle del sole valfrutta mutti cirio la molisana royal green garden naturli de vegetarische slager valess quorn beyond meat heura taylors gold golden seafood dirk damhert leev greenforce ekoplaza';
const allowed=new Set((baseWords+' '+brands).split(' '));
const forbidden=/(?:saus|sauce|soep|soup|salade|schotel|maaltijd|kruidenmix|maaltijdmix|bakplaatmix|bakmix|brood|wrap|pizza|chips|snack|nuggets?|schnitzel|vissticks?|kroket|koekjes?|taart|cake|smoothie|sap|sapje|tapenade|hoemoes|hummus|dip|dressing|spread|hapjes?|balletjes?|borrel|knijpfruit|bouillon)\b|\b(mix|gevuld|gevulde|americain|gerookt|gerookte|gegrild|gegrilde|gebakken|gebraden|voorgegaard|gepaneerd|gemarineerd|gekruid|kruiden|baby|olvarit|organix|whiskas|felix|sheba|kattenvoer|hondenvoer|poeder)\b/;
function quantity(text){
 let t=String(text||'').replace(/½/g,' 0.5').replace(/¼/g,' 0.25').replace(/¾/g,' 0.75').replace(/⅓/g,' 0.333').replace(/⅔/g,' 0.667').replace(/,/g,'.');
 const m=t.trim().match(/^(\d+(?:\.\d+)?)(?:\s+(0\.\d+))?\s*(kilogram|kg|gram|gr|g|milliliter|ml|liter|l|stuks?|ei(?:eren)?|scharreleieren|preien)\b/i);
 if(!m)return {};
 let n=Number(m[1])+Number(m[2]||0),unit=m[3].toLowerCase();
 if(/^(kg|kilogram)$/.test(unit)){n*=1000;unit='g'}else if(/^(gram|gr)$/.test(unit))unit='g';
 else if(/^(l|liter)$/.test(unit)){n*=1000;unit='ml'}else if(!['g','ml','milliliter'].includes(unit))unit='stuk';
 if(unit==='milliliter')unit='ml';
 return {quantity:Math.round(n*1000)/1000,unit};
}
function animalGroup(raw){
 if(/vegetarisch|vegan|veggie|plantaardig|bouillon|kruidenmix/.test(raw))return null;
 if(/\b(kip|kippenbout(?:en|jes)?|kipgehakt|kipfilet|kippendij|kalkoen(?:filet)?)\b/.test(raw))return 'kip';
 if(/\b(zalm|zalmfilet|gerookte zalm|vis|visfilet|tonijn|ansjovis(?:filets)?|kabeljauw|koolvis|garnalen|mosselen|haring)\b/.test(raw))return 'vis';
 if(/\b(rund(?:vlees)?|varken(?:svlees)?|lam(?:svlees)?|lamsgehakt|eend(?:enborst)?|hert(?:envlees)?|gehakt|biefstuk|spek(?:reepjes|blokjes)?|bacon|ham(?:blokjes|lapjes)?|rookworst|worst(?:jes)?|hamburger(?:s)?|runderburger(?:s)?|chorizo|salami|saucijs(?:jes)?)\b/.test(raw))return 'vlees';
 return null;
}
function isDeliChicken(o){
 const name=norm(o?.name),e=o?.semantic_evidence;
 const categories=e?.verified_identity===true?norm((e.categories||[]).join(' ')):'';
 if(!/kipfilet|scharrelkipfilet/.test(name))return false;
 if(/vleeswaren|broodbeleg/.test(categories)||/broodbeleg|vleeswaren|flinterdun|oven(?:ge)?bakken|gerookt|gebraden|plakjes/.test(name))return true;
 // The Jumbo product sold under this ambiguous name is sandwich meat, also
 // in larger packs. Weight alone never establishes raw chicken.
 const jumbo=/^jumbo scharrel ?kipfilet\b/.test(name);
 const rawEvidence=/\b(rauw|rauwe|vers|verse)\b/.test(name)||/verse kip|vers vlees|kip kalkoen/.test(categories);
 return jumbo&&!rawEvidence;
}
function displayCategory(o){return isDeliChicken(o)?'vleeswaren':o?.category;}
function profile(value,{ingredient=false}={}){
 const o=typeof value==='string'?{name:value}:value||{},raw=norm(o.name).replace(/\bscharrel(?=kip)/g,''),n=raw.replace(/\b\d+(?:g|kg|gr|ml|cl|l|st|stk|stuks)?\b/g,' ').replace(/\s+/g,' ').trim();
 if(isDeliChicken(o))return ingredient?{family:'broodbeleg_kip',group:null,variant:/gerookt/.test(raw)?'smoked':/tuinkruiden/.test(raw)?'herbs':'plain',form:'cooked',...quantity(o.name)}:null;
 if(!raw||['huishouden','bier','dranken','overige_dranken','snacks'].includes(o.category))return null;
 if(/(?:katten|honden|babyvoeding|knijpfruit|shampoo|vaatwas|wasmiddel|supplement)/.test(raw))return null;
 // A plant-based fish/meat analogue is a distinct main ingredient; never a vegetable.
 const plant=/\b(plantaardig(?:e)?|vegetarisch(?:e)?|vegan|vega|veggie)\b/.test(raw);
 if(plant&&/\b(zalmfilet|visfilet|kipfilet|gehakt|filet|burger)\b/.test(raw)){
  if(forbidden.test(raw.replace(/burger/g,'')))return null;
  const kind=/zalm|visfilet/.test(raw)?'vis':/gehakt/.test(raw)?'gehakt':/burger/.test(raw)?'burger':/spinazie/.test(raw)?'spinaziekaas':'filet';
  const small=String((o.name||'')+' '+(o.pack_label||'')).match(/(\d+)\s*g(?:ram)?\b/i);
  if(!ingredient&&small&&Number(small[1])<180)return null;
  return {family:'vega_'+kind,group:'vega',variant:kind,form:'substitute',...quantity(o.name)};
 }
 if(plant&&/\b(kip|rund|riblappen|varken|zalm|vis)\b/.test(raw))return null;
 const matches=definitions.filter(d=>d[2].test(raw));
 if(!matches.length){const animal=ingredient?animalGroup(raw):null;return animal?{family:'other_'+animal,group:animal,variant:'unsupported',form:'unsupported',...quantity(o.name)}:null;}
 let [family,group,pattern]=matches[0];
 // Composite products are rejected before any ingredient word can qualify them.
 if(forbidden.test(family==='brood'?raw.replace(pattern,''):raw))return ingredient&&group&&!/bouillon|saus|soep|mix/.test(raw)?{family:'other_'+group,group,variant:'unsupported',form:'unsupported',...quantity(o.name)}:null;
 // Raw product descriptions naming another ingredient do not establish a plain product.
 if(!ingredient&&matches.length>1)return null;
 let form='plain',variant=null;
 if(/\b(gekookt|gekookte|voorgekookt|voorgekookte)\b/.test(raw))form='cooked';
 if(/halfgedroogd|halfgedroogde|zongedroogd|zongedroogde|gedroogd|gedroogde/.test(raw))form='dried';
 if(family==='tomaten'&&/tomatenpuree/.test(raw))form='puree';
 else if(family==='tomaten'&&/tomatenblokjes|gepelde|blik|pot/.test(raw))form='canned';
 if(['kwark','yoghurt'].includes(family))variant=plant?'plant':/\b(mager|magere)\b/.test(raw)?'lean':/\b(vol|volle)\b/.test(raw)?'full':'dairy';
 if(family==='tofu')variant=/tempeh|tempe\b/.test(raw)?'tempeh':/zacht|zijde|silken/.test(raw)?'soft':'firm';
 if(family==='kip')variant=/dij/.test(raw)?'thigh':/bout|poten|drumstick/.test(raw)?'leg':'breast';
 if(family==='witvis')variant=/kabeljauw/.test(raw)?'cod':/koolvis/.test(raw)?'pollock':/pangasius/.test(raw)?'pangasius':/schol/.test(raw)?'plaice':/heek/.test(raw)?'hake':'whitefish';
 if(family==='gehakt')variant=/runder|\brund\b/.test(raw)?'beef':/varken/.test(raw)?'pork':/gemengd|half om half/.test(raw)?'mixed':'unspecified';
 if(family==='bonen')variant=/kidney/.test(raw)?'kidney':/zwarte/.test(raw)?'black':/witte/.test(raw)?'white':'brown';
 if(family==='linzen')variant=/rode/.test(raw)?'red':/groene/.test(raw)?'green':'unspecified';
 if(!ingredient){
  const grams=String((o.name||'')+' '+(o.pack_label||'')).match(/(\d+)\s*g(?:ram)?\b/i);
  if(['kip','vlees','vis'].includes(group)&&grams&&Number(grams[1])<180)return null;
  let rest=n.replace(pattern,' ').replace(/\b(?:halfgedroogde?|zongedroogde?|gedroogde?|tomatenpuree|tomatenblokjes|zachte?|zijde|zijden|silken|stevig|stevige|firm|rode|groene|bruine|zwarte|kabeljauwfilet|scharrelkipfilet)\b/g,' ');
  const brand=norm(o.brand||'').split(' '),unknown=rest.split(/\s+/).filter(t=>t&&!allowed.has(t)&&!brand.includes(t));
  if(unknown.length)return null;
 }
 return {family,group,variant,form,...(['kwark','yoghurt'].includes(family)?{flavour:/vanille|vanilla/.test(raw)?'vanilla':/aardbei|mango|banaan/.test(raw)?'flavoured':'plain'}:{}),...(/uitgelekt|uitlekgewicht/.test(raw)?{drained:true}:{}),...quantity(o.name)};
}
function compatible(a,b){
 if(!a||!b||a.family!==b.family||a.form!==b.form)return false;
 if((a.flavour||'plain')!==(b.flavour||'plain'))return false;
 if(a.variant===b.variant)return true;
 if(['kwark','yoghurt'].includes(b.family)&&b.variant==='dairy')return ['lean','full'].includes(a.variant);
 // Unspecified mince/lentils/whitefish in an original recipe permit the named kind.
 return ['gehakt','linzen','witvis'].includes(b.family)&&['unspecified','whitefish'].includes(b.variant);
}
function recipeProfiles(recipe){
 if(Array.isArray(recipe?.ingredients))return recipe.ingredients.map(i=>{const p=profile(i.name,{ingredient:true});return p?{...p,...(i.quantity>0?{quantity:i.quantity,unit:i.unit==='st'?'stuk':i.unit}:{})}:null}).filter(Boolean);
 return recipe?.ingredient_profile_version===VERSION&&Array.isArray(recipe.ingredient_profiles)?recipe.ingredient_profiles:[];
}
function group(recipe){
 if(['kip','vlees','vis','vega'].includes(recipe?.category))return recipe.category;
 const p=recipeProfiles(recipe),animal=p.find(x=>['kip','vlees','vis'].includes(x.group));
 if(animal)return animal.group;
 const t=norm(recipe?.title);
 const titleAnimal=animalGroup(t);if(titleAnimal)return titleAnimal;
 if(/veggie|vegetarisch|vegan|plantaardig/.test(t))return 'vega';
 if(/kip(?:pen)?(?:bout|dij|filet|sate)|\bkip\b/.test(t))return 'kip';
 if(/zalm|kabeljauw|koolvis|pangasius|garnalen|\bvis\b/.test(t))return 'vis';
 if(/rund|gehakt|varken|hamburger|rookworst|hachee|rendang/.test(t))return 'vlees';
 return 'vega';
}
function isMain(p,recipe){return p?.group===group(recipe);}
const CUISINES=[
 ['italiaans','Italiaans','italian|italiaans'],['indiaas','Indiaas','indian|indiaas|indiase'],
 ['indonesisch','Indonesisch','indonesian|indonesisch'],['thais','Thais','thai|thais'],
 ['japans','Japans','japanese|japans'],['koreaans','Koreaans','korean|koreaans'],
 ['vietnamees','Vietnamees','vietnamese|vietnamees'],['chinees','Chinees','chinese|chinees'],
 ['mexicaans','Mexicaans','mexican|mexicaans'],['surinaams','Surinaams','surinamese|surinaams'],
 ['marokkaans','Marokkaans','moroccan|marokkaans'],['turks','Turks','turkish|turks'],
 ['grieks','Grieks','greek|grieks'],['spaans','Spaans','spanish|spaans'],
 ['frans','Frans','french|frans'],['nederlands','Nederlands','dutch|nederlands|nedeland|nedelandsk|hollands'],
 ['belgisch','Belgisch','belgian|belgisch|belgisk'],['amerikaans','Amerikaans','american|amerikaans'],
 ['midden-oosters','Midden-Oosters','middle east|middle eastern|midden oosters'],
 ['zuid-amerikaans','Zuid-Amerikaans','south american|zuid amerikaans'],
 ['mediterraan','Mediterraan','mediterranean|mediterraan'],['aziatisch','Aziatisch','asian|aziatisch'],
 ['europees','Europees','european|europese|europees'],['fusion','Fusion','fusion']
];
const CUISINE_PATTERNS=CUISINES.map(([key,label,terms])=>[key,new RegExp('\\b(?:'+terms+')(?:e)?\\b')]);
function cuisine(recipe){
 const explicit=norm(Array.isArray(recipe?.cuisine)?recipe.cuisine.join(' '):recipe?.cuisine);
 const text=explicit||norm(recipe?.title);
 return CUISINE_PATTERNS.find(([,pattern])=>pattern.test(text))?.[0]||'onbekend';
}
function containsLeek(recipe){return recipeProfiles(recipe).some(p=>p.family==='prei')||/\bprei/.test(norm((recipe?.title||'')+' '+(recipe?.ingredients||[]).map(x=>x.name).join(' ')));}
return {VERSION,norm,CUISINES,cuisine,containsLeek,isDeliChicken,displayCategory,profile,compatible,recipeProfiles,group,isMain,quantity};
});
