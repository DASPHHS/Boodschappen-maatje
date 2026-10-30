/* Shared product eligibility policy. Keyword retrieval is never a match decision.
 * Classify audience, family, preparation and measurement separately; unknown
 * descriptions go to evidence review rather than a cheapest-product claim. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.MaatjeSemantics=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const VERSION='2026-10-30.1';
const norm=x=>String(x||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
const word=(s,t)=>(' '+s+' ').includes(' '+t+' ');
// Families are reusable product concepts, not retailer SKU exceptions.
const definitions=[
 ['chicken_breast','Kipfilet',['kipfilet','kipfiletblokjes','kipfiletreepjes','kipfilethaasjes','scharrelkipfilethaasjes']],
 ['chicken_leg','Kippenbouten',['kippenbouten','kippenpoten','kipbouten','drumsticks']],
 ['mince','Gehakt',['gehakt','rundergehakt','varkensgehakt','kipgehakt']],
 ['salmon','Zalm',['zalm','zalmfilet']],['trout','Forel',['forel']],['mackerel','Makreel',['makreel']],
 ['cod','Kabeljauw',['kabeljauw','kabeljauwfilet']],['pollock','Koolvis',['koolvis','koolvisfilet']],['herring','Haring',['haring','haringfilet']],
 ['pumpkin','Pompoen',['pompoen','flespompoen']],['green_beans','Sperziebonen',['sperziebonen']],
 ['carrot','Wortel',['bospeen','wortel','wortelen','wortels','winterpeen','waspeen']],
 ['broccoli','Broccoli',['broccoli']],['cauliflower','Bloemkool',['bloemkool']],['courgette','Courgette',['courgette']],
 ['paprika','Paprika',['paprika']],['tomato','Tomaat',['tomaat','tomaten']],['garlic','Knoflook',['knoflook']],
 ['lemongrass','Citroengras',['sereh','citroengras','lemongrass']],['almonds','Amandelen',['amandelen']],['walnuts','Walnoten',['walnoten']],
 ['peanut_butter','Pindakaas',['pindakaas']],['quark','Kwark',['kwark','fransekwark']],['milk','Melk',['melk']],['eggs','Eieren',['eieren']],
 ['tofu','Tofu',['tofu']],['tempeh','Tempeh',['tempeh','tempe']],['popcorn','Popcorn',['popcorn']],
 ['beer','Bier',['bier','skuumkoppe']],['dishwasher','Vaatwastabletten',['vaatwastabletten','vaatwascapsules','vaatwaspods']],
 ['boemboe','Boemboe',['boemboe']]
];
const fish=new Set(['salmon','trout','mackerel','cod','pollock','herring']);
const plain=new Set(['chicken_breast','chicken_leg','mince',...fish,'pumpkin','green_beans','carrot','broccoli','cauliflower','courgette','paprika','tomato','garlic','lemongrass','almonds','walnuts','tofu','tempeh']);
const labels=Object.fromEntries(definitions.map(d=>[d[0],d[1]]));
const brands=new Set(norm('ah jumbo lidl albert heijn verstegen kania ducros lassie conimex koh thai go tan al fez phare du cap bon lezziz milbona goldessa freshona vemondo golden seafood polenghi lemondor sebahat mill mortar zakje pot fles gemalen mild milde light fijn fijne grof grove romig romige glutenvrij volkoren zonder met huid biologisch biologische bio terra de zaanse hoeve vers verse extra fijne fijn gesneden diepvries naturel verse rauwe rauw zonder vel huid grootverpakking voordeelverpakking xxl verpakking per stuk stuks st g kg ml cl l x').split(' '));
function families(name){return definitions.filter(d=>d[2].some(t=>word(name,t))).map(d=>d[0]);}
function classify(product){
 const name=norm(product?.name),pack=norm(product?.pack_label),n=name+' '+pack;
 const meta=product?.semantic_evidence?.verified_identity===true?product.semantic_evidence:null;
 const category=norm(meta?.categories?.join(' ')||'');
 const combined=n+' '+category;
 let audience=/\b(kat|katten|kattenvoer|kattenvoeding|hond|honden|hondenvoer|hondenvoeding|diervoeder|dierenvoeding|petfood|catfood|dogfood|cat food|dog food|pet food|puppy|kitten|whiskas|felix|sheba|brokjes|brokken)\b/.test(combined)?'pet':
  /\b(baby|babyvoeding|babymelk|babymaaltijd|groentehapje|groentehapjes|knijpfruit|olvarit|kleintje|dreumes|peuter|maanden|months|infant)\b/.test(combined)?'baby':
  /\b(zeep|shampoo|deodorant|roomspray|schoonmaak|vaatwas|vaatwastabletten|vaatwascapsules|vaatwaspods|afwasmiddel|wasmiddel|wasverzachter|toiletreiniger)\b/.test(combined)?'household':'human';
 const matches=families(name),structured=families(category);
 const family=matches[0]||structured[0]||null;
 const preparationText=n+(plain.has(family)?' '+category:'');
 let form=/\b(gerookt|gerookte|rookvlees)\b/.test(preparationText)?'smoked':
  /\b(gegrild|gegrilde|gebakken|gebraden|gegaard|gekookt|gekookte|vleeswaren|broodbeleg|plakjes|plakken)\b/.test(preparationText)?'cooked':
  /\b(gemarineerd|gemarineerde|gekruid|gekruide|american(os|o)|tandoori|barbecue|bbq)\b/.test(preparationText)?'seasoned':
  /\b(gepaneerd|gepaneerde|gepan|battered)\b/.test(preparationText)?'breaded':
  /\b(blik|conserven|uitlekgewicht|uitgelekt|pot|potje|jar|canned)\b/.test(preparationText)||/\bhak\b/.test(preparationText)?'preserved':
  /\b(poeder|gemalen|gedroogd|gedroogde|kruidenmix)\b/.test(preparationText)?'powder':
  /\b(diepvries|bevroren|dv|frozen)\b/.test(preparationText)?'frozen':'plain';
 // Compound words matter: pureersoep and pepersaus are not plain produce/meat.
 const dish=/(?:soep|soup|saus|sauce|salade|salademix|groentemix|groentehap|knijpfruit|smoothie|maaltijd|schotel|pizza|burger|schnitzel|nugget|kroket|crouton|pate|wrap|taart|cake|koek(?:jes|en)?|biscuit|crackers?|chips|puree|stamp(pot)?|tapenade|hoemoes|hummus|smeerkaas|mueslireep|repen|brood)\b/.test(n);
 if(dish&&family!=='boemboe'&&audience==='human')form='prepared';
 if(plain.has(family)&&matches.filter(f=>plain.has(f)).length>1)form='mixed';
 if(family==='green_beans'&&/\b\d+\s*ml\b/.test(pack))form='preserved';
 const plant=/\b(plantaardig|plantaardige|vegan|vegetarisch|vegetarische|vega|redefine)\b/.test(n);
 const variant=family==='mince'?/\b(gemengd|half om half)\b/.test(n)?'gemengd':/rundergehakt/.test(n)?'rund':/varkensgehakt/.test(n)?'varken':'onbekend':
  family==='tofu'?/\b(zacht|zachte|silken|zijde|zijden)\b/.test(n)?'zacht':'naturel':
  family==='popcorn'?/\b(mais|maiskorrels|pofmais)\b/.test(n)?'pofmais':/\b(magnetron|microwave)\b/.test(n)?'magnetron':'gepofte popcorn':
  family==='beer'?/\b(0 0|alcoholvrij)\b/.test(n)?'alcoholvrij':'alcoholhoudend':
  family==='milk'?/\b(houdbaar|houdbare|uht|langlekker)\b/.test(n)?'houdbaar':'vers of niet gespecificeerd':'';
 const flavor=['vanille','aardbei','chocolade','karamel','banaan','bosvruchten'].find(t=>word(name,t))||'naturel';
 const attributes={flavor,...(['almonds','walnuts'].includes(family)?{roast:/\b(ongebrand|ongebrande)\b/.test(n)?'ongebrand':/\b(gebrand|gebrande|geroosterd|geroosterde)\b/.test(n)?'geroosterd':'bereiding niet vermeld',salt:/\bongezouten\b/.test(n)?'ongezouten':/\bgezouten\b/.test(n)?'gezouten':'zout niet vermeld'}:{}),...(family==='peanut_butter'?{recipe:/\b100\b/.test(name)?'100% pindas':'regulier'}:{}),...(family==='beer'?{container:/\b(blik|blikjes|blikken)\b/.test(name)?'blik':/\b(fles|flesjes|flessen)\b/.test(name)?'fles':'verpakking niet bevestigd'}:{})};
 return {family,families:matches,audience,form,plant,variant,name,meta:!!meta&&structured.includes(family),attributes};
}
function intent(profile){
 const q=norm([profile?.title, ...(profile?.match?.all||[]),...(profile?.match?.any||[])].join(' '));
 const explicit=profile?.semantics||{};
 const family=explicit.families||families(q);
 const expectedAudience=explicit.audience||(/\b(katten|kattenvoer|honden|hondenvoer|puppy|kitten)\b/.test(q)?'pet':/\b(baby|babyvoeding|olvarit)\b/.test(q)?'baby':family.includes('dishwasher')?'household':'human');
 let forms=explicit.forms;
 if(!forms&&family.length&&!family.includes('boemboe')&&!family.includes('dishwasher'))forms=/\b(gerookt|gerookte)\b/.test(q)?['smoked']:/\b(blik|pot|conserven)\b/.test(q)?['preserved']:/\b(poeder|gemalen)\b/.test(q)?['powder']:['plain','frozen'];
 return {families:family,audience:expectedAudience,forms,query:q};
}
const descriptors=new Set(norm('vers verse rauw rauwe onbewerkt naturel biologische biologisch bio scharrel halal beter leven bl xxl grootverpakking voordeelverpakking kleinverpakking voordeel verpakking blokken blokjes reepjes roosjes heel hele gebroken gesneden fijn fijngesneden fijne grof grove zacht zachte stevig stevige zijde zijden silken firm gerookt gerookte gekruid gekruide gemalen poeder diepvries bevroren dv alaska wilde wild noorse atlantische porties asc msc ggn filet filets zonder met huid vel z h hu zon ongebrand ongebrande ongezouten gezouten geroosterd geroosterde wit witte rood rode groen groene geel gele mager magere franse proteine protein high procent vet light romig romige volle vol halfvol halfvolle houdbaar houdbare uht langlekker melk koemelk vollemelk houdbaarheid net zak zakje bos stronk stronken stengel stengels pot fles blik blikjes flesjes flessen blikken boerderij gemengd half om rund rundvlees varken varkensvlees pindas pinda s stukjes crunchy smooth naturel calve ah jumbo lidl albert heijn de zaanse hoeve milbona freshona golden seafood vemondo vivera bio organic texels mais maiskorrels pofmais magnetron microwave platinum plus all in one dreft vaatwas citroen lemon diep deep clean capsules original kg g ml cl l stuks stuk st bos x gram liter kilogram s m xl').split(' '));
function unexplained(actual,profile,product){
 const own=definitions.find(d=>d[0]===actual.family)?.[2]||[];
 const brand=product?.semantic_evidence?.verified_identity===true?norm(product.semantic_evidence.brand):'';
 const allowed=new Set([...brands,...descriptors,...brand.split(' '),...own.flatMap(norm).flatMap(x=>x.split(' ')),...(profile?.match?.all||[]).flatMap(x=>norm(x).split(' '))]);
 return actual.name.split(' ').filter(t=>!allowed.has(t)&&!/^\d+(?:g|kg|ml|cl|l|st|stk|stuks)?$/.test(t));
}
function evaluate(product,profile,pricing){
 const actual=classify(product),expected=intent(profile);
 const result=(status,reason)=>({status,reason,policy_version:VERSION,actual,expected});
 if(actual.audience!==expected.audience)return result('reject','andere doelgroep: '+actual.audience);
 if(expected.families.length&&(!actual.family||!expected.families.includes(actual.family)))return result('partial','productsoort niet voldoende bevestigd');
 if(actual.plant&&expected.families.some(f=>fish.has(f)||['chicken_breast','chicken_leg','mince'].includes(f)))return result('reject','plantaardige variant in vlees/visvergelijking');
 if(expected.forms&&!expected.forms.includes(actual.form))return result('reject','andere productvorm: '+actual.form);
 if(actual.family&&unexplained(actual,profile,product).length)return result('partial','niet herkende productbeschrijving: '+unexplained(actual,profile,product).join(' '));
 if(!actual.family){
  // Future/custom queries are accepted only as literal, unambiguous product heads.
  const requested=(profile?.match?.all||[]).map(norm).filter(Boolean);
  const remaining=actual.name.split(' ').filter(t=>!brands.has(t)&&!/^\d+(g|kg|ml|cl|l)?$/.test(t));
  if(!requested.length||remaining.join(' ')!==requested.join(' '))return result('partial','onbekende productsoort; extra broninformatie nodig');
 }
 const categories=norm(product?.semantic_evidence?.verified_identity===true?product.semantic_evidence.categories?.join(' '):'');
 if(actual.family==='green_beans'&&actual.form==='plain'&&!/\b(vers|verse|rauw|rauwe)\b/.test(actual.name)&&!/(aardappelen.*groente.*fruit|verse groente|fresh vegetables)/.test(categories))return result('partial','vers/diepvries of conserven niet uit productbron vastgesteld');
 const p=pricing?.pack?.(product);
 if(plain.has(actual.family)&&p&&p.unit==='L')return result('reject','volume is geen vergelijkbaar eetbaar gewicht');
 const basis=p&&!p.approximate?p.unit:'inhoud onbekend';
 const detail=Object.values(actual.attributes).join(' · ');
 const key=[actual.family||'literal:'+norm((profile?.match?.all||[]).join(' ')),actual.form,actual.variant,detail,basis].join('|');
 const formLabel={plain:'naturel; bewaarmethode niet vermeld',frozen:'diepvries',smoked:'gerookt',preserved:'conserven',powder:'poeder',cooked:'bereid',seasoned:'gekruid',prepared:'bereid gerecht',mixed:'mengsel'}[actual.form]||actual.form;
 return {...result('match','productsoort, doelgroep en vorm passend'),comparison_key:key,
  comparison_label:[labels[actual.family]||actual.name,actual.variant,detail==='naturel'?'':detail,plain.has(actual.family)?formLabel:'',basis==='inhoud onbekend'?'inhoud niet bevestigd':'per '+basis].filter(Boolean).join(' · '),
  comparable:!!p&&!p.approximate};
}
return {VERSION,norm,classify,intent,evaluate};
});
