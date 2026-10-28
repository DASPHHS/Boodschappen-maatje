'use strict';
(function(){
const NAMES={lidl:'Lidl',jumbo:'Jumbo',ah:'Albert Heijn'};
const KINDS={kip:'Kip',vlees:'Vlees',vis:'Vis',vega:'Vega'};
const SYMBOLS={kip:'🍗',vlees:'🥩',vis:'🐟',vega:'🥦'};
const ORDER=['lidl','jumbo','ah'];
const DEPARTMENTS=['Groente & fruit','Eiwitbronnen','Vega & peulvruchten','Zuivel','Diepvries','Kruiden & voorraad','Overig'];
const $=s=>document.querySelector(s);
const money=x=>typeof x==='number'&&Number.isFinite(x)?new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'}).format(x):'Nog onbekend';
const safe=x=>String(x==null?'':x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const attr=safe;
const validdate=x=>typeof x==='string'&&/^\d{4}-\d\d-\d\d$/.test(x);
const today=()=>new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
const dateNL=x=>validdate(x)?new Date(x+'T12:00:00').toLocaleDateString('nl-NL',{day:'numeric',month:'short'}):'Onbekend';
const pick=(x,k)=>x&&typeof x==='object'?x[k]:undefined;
const state={view:'vandaag',store:'alle',kind:'alle',subtype:'alle',query:'',sortBy:'deals',dealFilter:'all',daily:null,weekly:null,archive:null,catalog:null,library:[],_offersCache:new Map(),_matchCache:new Map(),pageSize:{lidl:24,jumbo:24,ah:24},selected:read('bm_selected',{}),checks:read('bm_checks',{})};
function read(k,fallback){try{return JSON.parse(localStorage.getItem(k))||fallback}catch{return fallback}}
function save(){try{localStorage.setItem('bm_selected',JSON.stringify(state.selected));localStorage.setItem('bm_checks',JSON.stringify(state.checks))}catch{}}
async function load(path){try{const r=await fetch(path+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error(r.status);return await r.json()}catch{return null}}
function storeData(d,s){return (d&&d.stores&&d.stores[s])||{}}

function offers(s){
const key=s+'|'+today()+'|'+(state.catalog?.generated_at||'')+'|'+(state.daily?.generated_at||'');
if(state._offersCache.has(key))return state._offersCache.get(key);
const current=storeData(state.daily,s).offers||[];
const scan=state.catalog?.stores?.[s];
const fresh=state.catalog?.generated_at?.slice(0,10)===today()&&scan?.status==='ok';
const external=fresh&&Array.isArray(scan.offers)?scan.offers:[];
const ids=new Set(),all=[];
for(const o of [...current,...external])if(isOfferActive(o)&&!ids.has(o.id)){ids.add(o.id);all.push(o)}
state._offersCache.set(key,all);return all;
}
function isOfferActive(o){
if(!o||!Number.isFinite(o.price)||!validdate(o.end_date)||!validdate(o.start_date))return false;
if(o.start_date>today()||o.end_date<today()||o.online_only)return false;
return o.verified===true||(o.source_provider==='PrijsProfeet'&&o.promotion_status==='active');
}
function recipes(s){
const found=[],seen=new Set();
for(const [d,origin] of [[state.daily,'dagactie'],[state.weekly,'weekinspiratie'],[state.archive,'archief']]){
const list=origin==='archief'?(d?.stores?.[s]||[]):storeData(d,s).recipes;
if(!Array.isArray(list))continue;
for(const recipe of list){
if(!recipe?.id||seen.has(recipe.id))continue;seen.add(recipe.id);
found.push({...recipe,store:s,origin,...(origin==='archief'?{cost:null,price_status:'archief_verouderd'}:{})});
}}
for(const idea of (window.BoodschapRecipeEngine?.build(s,offers(s))||[])){
if(seen.has(idea.id))continue;seen.add(idea.id);found.push({...idea,store:s});
}
return found;
}
function catalog(s){
const newRecs=recipes(s);
const templates=state.library.map(r=>({...r,id:'library|'+r.id,store:s,origin:'bibliotheek',cost:null,macros:null}));
const used=new Set(newRecs.map(r=>r.title.toLocaleLowerCase('nl-NL').replace(/[^a-z0-9]/g,'')));
return newRecs.concat(templates.filter(r=>!used.has(r.title.toLocaleLowerCase('nl-NL').replace(/[^a-z0-9]/g,''))));
}
function norm(s){return String(s||'').toLocaleLowerCase('nl-NL').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ')}
function matchProduct(offer,ingredient){
const o=norm(offer.name),i=norm((ingredient.name||'')+' '+(ingredient.product_name||''));
const aliases=[
['broccoli',/broccoli/,/broccoli/],['prei',/\bprei\b/,/\bprei\b/],
['uien',/\buien\b/,/\buien\b|\bui\b/],['waspeen',/waspeen/,/wortel|winterpeen|waspeen/],
['zalm',/\bzalm/,/\bzalm/],['varkensoester',/varkensoester/,/varkensoester/],
['vegan spek',/vegan spek|plantaardige spek/,/vegan spek|plantaardige spek/],
['hutspot',/hutspot/,/hutspot/],['zuurkool',/zuurkool/,/zuurkool/],
['hummus',/hoemoes|hummus/,/hoemoes|hummus/],
['spruitjes',/spruitjes/,/spruitjes/],['bloemkool',/bloemkool/,/bloemkool/],
['varkensgehakt',/varkensgehakt/,/varkensgehakt/],
['plantaardige kip',/plantaardige kipstukjes/,/plantaardige kipstukjes/],
['flespompoen',/flespompoen/,/flespompoen|pompoen/],
['kiphaasjes',/kipfilethaasjes|kiphaasjes/,/kipfilethaasjes|kiphaasjes/]];
return aliases.some(([key,a,b])=>a.test(o)&&b.test(i));
}

function offerInfo(recipe,s){
const key=s+'|'+recipe.id+'|'+today();
if(state._matchCache.has(key))return state._matchCache.get(key);
const active=offers(s),confirmed=[],possible=[],usedIds=new Set();
for(const rel of (Array.isArray(recipe.offer_links)?recipe.offer_links:[])){
const offer=active.find(o=>o.id===rel.offer_id&&o.verified===true);
if(!offer||!rel.ingredient_name||rel.match_type!=='exact')continue;
const ing=recipe.ingredients.find(i=>norm(i.name)===norm(rel.ingredient_name));
if(ing?.price_status!=='folder_current')continue;
confirmed.push({offer,ingredient:ing});usedIds.add(offer.id);
}
const anchored=recipe.offer_anchor_id?active.find(o=>o.id===recipe.offer_anchor_id):null;
if(anchored)usedIds.add(anchored.id);
if(recipe.origin!=='actie-idee'){
for(const offer of active){
if(usedIds.has(offer.id))continue;
const ing=(recipe.ingredients||[]).find(i=>matchProduct(offer,i));
if(ing)possible.push({offer,ingredient:ing});
if(possible.length>=8)break;
}}
const result={confirmed,anchored,possible,total:confirmed.length+possible.length+(anchored?1:0)};
state._matchCache.set(key,result);return result;
}
function recipeSort(a,b){
const ca=offerInfo(a,a.store),cb=offerInfo(b,b.store);
const pa=a.cost?.basket_total,pb=b.cost?.basket_total,an=typeof pa==='number'&&Number.isFinite(pa)?pa:Infinity,bn=typeof pb==='number'&&Number.isFinite(pb)?pb:Infinity;
if(state.sortBy==='price')return an-bn||cb.confirmed.length-ca.confirmed.length||a.title.localeCompare(b.title,'nl');
if(state.sortBy==='protein')return (b.macros?.protein_g||-1)-(a.macros?.protein_g||-1)||an-bn;
if(state.sortBy==='time')return (a.minutes||999)-(b.minutes||999)||an-bn;
return cb.confirmed.length-ca.confirmed.length||Number(!!cb.anchored)-Number(!!ca.anchored)||cb.total-ca.total||an-bn||a.title.localeCompare(b.title,'nl');
}
function recipeFiltered(r){
if(state.kind!=='alle'&&r.category!==state.kind)return false;if(state.subtype!=='alle'&&proteinSubtype(r)!==state.subtype)return false;
if(state.query&&!(r.title+' '+(r.cuisine||'')+' '+(r.ingredients||[]).map(i=>i.name).join(' ')).toLocaleLowerCase('nl-NL').includes(state.query.toLocaleLowerCase('nl-NL')))return false;
const m=offerInfo(r,r.store);
if(state.dealFilter==='confirmed'&&!m.confirmed.length)return false;if(state.dealFilter==='anchor'&&!m.anchored)return false;
if(state.dealFilter==='potential'&&!m.possible.length)return false;
return true;
}
function storeRecipeCounts(s){return recipes(s).length}
function status(){const d=state.daily;const at=d?.generated_at;const date=at?String(at).slice(0,10):null;return !date?'Er is nog geen actuele scan':date<today()?'Laatste scan: '+date:'Actuele scan: '+date}
function storePill(s){return '<span class="store-mini">'+safe(NAMES[s]||'Algemene inspiratie')+'</span>'}
function priceQuality(r){const n=pick(r.cost,'basket_total');return typeof n==='number'?money(n):'Prijs nog niet bevestigd'}
function statusTag(r){const n=pick(r.cost,'basket_total');return typeof n!=='number'?'<span class="tag orange">Prijs onbekend</span>':r.cost.estimated?'<span class="tag orange">Prijsindicatie</span>':n<=10?'<span class="tag fresh">≤ € 10</span>':'<span class="tag orange">Boven € 10</span>'}
function storeLogo(s){return '<span class="store-dot '+s+'">'+(s==='lidl'?'L':s==='jumbo'?'J':'AH')+'</span>'}
function clearPage(){['vandaag','aanbiedingen','recepten','lijst'].forEach(v=>$('#view-'+v).classList.toggle('hidden',v!==state.view));document.querySelectorAll('[data-view]').forEach(el=>el.classList.toggle('active',el.dataset.view===state.view))}
function header(eyebrow,title,subtitle){$('#page-intro').innerHTML='<div class="eyebrow">'+safe(eyebrow)+'</div><h1>'+title+'</h1><p class="subhead">'+safe(subtitle)+'</p>'}
function title(t,sub,action){return '<div class="section-heading"><div><h2>'+safe(t)+'</h2>'+(sub?'<p>'+safe(sub)+'</p>':'')+'</div>'+(action||'')+'</div>'}
function storeControls(all=true){return '<div class="control-row store-filter">'+(all?'<button class="pill '+(state.store==='alle'?'active':'')+'" data-store="alle">Alle winkels</button>':'')+ORDER.map(s=>'<button class="pill '+(state.store===s?'active':'')+'" data-store="'+s+'">'+safe(NAMES[s])+'</button>').join('')+'</div>'}

function kindControls(offerPage=false){return '<div class="control-row">'+['alle','kip','vlees','vis','vega',...(offerPage?['groente']:[])].map(k=>'<button class="pill '+(state.kind===k?'active':'')+'" data-kind="'+k+'">'+(KINDS[k]||(k==='groente'?'Groente':'Alle soorten'))+'</button>').join('')+'<input class="search" id="find" aria-label="Zoek producten of recepten" placeholder="Zoek recept, keuken of ingrediënt…" value="'+attr(state.query)+'"></div>'}
function recipeControls(){return '<div class="recipe-toolbar"><label>Sorteer op <select id="recipe-sort"><option value="deals"'+(state.sortBy==='deals'?' selected':'')+'>Meeste acties eerst</option><option value="price"'+(state.sortBy==='price'?' selected':'')+'>Laagste kassaprijs</option><option value="protein"'+(state.sortBy==='protein'?' selected':'')+'>Meeste eiwit</option><option value="time"'+(state.sortBy==='time'?' selected':'')+'>Snelste bereiding</option></select></label><label>Actiestatus <select id="deal-filter"><option value="all"'+(state.dealFilter==='all'?' selected':'')+'>Alle recepten</option><option value="confirmed"'+(state.dealFilter==='confirmed'?' selected':'')+'>Actieprijs verwerkt</option><option value="anchor"'+(state.dealFilter==='anchor'?' selected':'')+'>Actie als hoofdingrediënt</option><option value="potential"'+(state.dealFilter==='potential'?' selected':'')+'>Past bij aanbieding</option></select></label></div>'}

function proteinSubtype(r){
const names=norm(r.title+' '+(r.ingredients||[]).map(i=>i.name||i.label||'').join(' '));
if(r.category==='vlees'){
if(/varken|varkens|hamlap|varkensoester/.test(names))return 'varken';
if(/rund|biefstuk|ossenhaas|rosbief/.test(names))return 'rund';
return 'ongespecificeerd';
}
if(r.category==='vis'){
if(/zalm|haring|sardine|makreel|forel/.test(names))return 'vet';
if(/koolvis|kabeljauw|schol|heek|pangasius|witvis|tilapia/.test(names))return 'mager';
return 'overig';
}
return 'alle';
}
function subtypeControls(){
const opts=state.kind==='vlees'?[['alle','Rund & varken'],['rund','Rund'],['varken','Varken'],['ongespecificeerd','Ander vlees']]:
state.kind==='vis'?[['alle','Alle vis'],['vet','Vette vis (omega 3)'],['mager','Magere vis'],['overig','Overige vis']]:[];
return opts.length?'<div class="control-row subtype-controls">'+opts.map(([k,v])=>'<button class="pill '+(state.subtype===k?'active':'')+'" data-subtype="'+k+'">'+v+'</button>').join('')+'</div>':'';
}
function featured(r){return '<div class="recipe-info"><span>4 porties</span><span>'+(Number(r.minutes)||'?')+' min</span><span>'+safe(KINDS[r.category]||'Maaltijd')+'</span></div>'}

function offerBadge(r){
const m=offerInfo(r,r.store);
if(m.confirmed.length)return '<span class="offer-badge confirmed">✓ '+m.confirmed.length+' actie'+(m.confirmed.length>1?'s':'')+' in prijs verwerkt</span>';
if(m.anchored)return '<span class="offer-badge anchor">★ Actie als basis · totaalprijs onbekend</span>';if(m.possible.length)return '<span class="offer-badge candidate">↗ '+m.possible.length+' mogelijke actie'+(m.possible.length>1?'s':'')+' · prijs niet doorgerekend</span>';
return '<span class="offer-badge neutral">Geen actie gekoppeld</span>';
}
function recipeCard(r){
const id=r.store+'|'+r.id,info=offerInfo(r,r.store),tip=info.confirmed.length?info.confirmed.map(x=>x.offer.name).join(' · '):info.anchored?'Actieproduct: '+info.anchored.name:info.possible.length?'Mogelijk: '+info.possible.slice(0,3).map(x=>x.offer.name).join(' · '):'';
return '<article class="recipe-card"><div class="recipe-visual '+(r.category==='kip'?'chicken':r.category==='vis'?'fish':r.category==='vlees'?'meat':'vega')+'">'+statusTag(r)+'<span class="plate" aria-hidden="true">'+(SYMBOLS[r.category]||'🥗')+'</span></div><div class="recipe-offers">'+offerBadge(r)+'</div><h3>'+safe(r.title)+'</h3><p>'+safe(r.cuisine||'Smakelijk & voedzaam')+' · '+safe(NAMES[r.store]||'')+'</p>'+featured(r)+(tip?'<p class="offer-hint">'+safe(tip)+'</p>':'')+'<div class="recipe-bottom"><div><b>'+priceQuality(r)+'</b><small>4 porties · '+(typeof r.cost?.basket_total==='number'?'indicatieve kassaprijs':'prijs nog te controleren')+(r.macros?' · '+safe(r.macros.protein_g)+' g eiwit/p':' · macro’s volgen')+'</small></div><button class="button small" data-open="'+attr(id)+'">Bekijk →</button></div></article>';
}

function dealCard(o,s){
const alt=o.cheapest_alternative;
const cheaper=alt&&Number.isFinite(alt.price)&&alt.price<o.price;
const independent=o.verified===true;
return '<article class="deal-card"><div class="deal-card-top"><div>'+storePill(s)+'<h3>'+safe(o.name||'Product')+'</h3></div><span class="tag '+(independent?'fresh':'orange')+'">'+(independent?'Actie gecontroleerd':'Via PrijsProfeet gemeld')+'</span></div><div class="price-line"><span class="price">'+money(o.price)+'</span>'+(typeof o.regular_price==='number'&&o.regular_price>o.price?'<span class="oldprice">'+money(o.regular_price)+'</span>':'')+'</div><div class="deal-meta">'+safe(o.pack_label||'Verpakking onbekend')+(o.unit_price?(' · '+money(o.unit_price)+'/'+safe(o.unit||'kg')):'')+' · geldig t/m '+dateNL(o.end_date)+(o.multi_buy_quantity?' · '+safe(o.multi_buy_quantity)+' voor '+money(o.multi_buy_price):'')+(o.member_required?' · klantenkaart nodig':'')+(o.loyalty_price?' · ledenprijs '+money(o.loyalty_price):'')+'</div>'+(cheaper?'<div class="deal-note bad">Een goedkoper passend product is gemeld: '+safe(alt.name)+' ('+money(alt.price)+'). Controleer de eenheid.</div>':alt?'<div class="deal-note">Alternatief: '+safe(alt.name)+' ('+money(alt.price)+').</div>':'<div class="deal-note">'+(independent?'Geen onafhankelijk vergelijkbare reguliere variant toegevoegd.':'Externe melding. Geen onafhankelijke winkelcontrole of bewijs van de laagste prijs.')+'</div>')+(o.source?.url?'<div class="deal-meta"><a href="'+attr(/^https:\/\//.test(o.source.url)?o.source.url:'#')+'" rel="noopener noreferrer" target="_blank">Prijsbron ↗</a></div>':'')+'</article>';
}
function empty(head,body){return '<div class="empty"><div class="empty-art">◌</div><strong>'+safe(head)+'</strong>'+safe(body)+'</div>'}
function overview(){
header('Jouw slimme boodschappenhulp','Wat eten we <span style="color:#719b66">deze week?</span>','Bekijk eerst alle drie de supermarkten. Kies straks zelf op basis van wat je lekker vindt.');
let x='<section class="hero"><div><div class="eyebrow" style="color:#c6e79b">GOED ETEN · SLIM KOPEN</div><h1>Meer smaak.<br><em>Minder uitgeven.</em></h1><p>Acties, nieuwe recepten en boodschappenlijsten per supermarkt. Altijd vier porties, genoeg voor twee dagen.</p></div><div class="hero-art" aria-hidden="true">✳</div></section>';
x+=title('Drie winkels, jouw keuze','Geen automatische winnaar. Bekijk per winkel wat er te koken valt.');
x+='<div class="store-grid">'+ORDER.map(s=>'<article class="store-card"><div class="store-top"><div class="store-logo">'+storeLogo(s)+safe(NAMES[s])+'</div><span class="tag">'+(storeRecipeCounts(s)?'Nieuwe recepten':'Prijscheck volgt')+'</span></div><p>'+ (storeRecipeCounts(s)?'Bekijk de nieuwe winkelrecepten en bijpassende acties.':'De eerste actuele winkelrapportage is nog niet beschikbaar.')+'</p><div class="store-metrics"><div class="metric"><b>'+offers(s).length+'</b><small>gecontroleerde deals</small></div><div class="metric"><b>'+storeRecipeCounts(s)+'</b><small>nieuwe recepten</small></div></div><button class="button full" data-goto-store="'+s+'">Bekijk '+safe(NAMES[s])+' →</button></article>').join('')+'</div>';

x+=title('Vandaag in de aanbieding','Alleen recepten die aantoonbaar een lopende aanbieding in hun gepubliceerde prijs bevatten.');
for(const store of ORDER){
let featured=recipes(store).filter(r=>offerInfo(r,store).confirmed.length).sort(recipeSort).slice(0,2);
x+=title(NAMES[store],featured.length+' recept(en) met bevestigde actie-ingrediënten','<button class="button secondary small" data-goto-store="'+store+'">Alle recepten →</button>');
x+=featured.length?'<div class="cards">'+featured.map(recipeCard).join('')+'</div>':empty('Nog geen actie-recept met geprijsd ingrediënt','Bekijk de gewone recepten of de losse aanbiedingen van '+NAMES[store]+'.');
}
x+='<div class="info-banner warning"><strong>Bronstatus:</strong> '+safe(status())+'. De app toont geen oude of onbevestigde aanbiedingen als actuele deal. Prijzen en macro’s verschijnen na de gecontroleerde publicatie.</div>';
$('#view-vandaag').innerHTML=x;
}
function offersView(){
header('Alle deals per supermarkt','Aanbiedingen die <span style="color:#719b66">echt tellen.</span>','Bekijk de deals van Lidl, Jumbo en Albert Heijn los van elkaar. Een actie is niet automatisch de voordeligste variant.');
let out=storeControls()+kindControls(true);
let any=false;
for(const s of ORDER.filter(s=>state.store==='alle'||state.store===s)){
const arr=offers(s).filter(o=>(state.kind==='alle'||o.category===state.kind)&&(!state.query||(o.name||'').toLowerCase().includes(state.query.toLowerCase()))).sort((a,b)=>a.price-b.price);
if(arr.length)any=true;
out+=title(NAMES[s],arr.length+' gecontroleerde aanbiedingen met geldige actieperiode');
out+=arr.length?'<div class="cards">'+arr.slice(0,state.pageSize[s]).map(o=>dealCard(o,s)).join('')+'</div>':empty('Nog geen actuele aanbiedingen voor '+NAMES[s],'De acties verschijnen zodra de nieuwe scan beschikbaar is.');if(arr.length>state.pageSize[s])out+='<div class="control-row"><button class="button secondary" data-more-offers="'+s+'">Nog 24 aanbiedingen laden ('+(arr.length-state.pageSize[s])+' resterend) →</button></div>';
}
out+='<div class="info-banner">We tonen alleen aanbiedingen met bevestigde prijs én lopende geldigheid. Een actie bij een andere winkel is geen reden om een extra winkel te bezoeken.</div>';
$('#view-aanbiedingen').innerHTML=out;
}
function allRecipes(){let found=ORDER.filter(s=>state.store==='alle'||state.store===s).flatMap(s=>recipes(s));let known=new Set(found.map(r=>r.title?.toLowerCase()));let suggestions=state.library.filter(r=>!known.has(r.title?.toLowerCase())).map(r=>({...r,store:null,origin:'bibliotheek'}));return found.concat(suggestions)}

function recipeView(){
header('Recepten & slimme acties','Lekker koken.<br><span style="color:#719b66">Acties die je écht gebruikt.</span>','Per supermarkt minstens tien recepten per categorie als inspiratie en dagelijkse actiegerichte gerechten zodra ze gecontroleerd zijn. Alleen bevestigde koppelingen tellen als actie in de prijs.');
let out=storeControls()+kindControls()+subtypeControls()+recipeControls();
for(const s of ORDER.filter(s=>state.store==='alle'||state.store===s)){
const all=catalog(s),found=all.filter(recipeFiltered).sort(recipeSort);
const current=all.filter(r=>offerInfo(r,s).confirmed.length).length;const anchored=all.filter(r=>offerInfo(r,s).anchored).length;
const potential=all.filter(r=>offerInfo(r,s).possible.length).length;
const counts=['kip','vlees','vis','vega'].map(k=>(KINDS[k]+' '+all.filter(r=>r.category===k).length)).join(' · ');
out+=title(NAMES[s]+' recepten',counts+' · '+current+' met actieprijs verwerkt · '+anchored+' actiegerichte ideeën · '+potential+' met mogelijke actie');
out+='<div class="info-banner">De recepten zonder actuele winkelprijs zijn inspiratie. Hun overeenkomsten met folderproducten zijn alleen suggesties, geen berekende besparing. '+(s==='jumbo'?'Op dit moment zijn er in de Jumbo-bron vooral plantaardige aanbiedingen; vlees- en visgerechten hoeven dus niet op een actie te steunen.':'')+'</div>';
out+=found.length?'<div class="cards">'+found.map(recipeCard).join('')+'</div>':empty('Geen recepten voor deze filters','Wijzig je actiestatus of zoekterm om meer recepten te zien.');
}
out+='<div class="info-banner warning">De receptenbibliotheek groeit met nieuwe dagelijkse en wekelijkse gerechten. Historische prijzen worden niet als actuele prijzen getoond. De goedkoopste werkelijke kassamand kan pas worden bevestigd als álle productprijzen en verpakkingen gecontroleerd zijn.</div>';
$('#view-recepten').innerHTML=out;
}
function normalize(r){return (r.ingredients||[]).map(i=>({name:i.name||i.label||'Ingrediënt',quantity:Number(i.quantity||0),unit:i.unit||'',department:i.department||'Overig',price:typeof i.pack_price==='number'?i.pack_price:null}));}
function currentSelections(s){const ids=state.selected[s]||[];return ids.map(id=>findRecipe(s,id)).filter(Boolean)}
function findRecipe(s,id){if(id.startsWith('library|'))return state.library.find(r=>r.id===id.slice(8));return recipes(s).find(r=>r.id===id)}
function shoppingView(){
header('Alles in één winkel','Jouw <span style="color:#719b66">boodschappenlijst.</span>','Jij kiest welke supermarkt je bezoekt. Combineer gerechten en vink je boodschappen in de winkel af.');
let s=state.store==='alle'?null:state.store;
let x=storeControls(false);
if(!s){x+=empty('Kies eerst je supermarkt','Selecteer Lidl, Jumbo of Albert Heijn. Je lijst blijft per winkel apart bewaard.');$('#view-lijst').innerHTML=x;return}
const picks=currentSelections(s);x+='<div class="info-banner">Je hebt '+picks.length+' '+(picks.length===1?'recept':'recepten')+' geselecteerd voor '+safe(NAMES[s])+'. We combineren gelijke ingrediënten. Winkelprijzen zonder verpakkingcontrole worden niet opgeteld.</div>';
if(!picks.length){x+=empty('Nog geen recepten gekozen','Ga naar Recepten, filter op '+NAMES[s]+' en voeg je favorieten toe aan de lijst.');x+='<button class="button" data-view="recepten">Ontdek recepten →</button>';$('#view-lijst').innerHTML=x;return}
x+=title('Geselecteerde gerechten','Klik op verwijderen om je lijst aan te passen.');
x+='<div class="control-row">'+picks.map(r=>'<span class="pill">'+safe(r.title)+' <button class="button ghost small" data-remove="'+attr(r.id)+'" title="Verwijderen uit je lijst">×</button></span>').join('')+'</div>';
const ing=new Map();for(const r of picks){for(const i of normalize(r)){let k=i.name.toLowerCase()+'|'+i.unit;let cur=ing.get(k);if(cur)cur.quantity+=i.quantity;else ing.set(k,{...i,key:k})}}
const groups={};[...ing.values()].forEach(i=>(groups[i.department]??=[]).push(i));
x+=title('Pak dit in de winkel','Hoeveelheden zijn totaalverbruik voor de gekozen gerechten. Verpakkingsadvies volgt zodra prijzen zijn geverifieerd.');
for(const dep of [...DEPARTMENTS,...Object.keys(groups).filter(x=>!DEPARTMENTS.includes(x))]){if(!groups[dep])continue;x+='<div class="list-group"><h3>'+safe(dep)+'</h3>'+groups[dep].map(i=>{let key=s+'|'+i.key;return '<label class="list-line"><input type="checkbox" data-check="'+attr(key)+'" '+(state.checks[key]?'checked':'')+'><span class="item-name '+(state.checks[key]?'done':'')+'">'+safe(i.name)+'</span><span class="item-qty">'+safe(Math.round(i.quantity*100)/100)+' '+safe(i.unit)+'</span></label>'}).join('')+'</div>'}
x+='<div class="control-row"><button class="button secondary" data-copy-list="'+s+'">Kopieer boodschappenlijst</button><button class="button ghost" data-reset-checks="'+s+'">Vinkjes wissen</button></div>';
$('#view-lijst').innerHTML=x;
}

function openRecipe(key){
const [s,...idparts]=key.split('|'),id=idparts.join('|'); const r=findRecipe(s,id);if(!r)return;
const list=normalize(r),steps=Array.isArray(r.instructions)?r.instructions:typeof r.instructions==='string'?r.instructions.split(/[.;]\s+/):[];
const matched=offerInfo(r,s),m=r.macros;
let x='<div class="eyebrow">'+safe(KINDS[r.category]||'Recept')+' · '+safe(NAMES[s])+'</div><h2>'+safe(r.title)+'</h2><p class="subhead">'+safe(r.cuisine||'')+' · 4 porties · '+(Number(r.minutes)||'?')+' minuten</p>';
x+='<div class="dialog-offer-section">'+offerBadge(r);
if(matched.confirmed.length){x+='<p class="dialog-note">De volgende geldige actieproducten zijn daadwerkelijk in de ingrediënten en de prijsberekening verwerkt:</p>';
for(const item of matched.confirmed){const o=item.offer;x+='<div class="offer-detail"><strong>'+safe(o.name)+'</strong> · '+money(o.price)+' per '+safe(o.pack_label||'verpakking')+' · gebruikt voor '+safe(item.ingredient.name)+(o.member_required?' · klantenkaart nodig':'')+' · t/m '+dateNL(o.end_date)+(o.source?.url?'<br><a href="'+attr(o.source.url)+'" target="_blank" rel="noopener noreferrer">Controleer deze aanbieding ↗</a>':'')+'</div>';}
}
if(matched.anchored){const o=matched.anchored;x+='<p class="dialog-note"><strong>Actie als basis:</strong> dit hoofdproduct is in de actiescan gezien, maar de volledige kassaprijs van het gerecht is onbekend. '+(o.verified?'Actiebron gecontroleerd.':'Externe prijswaarneming, niet onafhankelijk bevestigd.')+'</p><div class="offer-detail"><strong>'+safe(o.name)+'</strong> · '+money(o.price)+' per '+safe(o.pack_label||'verpakking')+' · t/m '+dateNL(o.end_date)+(o.multi_buy_quantity?' · bundel '+safe(o.multi_buy_quantity)+' voor '+money(o.multi_buy_price):'')+(o.loyalty_price?' · ledenprijs '+money(o.loyalty_price):'')+(o.source?.url?'<br><a target="_blank" rel="noopener noreferrer" href="'+attr(o.source.url)+'">Bekijk bron ↗</a>':'')+'</div>';}if(matched.possible.length){x+='<p class="dialog-note"><strong>Wel mogelijk, niet verrekend:</strong> deze aanbiedingen kunnen mogelijk bij een ingrediënt passen. Productvorm, gewicht en kassaprijs moeten nog worden gecontroleerd.</p><ul class="ingredients">'+matched.possible.map(item=>'<li>'+safe(item.offer.name)+' ('+money(item.offer.price)+' / '+safe(item.offer.pack_label||'verpakking')+')'+(item.offer.source?.url?' <a href="'+attr(item.offer.source.url)+'" rel="noopener noreferrer" target="_blank">Bron ↗</a>':'')+'</li>').join('')+'</ul>'}
if(!matched.total)x+='<p class="dialog-note">Geen actuele aanbieding aan deze ingrediënten gekoppeld.</p>';
x+='</div>';
x+='<div class="summary-tiles"><div class="summary-tile"><b>'+priceQuality(r)+'</b><span>'+(typeof r.cost?.basket_total==='number'?'KASSAPRIJSINDICATIE':'KASSAPRIJS ONBEKEND')+'</span></div><div class="summary-tile"><b>'+(m&&Number.isFinite(Number(m.protein_g))?m.protein_g+' g':'—')+'</b><span>EIWIT / PORTIE</span></div><div class="summary-tile"><b>'+(m&&Number.isFinite(Number(m.carbs_g))?m.carbs_g+' g':'—')+'</b><span>KOOLHYDRATEN / PORTIE</span></div></div>';
if(r.category==='vis')x+='<div class="info-banner">Tip: varieer met vissoorten. Zalm, haring en forel leveren omega 3; magere witvis levert vooral eiwit. Bron: <a href="https://www.voedingscentrum.nl/encyclopedie/vis" target="_blank" rel="noopener noreferrer">Voedingscentrum ↗</a>.</div>';if(m)x+='<p class="muted">Voedingswaarden per portie: '+safe(m.kcal)+' kcal, '+safe(m.protein_g)+' g eiwit, '+safe(m.carbs_g)+' g koolhydraten, '+safe(m.fat_g)+' g vet. '+(r.macro_status==='verified'?'Berekend':'Schatting')+'.</p>';
x+='<h3 style="margin-top:20px">Ingrediënten voor 4 porties</h3><ul class="ingredients">'+list.map((i,k)=>{const raw=r.ingredients[k];return '<li>'+safe(i.quantity)+' '+safe(i.unit)+' '+safe(i.name)+(typeof raw.pack_price==='number'?'<span class="muted"> · verpakkingen '+money(raw.pack_price)+(raw.price_observed_at?' · peildatum '+safe(raw.price_observed_at):'')+'</span>':' · <span class="muted">prijs onbekend</span>')+'</li>'}).join('')+'</ul>';
x+='<h3 style="margin-top:20px">Zo maak je het</h3><ol class="steps">'+steps.map(t=>'<li>'+safe(t)+'</li>').join('')+'</ol>';
x+='<div class="info-banner warning">'+(typeof r.cost?.basket_total==='number'?'Dit bedrag is gebaseerd op de gepubliceerde prijswaarnemingen; de volledige kassamand is '+(r.cost.verified_today?'die dag gecontroleerd.':'niet op dezelfde dag geverifieerd.')+' '+safe(r.cost.price_basis||''):'Voor dit bibliotheekrecept zijn nog niet alle vierportiehoeveelheden, actuele verpakkingsprijzen en macro’s gecontroleerd. Er is geen betrouwbare actuele kassaprijs.')+'</div>';
x+='<div class="dialog-actions"><button class="button" data-add="'+attr(s+'|'+id)+'">Voeg toe aan '+safe(NAMES[s])+'-lijst</button></div>';
$('#dialog-content').innerHTML=x;$('#recipe-dialog').showModal();
}
function setView(v){if(!['vandaag','aanbiedingen','recepten','lijst'].includes(v))return;state.view=v;state.kind='alle';state.subtype='alle';state.query='';history.replaceState(null,'','#'+v);render();window.scrollTo(0,0)}
function render(){clearPage();if(state.view==='vandaag')overview();if(state.view==='aanbiedingen')offersView();if(state.view==='recepten')recipeView();if(state.view==='lijst')shoppingView();let total=Object.values(state.selected).reduce((x,y)=>x+(y?.length||0),0);$('#nav-count').textContent=total||'';const st=$('#feed-status');st.textContent=status()+(state.catalog?.generated_at?' · actiescan '+String(state.catalog.generated_at).slice(0,10):'');st.classList.toggle('warn',!state.daily?.generated_at||String(state.daily.generated_at).slice(0,10)<today())}
function copyList(s){const picks=currentSelections(s);let m=new Map();picks.forEach(r=>normalize(r).forEach(i=>{let k=i.name+'|'+i.unit;let old=m.get(k);if(!old){old={...i,quantity:0};m.set(k,old)}old.quantity+=i.quantity;m.set(k,old)}));let txt='Boodschappenmaatje · '+NAMES[s]+'\n'+picks.map(x=>'• '+x.title).join('\n')+'\n\n'+[...m.values()].map(i=>'☐ '+i.quantity+' '+i.unit+' '+i.name).join('\n');navigator.clipboard?.writeText(txt).then(()=>alert('Boodschappenlijst gekopieerd.')).catch(()=>alert(txt))}
document.addEventListener('click',e=>{const b=e.target.closest('button,a[data-view]');if(!b)return;
if(b.dataset.view){e.preventDefault();setView(b.dataset.view);return}
if(b.dataset.moreOffers){state.pageSize[b.dataset.moreOffers]+=24;offersView();return}if(b.dataset.gotoStore){state.store=b.dataset.gotoStore;setView('recepten');return}
if(b.dataset.store){state.store=b.dataset.store;render();return}
if(b.dataset.kind){state.kind=b.dataset.kind;state.subtype='alle';render();return}if(b.dataset.subtype){state.subtype=b.dataset.subtype;render();return}
if(b.dataset.open){openRecipe(b.dataset.open);return}
if(b.dataset.add){let parts=b.dataset.add.split('|');let s=parts[0],id=parts.slice(1).join('|');state.selected[s]??=[];if(!state.selected[s].includes(id))state.selected[s].push(id);save();$('#recipe-dialog').close();state.store=s;setView('lijst');return}
if(b.dataset.remove){let s=state.store;state.selected[s]=(state.selected[s]||[]).filter(k=>k!==b.dataset.remove);save();render();return}
if(b.dataset.copyList){copyList(b.dataset.copyList);return}
if(b.dataset.resetChecks){Object.keys(state.checks).filter(x=>x.startsWith(b.dataset.resetChecks+'|')).forEach(k=>delete state.checks[k]);save();render();return}
});
document.addEventListener('input',e=>{if(e.target.id==='find'){let x=e.target.value;state.query=x;let pos=e.target.selectionStart;state.view==='recepten'?recipeView():offersView();let inp=$('#find');inp.focus();inp.setSelectionRange(pos,pos)}});
document.addEventListener('change',e=>{if(e.target.id==='recipe-sort'){state.sortBy=e.target.value;recipeView();return}if(e.target.id==='deal-filter'){state.dealFilter=e.target.value;recipeView();return}if(e.target.matches('[data-check]')){state.checks[e.target.dataset.check]=e.target.checked;save();e.target.closest('.list-line').querySelector('.item-name').classList.toggle('done',e.target.checked)}});
$('#dialog-close').addEventListener('click',()=>$('#recipe-dialog').close());
document.querySelector('#clock').textContent=new Date().toLocaleDateString('nl-NL',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Amsterdam'});
(async()=>{const res=await Promise.all([load('data/daily.json'),load('data/weekly.json'),load('data/library.json'),load('data/archive.json'),load('data/offers-catalog.json')]);state.daily=res[0];state.weekly=res[1];state.library=Array.isArray(res[2]?.recipes)?res[2].recipes:[];state.archive=res[3];state.catalog=res[4];state._offersCache.clear();state._matchCache.clear();state.view=['vandaag','aanbiedingen','recepten','lijst'].includes(location.hash.slice(1))?location.hash.slice(1):'vandaag';render()})();
})();
