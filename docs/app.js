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
const state={view:'vandaag',store:'alle',kind:'alle',subtype:'alle',query:'',sortBy:'deals',recipeQuality:'developed',dealFilter:'all',offerSort:'relevant',offerEvidence:'all',daily:null,weekly:null,archive:null,catalog:null,spotlight:null,watchlist:null,personalPrices:null,verification:null,supplemental:null,audit:null,library:[],offerMode:'personal',manageWatch:false,favorites:read('bm_product_favorites',[]),watchDisabled:read('bm_watch_disabled',[]),_offersCache:new Map(),_matchCache:new Map(),pageSize:{lidl:24,jumbo:24,ah:24},selected:read('bm_selected',{}),checks:read('bm_checks',{}),savedRecipes:read('bm_saved_recipes',[]),recipeSnapshots:read('bm_recipe_snapshots',{})};
function read(k,fallback){try{return JSON.parse(localStorage.getItem(k))||fallback}catch{return fallback}}
function save(){try{localStorage.setItem('bm_selected',JSON.stringify(state.selected));localStorage.setItem('bm_checks',JSON.stringify(state.checks));localStorage.setItem('bm_watch_disabled',JSON.stringify(state.watchDisabled));localStorage.setItem('bm_product_favorites',JSON.stringify(state.favorites));localStorage.setItem('bm_saved_recipes',JSON.stringify(state.savedRecipes));localStorage.setItem('bm_recipe_snapshots',JSON.stringify(state.recipeSnapshots))}catch{}}
async function load(path){try{const r=await fetch(path+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error(r.status);return await r.json()}catch{return null}}
function storeData(d,s){return (d&&d.stores&&d.stores[s])||{}}


function offers(s){
 const key=s+'|'+today()+'|'+(state.catalog?.generated_at||'')+'|'+(state.supplemental?.generated_at||'')+'|'+(state.daily?.generated_at||'');
 if(state._offersCache.has(key))return state._offersCache.get(key);
 const manual=storeData(state.spotlight,s).offers||[];
 const current=storeData(state.daily,s).offers||[];
 const supplements=storeData(state.supplemental,s).offers||[];
 const scan=state.catalog?.stores?.[s];
 const fresh=state.catalog?.generated_at?.slice(0,10)===today()&&scan?.status==='ok';
 const external=fresh&&Array.isArray(scan.offers)?scan.offers:[];
 const all=window.MaatjeOfferIdentity?.merge([...manual,...current,...external,...supplements].filter(isOfferActive))||[];
 state._offersCache.set(key,all);return all;
}
function isOfferActive(o){
 if(!o||o.is_regular_low_price||!Number.isFinite(o.price)||!validdate(o.end_date)||!validdate(o.start_date))return false;
 if(o.start_date>today()||o.end_date<today()||o.online_only)return false;
 return o.verified===true||(o.source_provider==='PrijsProfeet'&&o.promotion_status==='active')||(o.source_provider==='user_folder_image'&&!!o.evidence_date&&o.evidence_date<=today())||(o.source_provider==='Biernet'&&o.checked_at===today()&&o.status==='third_party_price_observation');
}
function recipes(s){
 const found=[],seen=new Set();
 for(const [d,origin] of [[state.daily,'dagactie'],[state.weekly,'weekinspiratie'],[state.spotlight,'folder-idee'],[state.archive,'archief']]){
   const list=origin==='archief'?(d?.stores?.[s]||[]):storeData(d,s).recipes;
   if(!Array.isArray(list))continue;
   for(const r of list){
     if(!r?.id||seen.has(r.id))continue;
     seen.add(r.id);found.push({...r,store:s,origin,...(origin==='archief'?{cost:null,price_status:'archief_verouderd'}:{})});
   }
 }
 // Geen automatische synthese meer uit gedeeltelijke productnaammatches.
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
 return !!(offer&&ingredient&&ingredient.product_id&&offer.product_id&&ingredient.product_id===offer.product_id);
}
function offerInfo(recipe,s){
const key=s+'|'+recipe.id+'|'+today();if(state._matchCache.has(key))return state._matchCache.get(key);
const active=offers(s),confirmed=[],possible=[],anchors=[],matcher=window.MaatjeProductMatcher;
const added=new Set();
function consider(offer,ingredient,role,source){
 if(!offer||!ingredient||added.has(offer.id+'|'+ingredient.name))return;
 const m=matcher?.evaluate(offer,ingredient)||{status:offer.name===ingredient.name?'compatible':'unrelated',reason:'geen beschikbare productmatcher'};
 if(m.status==='unrelated'||m.status==='incompatible')return;
 if(role==='eiwitbron'&&offer.category!==recipe.category)return;
 if(role==='groente'&&offer.category!=='groente')return;
 if(role==='aardappelen'&&!/aardappel/i.test(offer.name))return;
 added.add(offer.id+'|'+ingredient.name);
 if(m.status==='uncertain'){
   if(possible.length<8)possible.push({offer,ingredient,reason:'Variant nog te controleren: '+m.reason,source});
   return;
 }
 const linked={offer,ingredient,role,source};
 if(source==='exact'&&isOfficialOfferSource(offer,s)&&!offer.price_conflict&&matcher?.priceApplied(offer,ingredient)){
   confirmed.push(linked);
 }else{
   anchors.push(linked);
 }
}
for(const rel of (Array.isArray(recipe.offer_links)?recipe.offer_links:[])){
 const offer=active.find(o=>o.id===rel.offer_id),ing=(recipe.ingredients||[]).find(i=>i.name===rel.ingredient_name);
 if(!offer||!ing||rel.match_type!=='exact')continue;
 consider(offer,ing,offer.category===recipe.category?'eiwitbron':offer.category==='groente'?'groente':null,'exact');
}
const links=Array.isArray(recipe.offer_anchors)&&recipe.offer_anchors.length
  ?recipe.offer_anchors
  :(recipe.offer_anchor_id?[{offer_id:recipe.offer_anchor_id,ingredient_name:recipe.offer_anchor_name,role:'eiwitbron'}]:[]);
for(const link of links){
 const offer=active.find(o=>o.id===link.offer_id);
 const ing=(recipe.ingredients||[]).find(i=>i.name===link.ingredient_name);
 consider(offer,ing,link.role,'explicit');
}
for(const rel of (Array.isArray(recipe.candidate_offer_links)?recipe.candidate_offer_links:[])){
 const offer=active.find(o=>o.id===rel.offer_id),ing=(recipe.ingredients||[]).find(i=>i.name===rel.ingredient_name);
 if(offer&&ing&&matcher?.evaluate(offer,ing).status!=='incompatible'&&!added.has(offer.id+'|'+ing.name)&&possible.length<8){
   added.add(offer.id+'|'+ing.name);possible.push({offer,ingredient:ing,reason:rel.reason||'Productvariant niet onafhankelijk gecontroleerd',source:'suggested'});
 }
}
// Discover plausible recipes from ALL active products, across all stores. Never price automatically.
if(matcher&&possible.length<3){
 const ingredients=(recipe.ingredients||[]).filter(i=>/^(Groente & fruit|Eiwitbronnen|Vega & peulvruchten)$/.test(i.department)&&matcher.family(i.name));
 for(const ing of ingredients){
  if(possible.length>=3)break;
  if([...confirmed,...anchors].some(x=>x.ingredient.name===ing.name))continue;
  for(const o of active){
   if(possible.length>=3)break;
   if(added.has(o.id+'|'+ing.name))continue;
   const result=matcher.evaluate(o,ing);
   if(result.status==='unrelated'||result.status==='incompatible')continue;
   if(o.category==='bier'||o.category==='huishouden')continue;
   if(ing.department==='Eiwitbronnen'&&o.category!==recipe.category)continue;
   if(ing.department==='Vega & peulvruchten'&&o.category!=='vega')continue;
   if(ing.department==='Groente & fruit'&&o.category!=='groente')continue;
   added.add(o.id+'|'+ing.name);
   possible.push({offer:o,ingredient:ing,reason:result.status==='uncertain'?result.reason:'Zelfde productsoort; exacte schapvariant en verpakking niet gecontroleerd',source:'semantic'});
  }
 }
}
const anchored=anchors.concat(confirmed).find(x=>x.role==='eiwitbron')?.offer||null;
const discount=[...anchors,...confirmed].reduce((n,x)=>{
const i=x.ingredient,o=x.offer,k=Number(i.package_count||1);
if(!matcher?.priceApplied(o,i)||!Number.isFinite(o.regular_price)||!Number.isInteger(k)||k<1)return n;
const bundle=Number(o.multi_buy_quantity)>1&&Number.isFinite(o.multi_buy_price);
if(bundle&&k!==Number(o.multi_buy_quantity))return n;
const reference=bundle?o.regular_price:o.regular_price*k;
return n+Math.max(0,reference-i.pack_price);
},0);
const result={confirmed,anchored,anchors,possible,total:anchors.length+confirmed.length+possible.length,discount:Math.round(discount*100)/100};
state._matchCache.set(key,result);return result;
}
function recipeSort(a,b){
const ca=offerInfo(a,a.store),cb=offerInfo(b,b.store);
const pa=recipePrice(a),pb=recipePrice(b),an=pa.total===null?Infinity:pa.total,bn=pb.total===null?Infinity:pb.total;
if(state.sortBy==='price')return an-bn||cb.confirmed.length-ca.confirmed.length||a.title.localeCompare(b.title,'nl');
if(state.sortBy==='protein')return (b.macros?.protein_g||-1)-(a.macros?.protein_g||-1)||an-bn;
if(state.sortBy==='time')return (a.minutes||999)-(b.minutes||999)||an-bn;
return (window.MaatjeRanking?.score(cb)||0)-(window.MaatjeRanking?.score(ca)||0)||an-bn||a.title.localeCompare(b.title,'nl');
}
function recipeFiltered(r){
if(state.recipeQuality!=='all'&&r.quality_status==='concept_niet_culinair_getest')return false;
if(state.kind!=='alle'&&r.category!==state.kind)return false;if(state.subtype!=='alle'&&proteinSubtype(r)!==state.subtype)return false;
if(state.query&&!(r.title+' '+(r.cuisine||'')+' '+(r.ingredients||[]).map(i=>i.name).join(' ')).toLocaleLowerCase('nl-NL').includes(state.query.toLocaleLowerCase('nl-NL')))return false;
const m=offerInfo(r,r.store);
if(state.dealFilter==='confirmed'&&!m.confirmed.length)return false;if(state.dealFilter==='anchor'&&!(m.anchors.length||m.confirmed.length))return false;
if(state.dealFilter==='potential'&&!m.possible.length)return false;
return true;
}

const PERSONAL_MATCH={
bier:/\b(bier|pils(?:ener)?|radler|weizen|witbier|bokbier|bockbier|ipa|speciaalbier)\b/,
sungold:/\b(sungold|sun gold)\b/,pindakaas:/pindakaas/,kwark:/\b(kwark|skyr|cottage cheese)\b/,dreft:/\bdreft\b/,
walnoten:/\bwalnoten\b/,tofu:/\b(vivera|tofu|tempeh)\b/,gemengdgehakt:/\b(gemengd gehakt|half om half gehakt|rundergehakt|varkensgehakt)\b/,
kipfilet:/\b(kipfilet|kipfiletblokjes|kipfiletreepjes)\b/,
vis:/\b(zalmfilet|koolvisfilet|kabeljauwfilet|makreelfilet|forelfilet|haringfilet)\b/,
pompoen:/\b(flespompoen|biologische pompoen|oranje pompoen)\b/,
sperziebonen:/\b(sperziebonen|gebroken bonen)\b/,bospeen:/\bbospeen\b/,popcorn:/\bpopcorn\b/
};
function profileKey(o){
const name=norm(o.name);
if(/\bvolle melk\b/.test(name)&&!/plantaardig|halfvol|mager/.test(name))return 'volle_melk';
if(/skuumkoppe/.test(name))return 'skuumkoppe';
if(o?.category==='bier')return 'bier';
if(/(boemboe soto|soto boemboe|saoto boemboe|boemboe saoto)/.test(name))return 'soto_boemboe';
if(/(kippenpoten|kippenbouten|kipbouten|kippenpootjes|drumsticks)/.test(name)&&!/kruiden|saus|soep/.test(name))return 'kippenpoten';
if(/\b(sereh|citroengras|lemongrass)\b/.test(name)&&!/thee|smaak|aroma|saus|kruidenmix/.test(name))return 'sereh';
if(/kruiden|saus|bouillon|salade|schnitzel|burger|knaks|spek|baby|gepaneerd|kipmix/.test(name))return null;
if(/plantaardig|vegan|vegetarisch/.test(name)&&(o.category==='vis'||o.category==='kip'||o.category==='vlees'))return null;
return Object.keys(PERSONAL_MATCH).find(k=>PERSONAL_MATCH[k].test(name))||null;
}
function chosenWatch(){return (state.watchlist?.items||[]).filter(x=>!state.watchDisabled.includes(x.key))}
function priceRecords(key,s){
return (state.personalPrices?.products||[]).filter(p=>p.group===key&&p.store===s&&Number.isFinite(p.price)&&p.price>=0&&(
p.status==='official_promo'&&p.start_date<=today()&&p.end_date>=today()||
['official_regular_observed','external_regular_observed','official_discount_undated'].includes(p.status)&&p.checked_date&&p.checked_date<=today()&&
(Date.parse(today()+'T12:00:00Z')-Date.parse(p.checked_date+'T12:00:00Z'))<=(p.status==='official_discount_undated'?86400000:7*86400000)));
}
function normalizedPrice(p){
if(!p||!Number.isFinite(p.price)||!Number.isFinite(p.quantity)||p.quantity<=0)return null;
if(p.unit==='g'||p.unit==='ml')return p.price*1000/p.quantity;
if(p.unit==='stuk')return p.price/p.quantity;
return null;
}
function normalizedUnit(p){return p.unit==='g'?'kg':p.unit==='ml'?'L':p.unit==='stuk'?'stuk':'verpakking'}

function favoriteTarget(o,s){
return {name:String(o?.name||''),pack_label:String(o?.pack_label||((o?.quantity&&o?.unit)?o.quantity+' '+o.unit:'')),ean:o?.ean||null,store:s};
}
function isFavorite(o,s){return !!window.MaatjeFavorites?.find(state.favorites,favoriteTarget(o,s),s)}
function favButton(o,s){
const p=favoriteTarget(o,s),yes=isFavorite(p,s);
return '<button class="favorite-heart '+(yes?'chosen':'')+'" type="button" data-fav-toggle="1" data-fav-store="'+attr(s)+'" data-fav-name="'+attr(p.name)+'" data-fav-pack="'+attr(p.pack_label)+'" data-fav-ean="'+attr(p.ean||'')+'" aria-pressed="'+yes+'" aria-label="'+(yes?'Verwijder '+attr(p.name)+' uit favorieten':'Bewaar '+attr(p.name)+' als favoriet')+'" title="'+(yes?'Verwijder favoriet':'Opslaan als favoriet')+'">'+(yes?'♥':'♡')+'</button>';
}
function toggleFavorite(p,s){
const helper=window.MaatjeFavorites;if(!helper)return;
const product=favoriteTarget(p,s),ix=state.favorites.findIndex(f=>helper.same(f,product,s));
if(ix>=0)state.favorites.splice(ix,1);else if(product.name)state.favorites.unshift(helper.record(product,s));
save();
}
function favoriteMatches(f,s){
return offers(s).filter(o=>window.MaatjeFavorites?.same(f,favoriteTarget(o,s),s)).sort((a,b)=>Number(!!b.verified)-Number(!!a.verified)||a.price-b.price);
}
function favoriteDashboard(){
 const helper=window.MaatjeFavorites;
 const groups=helper?.familyMembers(state.favorites)||[];
 const matches=groups.reduce((sum,g)=>sum+ORDER.reduce((n,s)=>n+offers(s).filter(o=>helper.familyKey(o)===g.key).length,0),0);
 let out=title('Mijn productfavorieten','Dezelfde productfamilie bij elkaar. Verpakkingen en 0.0 blijven afzonderlijk herkenbaar; prijs per liter alleen bij exact bekende inhoud.');
 out+='<div class="favorite-summary"><div><strong>♥ '+state.favorites.length+' bewaarde varianten · '+groups.length+' productgroepen</strong><p>'+matches+' mogelijke aanbiedingen in ontvangen feeds. Dit zegt niet dat alle winkelacties of reguliere prijzen zijn gevonden.</p></div><button class="button secondary small" data-offer-mode="all">Meer favorieten ♡</button></div>';
 if(!groups.length)return out+empty('Nog geen favoriete producten','Klik op een hartje in Alle aanbiedingen om producten te bewaren.');
 for(const group of groups){
 const saved=group.items;
 out+='<section class="personal-product favorite-product favorite-family"><div class="favorite-title"><div><strong>'+safe(group.label)+'</strong><small>'+saved.length+' bewaarde verpakking'+(saved.length===1?'':'en')+' · alle varianten apart vergelijkbaar</small></div></div>';
 out+='<div class="favorite-variant-list">'+saved.map(f=>'<div class="favorite-variant"><span>'+safe(f.name)+' <small>· '+safe(f.pack_label||'verpakking onbekend')+'</small></span>'+favButton(f,f.store||'jumbo')+'</div>').join('')+'</div>';
 out+='<div class="personal-grid">'+ORDER.map(s=>{
 const choices=offers(s).filter(o=>helper.familyKey(o)===group.key).map(o=>({o,unit:window.MaatjePricing?.unitCost(o),exact:saved.some(f=>helper.same(f,favoriteTarget(o,s),s))}));
 choices.sort((a,b)=>Number(b.exact)-Number(a.exact)||Number(!!a.o.price_conflict)-Number(!!b.o.price_conflict)||(a.unit&&b.unit?a.unit.price-b.unit.price:0)||a.o.price-b.o.price);
 if(!choices.length)return '<div class="personal-shop"><b>'+safe(NAMES[s])+'</b><span class="personal-unknown">Geen bijpassende actie in de beschikbare bronnen</span><small>Reguliere prijs niet bekend; assortiment kan groter zijn.</small></div>';
 return '<div class="personal-shop"><b>'+safe(NAMES[s])+'</b>'+
 choices.slice(0,5).map(({o,unit,exact})=>
 '<div class="favorite-store-option"><div class="favorite-store-price"><strong>'+money(o.price)+(o.price_conflict?'*':'')+'</strong>'+(unit?'<span>'+money(unit.price)+'/L</span>':'<span>Eenheidsprijs onbekend</span>')+'</div><small>'+safe(o.name)+' · '+safe(o.pack_label||'verpakking onbekend')+'</small><small>'+(exact?'Exact bewaarde variant':'Andere verpakking/variant binnen dezelfde productfamilie')+' · '+safe(offerEvidenceLabel(o,s))+'</small><small>Geldig t/m '+dateNL(o.end_date)+'</small>'+(o.source?.url?'<a href="'+attr(o.source.url)+'" rel="noopener noreferrer" target="_blank">Prijsbron</a>':'')+
 '</div>').join('')+
 (choices.length>5?'<small>+'+(choices.length-5)+' aanvullende waarnemingen in Alle aanbiedingen</small>':'')+'</div>';
 }).join('')+'</div></section>';
 }
 return out+'<div class="info-banner warning">Productgroepen zijn geen bewijs dat twee artikelen identiek zijn. Vergelijk alleen gelijkwaardige inhoud en de prijs per liter; 0.0 en alcoholhoudend blijven gescheiden. Hartjes worden in deze browser bewaard, niet tussen apparaten gesynchroniseerd.</div>';
}

function quickTrackedProducts(){
const important=['volle_melk','skuumkoppe','soto_boemboe','kippenpoten','sereh'];
const watch=chosenWatch().filter(w=>important.includes(w.key));
if(!watch.length)return '';
let out=title('Mijn vaste favorieten · ook zonder actie','Dit zijn productinteresses uit je boodschappenprofiel. Hartjes bewaren daarnaast exacte verpakkingen in deze browser.');
out+='<div class="tracked-items">'+watch.map(w=>{
 const offersByStore=ORDER.map(s=>({store:s,offers:offers(s).filter(o=>profileKey(o)===w.key),regular:priceRecords(w.key,s)}));
 return '<article class="tracked-product"><div class="tracked-head"><strong>'+safe(w.title)+'</strong><small>'+safe(w.description||'')+'</small></div><div class="tracked-store-grid">'+offersByStore.map(p=>{
 let o=p.offers[0], reg=[...p.regular].sort((a,b)=>(normalizedPrice(a)??Infinity)-(normalizedPrice(b)??Infinity))[0];
 if(o)return '<div><b>'+safe(NAMES[p.store])+'</b><div><strong>'+money(o.price)+'</strong><small> Actie gemeld</small></div><small>'+safe(o.pack_label||o.name)+'</small>'+favButton(o,p.store)+'</div>';
 if(reg)return '<div><b>'+safe(NAMES[p.store])+'</b><div><strong>'+money(reg.price)+'</strong><small> '+safe(reg.status==='external_regular_observed'?'extern':reg.status==='official_discount_undated'?'korting, duur onbekend':'regulier')+'</small></div><small>'+safe(reg.name)+'</small>'+favButton(reg,p.store)+'</div>';
 return '<div><b>'+safe(NAMES[p.store])+'</b><div class="personal-unknown">Prijs onbekend</div></div>';
 }).join('')+'</div></article>';
 }).join('')+'</div>';
return out;
}
function personalComparison(){
const watch=chosenWatch();
let out=title('Mijn vaste producten · drie supermarkten','Je kiest zelf de winkel. Vergelijken gebeurt alleen als de productvariant en eenheid passen.');
out+='<div class="personal-settings"><span>'+watch.length+' geselecteerde productgroepen</span><button class="button secondary small" data-manage-watch="1">'+(state.manageWatch?'Mijn selectie sluiten':'Mijn producten aanpassen')+'</button></div>';
if(state.manageWatch)out+='<div class="watch-editor">'+(state.watchlist?.items||[]).map(w=>'<label class="watch-option"><input type="checkbox" data-watch-key="'+attr(w.key)+'" '+(!state.watchDisabled.includes(w.key)?'checked':'')+'><span><b>'+safe(w.title)+'</b><small>'+safe(w.description)+'</small></span></label>').join('')+'</div>';
for(const w of watch){
const observations=ORDER.map(s=>({store:s,entries:priceRecords(w.key,s)}));
out+='<section class="personal-product"><div class="personal-product-title"><strong>'+safe(w.title)+'</strong><small>'+safe(w.description||'')+'</small></div>';
out+='<div class="personal-grid">'+observations.map(({store,entries})=>{
const sorted=[...entries].sort((a,b)=>(normalizedPrice(a)??Infinity)-(normalizedPrice(b)??Infinity));
if(!sorted.length)return '<div class="personal-shop"><b>'+safe(NAMES[store])+'</b><span class="personal-unknown">Geen recente prijs bevestigd</span></div>';
const r=sorted[0],p=normalizedPrice(r);
return '<div class="personal-shop"><b>'+safe(NAMES[store])+'</b><strong class="personal-price">'+money(r.price)+'</strong><small>'+safe(r.name)+'</small><small>'+ (p===null?'Prijs per eenheid onbekend':money(p)+'/'+safe(normalizedUnit(r))) +'</small>'+(sorted.length>1?'<small>'+ (sorted.length-1)+' andere variante(n) geregistreerd</small>':'')+'<small class="personal-evidence">'+safe(r.status==='official_promo'?'Actie (controleer datum)':r.status==='official_discount_undated'?'Webkorting, periode onbekend':r.status==='external_regular_observed'?'Externe prijswaarneming':'Reguliere schapprijs')+'</small>'+'<div class="personal-shop-actions">'+favButton(r,store)+'</div><a href="'+attr(r.url)+'" target="_blank" rel="noopener noreferrer">Prijsbron ↗</a></div>';
}).join('')+'</div>';
if(w.key==='sungold')out+='<p class="personal-finding">Gelijke SunGold 750 g: Jumbo € 4,99 en Albert Heijn € 6,59. Lidl-prijs nog niet bevestigd.</p>';
if(w.key==='pindakaas')out+='<p class="personal-finding">Jumbo huismerk is per kilo goedkoper dan de Calvé-actie. Samenstelling van gewone en 100%-pindakaas verschilt; geen automatische vergelijkbaarheid.</p>';
if(w.key==='sperziebonen')out+='<p class="personal-finding">De waargenomen diepvriesbonen van € 2,07/kg zijn goedkoper dan de verse aanbieding van circa € 4,98/kg.</p>';
out+='</section>';
}
out+='<div class="info-banner warning">Ontbrekende prijsgegevens betekenen niet dat een winkel het product niet verkoopt. Een prijs met peildatum is geen live-kassagarantie. Bij verschillende varianten of aankoopaantallen is geen absolute goedkoopste winkel vastgesteld.</div>';
return out;
}

function personalHighlights(){
const selected=new Set(chosenWatch().map(w=>w.key));
const relevant=ORDER.flatMap(s=>offers(s).filter(o=>selected.has(profileKey(o))).map(o=>({...o,store:s,interest:profileKey(o)})));
const hasOld=o=>typeof o.regular_price==='number'&&o.regular_price>o.price&&!o.price_conflict;
const saving=o=>hasOld(o)?o.regular_price-o.price:0;
relevant.sort((a,b)=>
Number(isOfficialOfferSource(b,b.store)&&!b.price_conflict)-Number(isOfficialOfferSource(a,a.store)&&!a.price_conflict)||
Number(b.interest==='skuumkoppe')-Number(a.interest==='skuumkoppe')||
saving(b)-saving(a)||a.name.localeCompare(b.name,'nl'));
let out=title('Voor mij · aanbiedingen op je vaste producten','Alleen gevolgde productgroepen; ook relevante externe meldingen tellen mee, maar blijven als onbevestigd gemarkeerd.');
out+=relevant.length?'<div class="cards">'+relevant.slice(0,18).map(o=>dealCard(o,o.store)).join('')+'</div>':empty('Geen actuele actie op je vaste producten gevonden','Bekijk daaronder de reguliere prijzen. Ontbrekende aanbiedingen zijn geen bewijs dat een product niet in de actie is.');
if(relevant.length>18)out+='<p class="muted">Er zijn '+(relevant.length-18)+' aanvullende treffers. Open Alle aanbiedingen en filter op de betreffende categorie.</p>';
return out;
}
function storeRecipeCounts(s){return recipes(s).length}
function status(){const d=state.daily;const at=d?.generated_at;const date=at?String(at).slice(0,10):null;return !date?'Dagrapport ontbreekt':date<today()?'Dagrapport verouderd: '+date:'Dagrapport: '+date}
function storePill(s){return '<span class="store-mini">'+safe(NAMES[s]||'Algemene inspiratie')+'</span>'}

function recipePrice(r){return window.MaatjePricing?.basket(r,today())||{state:'unpriced',total:null,partial:0,missing:[],oldest_date:null}}
function recipeIsCurrentPrice(r){return recipePrice(r).state==='today_confirmed'}
function priceTagText(r){
 const p=recipePrice(r);return p.state==='today_confirmed'?'Vandaag onderbouwd':p.state==='historical_estimate'?'Historische prijsindicatie':p.state==='partial'?'Deels geprijsd':'Prijs onbekend';
}
function priceStatusText(r){
 const p=recipePrice(r);
 if(p.state==='today_confirmed')return '4 porties · vandaag gecontroleerde webshopprijzen, geen kassagarantie';
 if(p.state==='historical_estimate')return '4 porties · historische indicatie'+(p.oldest_date?' (oudste prijs '+p.oldest_date+')':' zonder exacte peildatum')+', geen actuele kassaprijs';
 return '4 porties · '+p.missing.length+' ingrediënten zonder verpakkingsprijs, geen complete mand';
}
function priceQuality(r){const p=recipePrice(r);return p.total!==null?money(p.total):p.partial>0?'Minimaal '+money(p.partial):'Prijs onbekend'}
function statusTag(r){return '<span class="tag '+(recipeIsCurrentPrice(r)?'fresh':'orange')+'">'+safe(priceTagText(r))+'</span>'}
function storeLogo(s){return '<span class="store-dot '+s+'">'+(s==='lidl'?'L':s==='jumbo'?'J':'AH')+'</span>'}
function clearPage(){['vandaag','aanbiedingen','recepten','lijst','mijn'].forEach(v=>$('#view-'+v).classList.toggle('hidden',v!==state.view));document.querySelectorAll('[data-view]').forEach(el=>el.classList.toggle('active',el.dataset.view===state.view))}
function header(eyebrow,title,subtitle){$('#page-intro').innerHTML='<div class="eyebrow">'+safe(eyebrow)+'</div><h1>'+title+'</h1><p class="subhead">'+safe(subtitle)+'</p>'}
function title(t,sub,action){return '<div class="section-heading"><div><h2>'+safe(t)+'</h2>'+(sub?'<p>'+safe(sub)+'</p>':'')+'</div>'+(action||'')+'</div>'}
function storeControls(all=true){return '<div class="control-row store-filter">'+(all?'<button class="pill '+(state.store==='alle'?'active':'')+'" data-store="alle">Alle winkels</button>':'')+ORDER.map(s=>'<button class="pill '+(state.store===s?'active':'')+'" data-store="'+s+'">'+safe(NAMES[s])+'</button>').join('')+'</div>'}

const OFFER_CATEGORY_NAMES={alle:'Alle aanbiedingen',bier:'Bier',dranken:'Fris & koffie',overige_dranken:'Overige dranken',huishouden:'Huishouden',fruit:'Fruit',voorraad:'Voorraad & noten',zuivel:'Zuivel',groente:'Groente',kip:'Kip',vlees:'Vlees',vis:'Vis',vega:'Vega',snacks:'Snacks',brood_graan:'Brood & granen',overig:'Overig'};
function kindControls(offerPage=false){
 if(offerPage){
 const all=ORDER.flatMap(s=>offers(s)),cats=['alle',...Object.keys(OFFER_CATEGORY_NAMES).filter(c=>c!=='alle'&&all.some(o=>o.category===c))];
 const select='<select class="offer-category-select" id="offer-category" aria-label="Productgroep aanbiedingen">'+cats.map(c=>'<option value="'+c+'"'+(state.kind===c?' selected':'')+'>'+safe(OFFER_CATEGORY_NAMES[c])+' ('+(c==='alle'?all.length:all.filter(o=>o.category===c).length)+')</option>').join('')+'</select>';
 const top=['alle','bier','groente','huishouden','fruit','zuivel'].filter(c=>cats.includes(c));
 return '<div class="control-row offer-filter-row">'+top.map(c=>'<button class="pill '+(state.kind===c?'active':'')+'" data-kind="'+c+'">'+safe(OFFER_CATEGORY_NAMES[c])+'</button>').join('')+select+'<input class="search" id="find" aria-label="Zoek aanbiedingen" placeholder="Zoek merk of product..." value="'+attr(state.query)+'"></div>';
 }
 return '<div class="control-row">'+['alle','kip','vlees','vis','vega'].map(k=>'<button class="pill '+(state.kind===k?'active':'')+'" data-kind="'+k+'">'+(KINDS[k]||'Alle soorten')+'</button>').join('')+'<input class="search" id="find" aria-label="Zoek recepten" placeholder="Zoek recept, keuken of ingrediënt…" value="'+attr(state.query)+'"></div>';
}
function recipeControls(){return '<div class="recipe-toolbar"><label>Sorteer op <select id="recipe-sort"><option value="deals"'+(state.sortBy==='deals'?' selected':'')+'>Meeste acties eerst</option><option value="price"'+(state.sortBy==='price'?' selected':'')+'>Laagste kassaprijs</option><option value="protein"'+(state.sortBy==='protein'?' selected':'')+'>Meeste eiwit</option><option value="time"'+(state.sortBy==='time'?' selected':'')+'>Snelste bereiding</option></select></label><label>Actiestatus <select id="deal-filter"><option value="all"'+(state.dealFilter==='all'?' selected':'')+'>Alle recepten</option><option value="confirmed"'+(state.dealFilter==='confirmed'?' selected':'')+'>Actieprijs verwerkt</option><option value="anchor"'+(state.dealFilter==='anchor'?' selected':'')+'>Recept met actieproduct</option><option value="potential"'+(state.dealFilter==='potential'?' selected':'')+'>Past bij aanbieding</option></select></label><label>Kwaliteit <select id="recipe-quality"><option value="developed"'+(state.recipeQuality==='developed'?' selected':'')+'>Uitgewerkt & actie-ideeën</option><option value="all"'+(state.recipeQuality==='all'?' selected':'')+'>Ook 40 oudere concepten</option></select></label></div>'}

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
 const m=offerInfo(r,r.store),main=window.MaatjeRanking?.mainOffer(m);
 if(main){
  const priced=m.confirmed.some(x=>x===main);
  return '<span class="offer-badge '+(priced?'confirmed':'anchor')+'">Hoofdingrediënt in actie: '+safe(main.offer.name)+' · '+(priced?'productprijs verwerkt, mand nog controleren':'prijs/variant nog niet volledig bevestigd')+'</span>';
 }
 if(m.confirmed.length)return '<span class="offer-badge confirmed">'+m.confirmed.length+' aanvullend actieproduct'+(m.confirmed.length>1?'en':'')+' · prijs deels verwerkt</span>';
 if(m.anchors.length)return '<span class="offer-badge anchor">'+m.anchors.length+' aanvullend actieproduct'+(m.anchors.length>1?'en':'')+' · voordeel niet bewezen</span>';
 if(m.possible.length)return '<span class="offer-badge candidate">'+m.possible.length+' mogelijke aanbieding'+(m.possible.length>1?'en':'')+' · niet verwerkt</span>';
 return '<span class="offer-badge neutral">Geen actie gekoppeld</span>';
}
function recipeSourceLabel(r){
if(r.quality_status==='concept_niet_culinair_getest')return 'Concept · oorspronkelijke receptbron niet volledig gecontroleerd';
if(r.quality_status==='uitgewerkt_niet_culinair_getest')return 'Eigen bewerking · niet proefgekookt';
if(r.origin==='folder-idee')return 'Eigen receptidee rond actie · niet proefgekookt';
if(r.origin==='dagactie')return 'Eigen dagrecept · niet proefgekookt';
return 'Eigen inspiratie of bewerking · niet proefgekookt';
}
function recipeCard(r){
const id=r.store+'|'+r.id,info=offerInfo(r,r.store),price=recipePrice(r),tip=info.confirmed.length?'Actieprijzen in ingrediënten: '+info.confirmed.map(x=>x.offer.name).join(' · '):info.anchors.length?'Actieproduct gekoppeld: '+info.anchors.map(x=>x.offer.name).join(' · '):info.possible.length?'Vergelijkbare aanbieding (niet bewezen): '+info.possible.slice(0,3).map(x=>x.offer.name).join(' · '):'';
return '<article class="recipe-card"><div class="recipe-visual '+(r.category==='kip'?'chicken':r.category==='vis'?'fish':r.category==='vlees'?'meat':'vega')+'">'+statusTag(r)+recipeSaveButton(r)+'<span class="plate" aria-hidden="true">'+(SYMBOLS[r.category]||'🥗')+'</span></div><div class="recipe-offers">'+offerBadge(r)+'</div><h3>'+safe(r.title)+'</h3><p>'+safe(r.cuisine||'Smakelijk & voedzaam')+' · '+safe(NAMES[r.store]||'')+'</p><p class="recipe-origin">'+safe(recipeSourceLabel(r))+'</p>'+featured(r)+(tip?'<p class="offer-hint">'+safe(tip)+'</p>':'')+(info.discount>0?'<p class="offer-smallnote">Oude vergelijkingsprijzen bekend, maar geen bewezen besparing op de hele maaltijd.</p>':'')+(price.state==='partial'?'<p class="lower-bound">'+price.missing.length+' ingrediënten niet geprijsd · géén volledige kassamand</p>':'')+'<div class="recipe-bottom"><div><b>'+priceQuality(r)+'</b><small>4 porties · '+(price.state==='historical_estimate'?'oude prijspeildatum, niet actueel':price.state==='today_confirmed'?'actuele berekening':'prijs onvolledig')+(r.macros?' · '+safe(r.macros.protein_g)+' g eiwit/p':' · macro’s volgen')+'</small></div><button class="button small" data-open="'+attr(id)+'">Bekijk →</button></div></article>';
}


function isOfficialOfferSource(o,s){
const url=String(o?.source?.url||'');
if(!/^https:\/\//.test(url)||o.verified!==true)return false;
try{
 const h=new URL(url).hostname.toLowerCase().replace(/^www\./,'');
 return s==='lidl'?h==='lidl.nl'||h.endsWith('.lidl.nl'):
        s==='jumbo'?h==='jumbo.com'||h.endsWith('.jumbo.com'):
        s==='ah'?h==='ah.nl'||h.endsWith('.ah.nl'):false;
}catch{return false}
}

function auditStatus(s,o){return state.audit?.day===today()?state.audit?.status_by_id?.[s]?.[o.id]:null;}
function auditBadge(o,s){
 const a=auditStatus(s,o);
 if(!a)return '<p class="muted">Automatische productcontrole nog niet gepubliceerd of verouderd.</p>';
 const detail=a.status==='needs_review'?'Gegevens vragen controle: '+a.issues.join(', '):
 a.issues?.length?'Automatisch nagekeken, met aandachtspunten: '+a.issues.join(', '):
 a.status==='retailer_page_reported'?'Datums, bron en prijslogica gecontroleerd; winkel-URL aanwezig':
 'Datums, bron en prijslogica gecontroleerd; externe prijswaarneming';
 return '<p class="muted">'+safe(detail)+' · geen onafhankelijke kassagarantie</p>';
}
function auditSummary(){
 const report=state.audit;
 if(!report||report.day!==today())return '<div class="info-banner warning">De actuele kwaliteitscontrole is nog niet gepubliceerd. Aanbiedingenfeed ≠ geverifieerde kassaprijzen.</div>';
 return '<div class="info-banner"><strong>Dagelijkse kwaliteitscontrole ('+safe(report.day)+'):</strong> '+
 ORDER.map(s=>{const r=report.stores?.[s];return r?safe(NAMES[s])+': '+r.evaluated+' ontvangen aanbiedingen nagekeken, '+r.with_issues+' met aandachtspunten (waarvan '+r.by_status.needs_review+' ernstig)':safe(NAMES[s])+': geen controle';}).join(' · ')+
 '<p>Deze controle omvat alle ONTVANGEN aanbiedingen, niet alle bestaande winkelacties; zij is geen onafhankelijke prijsbevestiging.</p></div>';
}
function offerEvidenceLabel(o,s){
if(o.price_conflict)return 'Bronnen verschillen';if(isOfficialOfferSource(o,s))return 'Winkelbron, niet onafhankelijk bevestigd';
return o.source_provider==='Biernet'?'Biernet: externe actieprijs':o.source_provider==='PrijsProfeet'?'Externe prijswaarneming':o.source_provider==='user_folder_image'?'Aangeleverde folderfoto · prijs controleren':'Folder- of vergelijkingsbron';
}

function productReview(s,o){
 const r=state.verification?.reviews?.[s]?.[o.id];
 return r?.checked_at===today()?r:null;
}

function campaignHighlights(s){
 const offers=(state.verification?.campaigns||[]).filter(c=>c.store===s&&c.end_date>=today());
 if(!offers.length)return '';
 const cards=offers.map(c=>'<div class="campaign-card"><strong>'+safe(c.name)+'</strong><div class="campaign-condition">'+safe(c.condition)+'</div>'+
 (Number.isFinite(c.price)?'<p>'+money(c.price)+' '+safe(c.unit||'')+'</p>':'<p class="muted">Variantprijs onbekend — controleer verpakking en kassaprijs</p>')+
 '<a href="'+attr(c.url)+'" target="_blank" rel="noopener noreferrer">Bekijk officiële AH Bonus ↗</a></div>').join('');
 return title('Extra aanbiedingen zonder vaste variantprijs','Huishouden en frisdrank: betrouwbare voorwaarden, maar niet zomaar een prijs per tablet of wasbeurt.')+'<div class="campaign-grid">'+cards+'</div>';
}
function reviewLabel(s,o){
 const r=productReview(s,o);if(!r)return '';
 const st=r.status;
 const warn=/conflicting|photo_only|folder_confirmed|variant_weight|variant_price|old_price_conflict/.test(st);
 const label=/conflicting/.test(st)?'Prijsverschil tussen bronnen':
 /photo_only|folder_confirmed/.test(st)?'Folderprijs nog niet onafhankelijk nagekeken':
 /old_price_conflict/.test(st)?'Oude prijs verschilt per bron':
 /bundle/.test(st)?'Bundelbedrag gecontroleerd':
 /unit_price_correction/.test(st)?'Eenheidsprijs herberekend':
 /variant_range/.test(st)?'Verschillende oude prijzen per variant':
 /regular_not_promo/.test(st)?'Reguliere prijs, geen actie':'Prijs met bronnen vergeleken';
 const links=r.checks.filter(x=>x.url).slice(0,4).map(x=>'<li><a href="'+attr(x.url)+'" target="_blank" rel="noopener noreferrer">'+safe(x.site)+' ↗</a>'+(Number.isFinite(x.price)?' · '+money(x.price):'')+'<small>'+safe(x.note||'')+'</small></li>').join('');
 return '<div class="review-box '+(warn?'review-uncertain':'')+'"><strong>Broncontrole 28 okt: '+safe(label)+'</strong>'+(warn?'<small>Exacte variant en actuele kassaprijs controleren.</small>':'')+'<details class="review-details"><summary>Prijs en uitleg per bron ('+r.checks.length+')</summary><ul>'+links+'</ul></details></div>';
}
function dealCard(o,s){
const alt=o.cheapest_alternative;
const cheaper=alt&&Number.isFinite(alt.unit_price)&&Number.isFinite(o.unit_price)&&alt.unit===o.unit&&alt.unit_price<o.unit_price;
const independent=isOfficialOfferSource(o,s)&&!o.price_conflict;
return '<article class="deal-card"><div class="deal-card-top"><div>'+storePill(s)+'<h3>'+safe(o.name||'Product')+'</h3></div><div class="deal-card-actions">'+favButton(o,s)+'</div><span class="tag '+(independent?'fresh':'orange')+'">'+offerEvidenceLabel(o,s)+'</span></div><div class="price-line"><span class="price">'+money(o.price)+'</span>'+(typeof o.regular_price==='number'&&o.regular_price>o.price?'<span class="oldprice">'+money(o.regular_price)+'</span>':'')+'</div><div class="deal-meta">'+safe(o.pack_label||'Verpakking onbekend')+(o.unit_price?(' · '+money(o.unit_price)+'/'+safe(o.unit||'kg')):'')+' · geldig t/m '+dateNL(o.end_date)+(o.multi_buy_quantity?' · '+safe(o.multi_buy_quantity)+' voor '+money(o.multi_buy_price):'')+(o.member_required?' · klantenkaart nodig':'')+(o.loyalty_price?' · ledenprijs '+money(o.loyalty_price):'')+'</div>'+(o.price_conflict?'<div class="deal-note bad">Prijsverschil tussen bronnen: '+safe(o.price_conflict)+'</div>':'')+(cheaper?'<div class="deal-note bad">Goedkoper per '+safe(o.unit)+': '+safe(alt.name)+' ('+money(alt.unit_price)+' tegenover '+money(o.unit_price)+' per '+safe(o.unit)+'). Controleer beschikbaarheid.</div>':alt?'<div class="deal-note">Alternatief: '+safe(alt.name)+' ('+money(alt.price)+').</div>':'<div class="deal-note">'+(independent?'Officiële actiebron, maar de laagste prijs t.o.v. alternatieven en kassabeschikbaarheid zijn niet gegarandeerd.':'Actie gemeld via een externe bron; niet onafhankelijk bij de supermarkt bevestigd. Vergelijk reguliere alternatieven.')+'</div>')+(o.source?.url?'<div class="deal-meta"><a href="'+attr(/^https:\/\//.test(o.source.url)?o.source.url:'#')+'" rel="noopener noreferrer" target="_blank">Prijsbron ↗</a></div>':'')+reviewLabel(s,o)+auditBadge(o,s)+'</article>';
}
function empty(head,body){return '<div class="empty"><div class="empty-art">◌</div><strong>'+safe(head)+'</strong>'+safe(body)+'</div>'}
function overview(){
header('Jouw slimme boodschappenhulp','Wat eten we <span style="color:#719b66">deze week?</span>','Bekijk eerst alle drie de supermarkten. Kies straks zelf op basis van wat je lekker vindt.');
let x='<section class="hero"><div><div class="eyebrow" style="color:#c6e79b">GOED ETEN · SLIM KOPEN</div><h1>Meer smaak.<br><em>Minder uitgeven.</em></h1><p>Acties, nieuwe recepten en boodschappenlijsten per supermarkt. Altijd vier porties, genoeg voor twee dagen.</p></div><div class="hero-art" aria-hidden="true">✳</div></section>';

x+=title('Drie winkels, jouw keuze','Jij kiest zelf precies één winkel. Hieronder zie je de bronwaarnemingen en receptmogelijkheden per supermarkt.');
x+='<div class="store-grid">'+ORDER.map(s=>{
const deals=recipes(s).filter(r=>window.MaatjeRanking?.mainOffer(offerInfo(r,s))).length;
const known=recipes(s).filter(r=>recipePrice(r).total!==null).length;
return '<article class="store-card"><div class="store-top"><div class="store-logo">'+storeLogo(s)+safe(NAMES[s])+'</div><span class="tag">'+deals+' met hoofdproductactie</span></div><p>'+deals+' recepten met een hoofdingrediënt uit de beschikbare actiebronnen. '+known+' recepten met een prijsindicatie op basis van volledige verpakkingen (niet noodzakelijk actueel).</p><div class="store-metrics"><div class="metric"><b>'+offers(s).length+'</b><small>lopende acties</small></div><div class="metric"><b>'+storeRecipeCounts(s)+'</b><small>dag- en folderrecepten</small></div></div><button class="button full" data-goto-store="'+s+'">Bekijk '+safe(NAMES[s])+' →</button></article>';
}).join('')+'</div>';
x+='<div class="my-home-link"><span>♧ <strong>'+state.savedRecipes.length+' bewaarde recepten</strong> · '+Object.values(state.selected).reduce((n,v)=>n+(v?.length||0),0)+' gerechten gepland</span><button class="button secondary small" data-view="mijn">Mijn recepten →</button></div>';
x+='<div class="favorite-home-link"><span>♥ <strong>'+state.favorites.length+' favorieten</strong> · Bekijk direct je actuele aanbiedingen</span><button class="button secondary small" data-open-favorites="1">Mijn favorieten →</button></div>';

x+=title('Recepten rond deze weekacties','Hoofdingrediënten krijgen voorrang op kleine groentekortingen. De totale besparing is pas betrouwbaar bij een volledige vergelijkbare mand.');
for(const s of ORDER){
let featured=recipes(s).filter(r=>{const m=offerInfo(r,s);return m.confirmed.length||m.anchors.length}).sort(recipeSort).slice(0,3);
x+=title(NAMES[s],featured.length?featured.length+' uitgelichte recepten met lopende actieproducten':'Geen exact gekoppelde actierecepten gevonden','<button class="button secondary small" data-goto-store="'+s+'">Alle recepten →</button>');
x+=featured.length?'<div class="cards">'+featured.map(recipeCard).join('')+'</div>':empty('Geen gekoppelde actierecepten','Bekijk wel de losse aanbiedingen of de bestaande recepten.');
}
x+=title('Niet missen · Lidl, Jumbo & AH','Relevante aanbiedingen met hartjes om direct te bewaren. Een actie is niet automatisch de goedkoopste optie.');
const focus={
lidl:['broccoli','zalm','prei'],
jumbo:['jumbo-w44-gemengdgehakt','jumbo-w44-vivera-shoarma','jumbo-w44-flespompoen','jumbo-w44-kipblokjes','jumbo-w44-dreft'],
ah:['ah-w44-pork-300','ah-w44-sprouts-500','ah-w44-plant-chicken-160','ah-w44-butternut-piece','ah-w44-cauliflower-piece','ah-w44-chicken-300']
};
for(const s of ORDER){
let wanted=offers(s).filter(o=>focus[s].includes(o.id)||(s==='lidl'&&focus.lidl.some(k=>norm(o.name).includes(k)))).slice(0,6);
x+=title(NAMES[s],wanted.length+' uitgelichte producten','<button class="button secondary small" data-goto-offers="'+s+'">Alle aanbiedingen →</button>');
if(wanted.length)x+='<div class="cards">'+wanted.map(o=>dealCard(o,s)).join('')+'</div>';
}
x+='<div class="info-banner"><strong>Vergelijk per verpakking:</strong> ingrediënten kunnen in actie zijn, maar de totale maaltijd is alleen aantoonbaar goedkoop als alle kassaprijzen en goedkopere alternatieven zijn gecontroleerd.</div>';
x+=title('Budgetbasis zonder acties','Voordelige reguliere recepten op basis van eerder waargenomen schapprijzen — geen garantie dat de prijs altijd gelijk blijft.');
const budgetRec=ORDER.flatMap(s=>recipes(s).filter(r=>r.origin!=='actie-idee'&&recipePrice(r).total!==null&&recipePrice(r).total<=10&&!offerInfo(r,s).confirmed.length&&!offerInfo(r,s).anchors.length&&!(r.ingredients||[]).some(i=>i.price_status==='folder_current')).slice(0,3));
x+=budgetRec.length?'<div class="cards">'+budgetRec.map(recipeCard).join('')+'</div>':empty('Budgetbasis wordt nog opgebouwd','Zonder betrouwbare reguliere schapprijzen kunnen we geen gerecht als structureel goedkoop bevestigen.');
x+='<div class="info-banner warning"><strong>Bronstatus:</strong> '+safe(status())+'. De prijzen zijn momentopnames; de gepubliceerde volledige kassamand is niet automatisch vandaag geverifieerd.</div>';
$('#view-vandaag').innerHTML=x;
}


function offerSortValue(o,type){
if(type==='price')return Number(o.price)||Infinity;
if(type==='saving'||type==='percent'){
 if(o.price_conflict||!Number.isFinite(o.regular_price)||o.regular_price<=o.price||Number(o.multi_buy_quantity)>1)return -1;
 const delta=o.regular_price-o.price;
 return type==='percent'?delta/o.regular_price:delta;
}
return 0;
}
function offerFiltered(o,s){
if(state.kind!=='alle'&&o.category!==state.kind)return false;
if(state.query&&!norm(o.name).includes(norm(state.query)))return false;
if(state.offerEvidence==='official'&&!(isOfficialOfferSource(o,s)&&!o.price_conflict))return false;
if(state.offerEvidence==='external'&&(isOfficialOfferSource(o,s)&&!o.price_conflict))return false;
return true;
}
function offerSorter(a,b,s){
const va=offerSortValue(a,state.offerSort),vb=offerSortValue(b,state.offerSort);
if(state.offerSort==='price')return va-vb||a.name.localeCompare(b.name,'nl');
if(state.offerSort==='saving'||state.offerSort==='percent')return vb-va||a.name.localeCompare(b.name,'nl');
const selected=new Set(chosenWatch().map(w=>w.key));
const pa=Number(selected.has(profileKey(a))),pb=Number(selected.has(profileKey(b)));
return pb-pa||Number(isOfficialOfferSource(b,s)&&!b.price_conflict)-Number(isOfficialOfferSource(a,s)&&!a.price_conflict)||
offerSortValue(b,'saving')-offerSortValue(a,'saving')||a.name.localeCompare(b.name,'nl');
}
function offerSortingControls(){
return '<div class="recipe-toolbar offer-toolbar"><label>Sorteren <select id="offer-sort">'+
[['relevant','Voor mij relevant'],['saving','Grootste € korting*'],['percent','Hoogste procent korting*'],['price','Laagste verpakkingsprijs']].map(([v,t])=>'<option value="'+v+'"'+(state.offerSort===v?' selected':'')+'>'+t+'</option>').join('')+
'</select></label><label>Broncontrole <select id="offer-evidence">'+
[['all','Alle bronnen'],['official','Officieel, zonder prijsconflict'],['external','Extern of prijsconflict']].map(([v,t])=>'<option value="'+v+'"'+(state.offerEvidence===v?' selected':'')+'>'+t+'</option>').join('')+
'</select></label><span class="muted">* Alleen vergelijkbare gewone prijs en actieprijs; bundels zonder zekere vergelijkbaarheid niet als korting gerangschikt.</span></div>';
}
function offersView(){
header('Slim besparen','Voor mij: <span style="color:#719b66">echte voordelen.</span>','Bekijk je eigen veelgekochte producten, vergelijk prijzen tussen Lidl, Jumbo en Albert Heijn, en laat de winkelkeuze aan jezelf.');
let out=auditSummary();out+='<div class="control-row"><button class="pill '+(state.offerMode==='personal'?'active':'')+'" data-offer-mode="personal">Voor mij</button><button class="pill '+(state.offerMode==='favorites'?'active':'')+'" data-offer-mode="favorites">♥ Favorieten ('+state.favorites.length+')</button><button class="pill '+(state.offerMode==='all'?'active':'')+'" data-offer-mode="all">Alle aanbiedingen</button></div>';
if(state.offerMode==='personal')out+=quickTrackedProducts()+personalHighlights()+personalComparison()+campaignHighlights('ah');
else if(state.offerMode==='favorites')out+=favoriteDashboard()+quickTrackedProducts();
else{
out+=storeControls()+kindControls(true)+offerSortingControls();
for(const s of ORDER.filter(s=>state.store==='alle'||state.store===s)){
const arr=offers(s).filter(o=>offerFiltered(o,s)).sort((a,b)=>offerSorter(a,b,s));
out+=title(NAMES[s],arr.length+' lopende prijswaarnemingen · '+Math.min(arr.length,state.pageSize[s])+' getoond');
out+=arr.length?'<div class="cards">'+arr.slice(0,state.pageSize[s]).map(o=>dealCard(o,s)).join('')+'</div>':empty('Geen actuele prijswaarneming','De bron is mogelijk nog niet bijgewerkt.');
if(arr.length>state.pageSize[s])out+='<div class="control-row"><button class="button secondary" data-more-offers="'+s+'">Nog 24 laden ('+(arr.length-state.pageSize[s])+' resterend)</button></div>';
if(s==='ah')out+=campaignHighlights(s);if(s==='lidl')out+='<div class="info-banner warning"><strong>Lidl-dekking beperkt:</strong> de productfeed is geen compleet assortiment. Controleer de <a href="https://www.lidl.nl/c/service-contact-folders/s10008124" rel="noopener noreferrer" target="_blank">officiële weekfolder</a> en Lidl Plus. Ontbrekend in de feed betekent niet dat er geen actie is. Lidl-bier wordt aanvullend gecontroleerd bij <a href="https://www.biernet.nl/bier/aanbiedingen/" target="_blank" rel="noopener noreferrer">Biernet</a> en <a href="https://www.allefolders.nl/nl/aanbiedingen/bier" target="_blank" rel="noopener noreferrer">AlleFolders</a>; die prijzen zijn externe meldingen.</div>';
}}
$('#view-aanbiedingen').innerHTML=out;
}
function allRecipes(){let found=ORDER.filter(s=>state.store==='alle'||state.store===s).flatMap(s=>recipes(s));let known=new Set(found.map(r=>r.title?.toLowerCase()));let suggestions=state.library.filter(r=>!known.has(r.title?.toLowerCase())).map(r=>({...r,store:null,origin:'bibliotheek'}));return found.concat(suggestions)}

function recipeView(){
header('Recepten & slimme acties','Lekker koken.<br><span style="color:#719b66">Acties die je écht gebruikt.</span>','Uitgewerkte ideeën en actierecepten voorop. De 40 oudere titel-geïnspireerde concepten kun je apart inschakelen. Geen van deze gerechten is door ons proefgekookt.');
let out=storeControls()+kindControls()+subtypeControls()+recipeControls();
for(const s of ORDER.filter(s=>state.store==='alle'||state.store===s)){
const all=catalog(s),found=all.filter(recipeFiltered).sort(recipeSort);
const current=all.filter(r=>offerInfo(r,s).confirmed.length).length;const anchored=all.filter(r=>offerInfo(r,s).anchors.length||offerInfo(r,s).confirmed.length).length;
const potential=all.filter(r=>offerInfo(r,s).possible.length).length;
const counts=['kip','vlees','vis','vega'].map(k=>(KINDS[k]+' '+all.filter(r=>r.category===k).length)).join(' · ');
out+=title(NAMES[s]+' recepten',counts+' · '+anchored+' recepten met gekoppeld actieproduct · '+all.filter(r=>recipePrice(r).total!==null).length+' met volledige prijsindicatie · '+potential+' vergelijkbare actie-opties');
out+='<div class="info-banner">Actiekoppelingen vereisen passende productvarianten, verpakkingen en prijzen. Andere vergelijkbare producten verschijnen alleen als mogelijke aanbieding. '+(s==='jumbo'?'Vis zonder passende aanbieding blijft gewone inspiratie.':'')+'</div>';
out+=found.length?'<div class="cards">'+found.map(recipeCard).join('')+'</div>':empty('Geen recepten voor deze filters','Wijzig je actiestatus of zoekterm om meer recepten te zien.');
}
out+='<div class="info-banner warning">De receptenbibliotheek groeit met nieuwe dagelijkse en wekelijkse gerechten. Historische prijzen worden niet als actuele prijzen getoond. De goedkoopste werkelijke kassamand kan pas worden bevestigd als álle productprijzen en verpakkingen gecontroleerd zijn.</div>';
$('#view-recepten').innerHTML=out;
}
function normalize(r){return (r.ingredients||[]).map(i=>({name:i.name||i.label||'Ingrediënt',quantity:Number(i.quantity||0),unit:i.unit||'',department:i.department||'Overig',price:typeof i.pack_price==='number'?i.pack_price:null}));}
function currentSelections(s){const ids=state.selected[s]||[];return ids.map(id=>findRecipe(s,id)).filter(Boolean)}
function findRecipe(s,id){const r=id.startsWith('library|')?state.library.find(x=>x.id===id.slice(8)):recipes(s).find(x=>x.id===id);if(r)return r;const copy=state.recipeSnapshots[s+'|'+id];return copy?{...copy,store:s,origin:'bewaarde_kopie',cost:null,macros:null,offer_links:[],offer_anchors:[],minimum_known_spend:null}:null}

function recipeKey(r){return r.store+'|'+r.id}
function savedRecipe(key){return state.savedRecipes.includes(key)}
function snapshotRecipe(s,id){
 const r=findRecipe(s,id);if(!r)return;
 state.recipeSnapshots[s+'|'+id]={id,title:r.title,category:r.category,cuisine:r.cuisine,servings:4,minutes:r.minutes,ingredients:r.ingredients,instructions:r.instructions,source_name:r.source_name,source_note:r.source_note};
}
function toggleSavedRecipe(key){
 const [s,...rest]=key.split('|'),id=rest.join('|');if(!ORDER.includes(s)||!id)return;
 const ix=state.savedRecipes.indexOf(key);
 if(ix>=0)state.savedRecipes.splice(ix,1);else{state.savedRecipes.unshift(key);snapshotRecipe(s,id)}
 save();
}
function planRecipe(key){
 const [s,...rest]=key.split('|'),id=rest.join('|');if(!ORDER.includes(s)||!findRecipe(s,id))return;
 state.selected[s]??=[];
 if(!state.selected[s].includes(id))state.selected[s].push(id);
 snapshotRecipe(s,id);save();
}
function unplanRecipe(key){
 const [s,...rest]=key.split('|'),id=rest.join('|');if(!ORDER.includes(s))return;
 state.selected[s]=(state.selected[s]||[]).filter(x=>x!==id);save();
}
function recipeSaveButton(r){
 const key=recipeKey(r),yes=savedRecipe(key);
 return '<button type="button" class="recipe-heart '+(yes?'chosen':'')+'" data-recipe-save="'+attr(key)+'" aria-pressed="'+yes+'" aria-label="'+(yes?'Verwijder '+attr(r.title)+' uit bewaarde recepten':'Bewaar '+attr(r.title)+' als recept')+'" title="'+(yes?'Verwijder bewaard recept':'Bewaar recept')+'">'+(yes?'♥':'♡')+'</button>';
}
function myRecipesView(){
 header('Jouw kookplanning','Mijn <span style="color:#719b66">recepten.</span>','Bewaarde favorieten en gekozen gerechten per supermarkt. Jij bepaalt nog steeds zelf welke winkel je bezoekt.');
 const count=ORDER.reduce((n,s)=>n+(state.selected[s]||[]).length,0);
 let out='<div class="personal-hero"><div class="personal-stat"><strong>'+state.savedRecipes.length+'</strong><span>Favoriete recepten</span></div><div class="personal-stat"><strong>'+count+'</strong><span>Geselecteerde gerechten</span></div><div class="personal-stat"><strong>'+(count*2)+'</strong><span>Eetdagen (4 porties per gerecht)</span></div></div>';
 out+='<div class="info-banner">Een geselecteerd gerecht blijft leesbaar nadat de dagfeed ververst is. Oude prijzen en verlopen aanbiedingen worden dan niet als actueel overgenomen.</div>';
 out+=title('Mijn planning','Gekozen gerechten, overzichtelijk gegroepeerd per supermarkt.');
 for(const s of ORDER){
   const list=state.selected[s]||[];
   out+='<section class="personal-plan-group"><div class="personal-group-header"><h3>'+safe(NAMES[s])+' · '+list.length+' gerechten</h3><button class="button secondary small" data-my-list="'+s+'">Boodschappenlijst →</button></div>';
   if(!list.length)out+='<p class="muted">Nog geen gerechten gekozen.</p>';
   else out+='<div class="my-recipe-list">'+list.map(id=>{
     const r=findRecipe(s,id),key=s+'|'+id;
     return '<div class="my-recipe-row"><div><strong>'+safe(r?.title||'Recept niet beschikbaar')+'</strong><small>'+safe(r?.cuisine||'')+' · 4 porties · twee dagen</small></div><div class="my-actions">'+(r?'<button class="button secondary small" data-open="'+attr(key)+'">Open</button>':'')+'<button class="button ghost small" data-unplan="'+attr(key)+'">Verwijder ×</button></div></div>';
   }).join('')+'</div>';
   out+='</section>';
 }
 out+=title('Mijn bewaarde recepten','Met één klik toevoegen aan de planning voor de betreffende supermarkt.');
 if(!state.savedRecipes.length)out+=empty('Nog geen favorieten','Klik op het hartje op een receptenkaart om het gerecht hier te bewaren.');
 else out+='<div class="cards">'+state.savedRecipes.map(key=>{
    const [s,...parts]=key.split('|'),id=parts.join('|'),r=findRecipe(s,id);
    if(!r)return '<div class="empty">Recept niet beschikbaar <button class="button secondary small" data-recipe-save="'+attr(key)+'">Verwijder</button></div>';
    return '<article class="my-saved-card"><div><div class="eyebrow">'+safe(NAMES[s])+'</div><h3>'+safe(r.title)+'</h3><p class="muted">'+safe(r.cuisine||'')+' · '+safe(r.minutes||'?')+' min · 4 porties</p></div><div class="my-saved-actions"><button class="button secondary small" data-open="'+attr(key)+'">Bekijk</button><button class="button small" data-plan-recipe="'+attr(key)+'">Kies voor mijn lijst</button>'+recipeSaveButton({...r,store:s})+'</div></article>';
 }).join('')+'</div>';
 out+='<div class="info-banner warning">Je persoonlijke recepten worden lokaal in de huidige browser bewaard. Ze synchroniseren niet automatisch tussen apparaten. De kopieën bevatten geen actuele prijzen of aanbiedingen.</div>';
 $('#view-mijn').innerHTML=out;
}
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
let x='<div class="eyebrow">'+safe(KINDS[r.category]||'Recept')+' · '+safe(NAMES[s])+'</div><h2>'+safe(r.title)+'</h2><p class="subhead">'+safe(r.cuisine||'')+' · 4 porties · '+(Number(r.minutes)||'?')+' minuten</p><div class="info-banner"><strong>Herkomst:</strong> '+safe(recipeSourceLabel(r))+(r.source_name?'<p>Brontitel of inspiratie: '+safe(r.source_name)+'</p>':'')+(r.source_note?'<p>'+safe(r.source_note)+'</p>':'')+'</div>'+(r.quality_issues?.length?'<div class="info-banner warning"><strong>Controlepunten:</strong> '+safe(r.quality_issues.join(' · '))+'</div>':'');
x+='<div class="dialog-offer-section">'+offerBadge(r);
if(matched.confirmed.length){x+='<p class="dialog-note">De volgende geldige actieproducten zijn daadwerkelijk in de ingrediënten en de prijsberekening verwerkt:</p>';
for(const item of matched.confirmed){const o=item.offer;x+='<div class="offer-detail"><strong>'+safe(o.name)+'</strong> · '+money(o.price)+' per '+safe(o.pack_label||'verpakking')+' · gebruikt voor '+safe(item.ingredient.name)+(o.member_required?' · klantenkaart nodig':'')+' · t/m '+dateNL(o.end_date)+(o.source?.url?'<br><a href="'+attr(o.source.url)+'" target="_blank" rel="noopener noreferrer">Controleer deze aanbieding ↗</a>':'')+'</div>';}
}
if(matched.anchors.length){
x+='<p class="dialog-note"><strong>Deze aanbiedingen horen echt bij de ingrediënten:</strong> '+matched.anchors.length+'. De overige ingrediënten zijn mogelijk nog niet geprijsd.</p>';
for(const x1 of matched.anchors){
 const o=x1.offer,i=x1.ingredient,priced=i.price_status==='folder_current'&&typeof i.pack_price==='number';
 x+='<div class="offer-detail"><strong>'+safe(o.name)+'</strong> · '+(priced?money(i.pack_price)+' bekende pakkosten':'bundelprijs nog niet doorgerekend')+' · '+safe(o.pack_label||'verpakking')+' · geldig t/m '+dateNL(o.end_date)+(o.promo_note?'<p class="muted">'+safe(o.promo_note)+'</p>':'')+(o.source?.url?'<a href="'+attr(o.source.url)+'" target="_blank" rel="noopener noreferrer">Bekijk officiële aanbieding ↗</a>':'')+'</div>';
}
if(matched.discount>0)x+='<div class="info-banner warning">Oude referentieprijzen zijn bekend, maar de totale besparing is pas aantoonbaar als ook de ontbrekende ingrediënten en alternatieven geprijsd zijn.</div>';
}
if(matched.possible.length){x+='<p class="dialog-note"><strong>Wel mogelijk, niet verrekend:</strong> deze aanbiedingen kunnen mogelijk bij een ingrediënt passen. Productvorm, gewicht en kassaprijs moeten nog worden gecontroleerd.</p><ul class="ingredients">'+matched.possible.map(item=>'<li>'+safe(item.offer.name)+' ('+money(item.offer.price)+' / '+safe(item.offer.pack_label||'verpakking')+')'+(item.offer.source?.url?' <a href="'+attr(item.offer.source.url)+'" rel="noopener noreferrer" target="_blank">Bron ↗</a>':'')+'</li>').join('')+'</ul>'}
if(!matched.total)x+='<p class="dialog-note">Geen actuele aanbieding aan deze ingrediënten gekoppeld.</p>';
x+='</div>';
x+='<div class="summary-tiles"><div class="summary-tile"><b>'+priceQuality(r)+'</b><span>'+safe(priceTagText(r).toUpperCase())+'</span></div><div class="summary-tile"><b>'+(m&&Number.isFinite(Number(m.protein_g))?m.protein_g+' g':'—')+'</b><span>EIWIT / PORTIE</span></div><div class="summary-tile"><b>'+(m&&Number.isFinite(Number(m.carbs_g))?m.carbs_g+' g':'—')+'</b><span>KOOLHYDRATEN / PORTIE</span></div></div>';
if(r.category==='vis')x+='<div class="info-banner">Tip: varieer met vissoorten. Zalm, haring en forel leveren omega 3; magere witvis levert vooral eiwit. Bron: <a href="https://www.voedingscentrum.nl/encyclopedie/vis" target="_blank" rel="noopener noreferrer">Voedingscentrum ↗</a>.</div>';if(r.inspiration_source?.url)x+='<p class="muted">Culinaire inspiratie: <a href="'+attr(r.inspiration_source.url)+'" target="_blank" rel="noopener noreferrer">'+safe(r.inspiration_source.name||'Receptenbron')+' ↗</a>. Dit gerecht is een eigen bewerking.</p>';if(m)x+='<p class="muted">Voedingswaarden per portie: '+safe(m.kcal)+' kcal, '+safe(m.protein_g)+' g eiwit, '+safe(m.carbs_g)+' g koolhydraten, '+safe(m.fat_g)+' g vet. '+(r.macro_status==='verified'?'Berekend':'Schatting')+'.</p>';
const priceAudit=recipePrice(r);if(priceAudit.state!=='today_confirmed')x+='<div class="info-banner warning"><strong>Prijsstatus:</strong> '+safe(priceStatusText(r))+'. '+(priceAudit.missing.length?'Niet geprijsd: '+safe(priceAudit.missing.join(' · '))+'. ':'')+'De kassaprijs is niet onafhankelijk bevestigd.</div>';if(r.nutrition_note)x+='<div class="info-banner warning"><strong>Voedingsprofiel:</strong> '+safe(r.nutrition_note)+'</div>';x+='<h3 style="margin-top:20px">Ingrediënten voor 4 porties</h3><ul class="ingredients">'+list.map((i,k)=>{const raw=r.ingredients[k];return '<li>'+safe(i.quantity)+' '+safe(i.unit)+' '+safe(i.name)+(typeof raw.pack_price==='number'&&(r.origin!=='folder-idee'||!!matched.anchored)?'<span class="muted"> · verpakkingen '+money(raw.pack_price)+(raw.price_observed_at?' · peildatum '+safe(raw.price_observed_at):'')+'</span>':' · <span class="muted">prijs onbekend</span>')+'</li>'}).join('')+'</ul>';
x+='<h3 style="margin-top:20px">Zo maak je het</h3><ol class="steps">'+steps.map(t=>'<li>'+safe(t)+'</li>').join('')+'</ol>';
x+='<div class="info-banner warning">'+(typeof r.cost?.basket_total==='number'?'Dit bedrag is gebaseerd op de gepubliceerde prijswaarnemingen; de volledige kassamand is '+(r.cost.verified_today?'die dag gecontroleerd.':'niet op dezelfde dag geverifieerd.')+' '+safe(r.cost.price_basis||''):'Voor dit bibliotheekrecept zijn nog niet alle vierportiehoeveelheden, actuele verpakkingsprijzen en macro’s gecontroleerd. Er is geen betrouwbare actuele kassaprijs.')+'</div>';
x+='<div class="dialog-actions">'+recipeSaveButton({...r,store:s})+'<button class="button" data-add="'+attr(s+'|'+id)+'">Voeg toe aan '+safe(NAMES[s])+'-lijst</button></div>';
$('#dialog-content').innerHTML=x;$('#recipe-dialog').showModal();
}
function setView(v){if(!['vandaag','aanbiedingen','recepten','lijst','mijn'].includes(v))return;state.view=v;state.kind='alle';state.subtype='alle';state.query='';history.replaceState(null,'','#'+v);render();window.scrollTo(0,0)}
function render(){clearPage();if(state.view==='vandaag')overview();if(state.view==='aanbiedingen')offersView();if(state.view==='recepten')recipeView();if(state.view==='lijst')shoppingView();if(state.view==='mijn')myRecipesView();let total=Object.values(state.selected).reduce((x,y)=>x+(y?.length||0),0);$('#nav-count').textContent=total||'';$('#saved-count').textContent=state.savedRecipes.length||'';$('#product-favorites-count').textContent=state.favorites.length||'';const st=$('#feed-status');st.textContent=status()+(state.catalog?.generated_at?' · externe actiescan '+String(state.catalog.generated_at).slice(0,10)+' (niet elke prijs geverifieerd)':' · geen externe actiescan');st.classList.toggle('warn',!state.daily?.generated_at||String(state.daily.generated_at).slice(0,10)<today())}
function copyList(s){const picks=currentSelections(s);let m=new Map();picks.forEach(r=>normalize(r).forEach(i=>{let k=i.name+'|'+i.unit;let old=m.get(k);if(!old){old={...i,quantity:0};m.set(k,old)}old.quantity+=i.quantity;m.set(k,old)}));let txt='Boodschappenmaatje · '+NAMES[s]+'\n'+picks.map(x=>'• '+x.title).join('\n')+'\n\n'+[...m.values()].map(i=>'☐ '+i.quantity+' '+i.unit+' '+i.name).join('\n');navigator.clipboard?.writeText(txt).then(()=>alert('Boodschappenlijst gekopieerd.')).catch(()=>alert(txt))}
document.addEventListener('click',e=>{const b=e.target.closest('button,a[data-view]');if(!b)return;
if(b.dataset.view){e.preventDefault();setView(b.dataset.view);return}
if(b.dataset.recipeSave){toggleSavedRecipe(b.dataset.recipeSave);if($('#recipe-dialog').open)$('#recipe-dialog').close();render();return}if(b.dataset.planRecipe){planRecipe(b.dataset.planRecipe);render();return}if(b.dataset.unplan){unplanRecipe(b.dataset.unplan);render();return}if(b.dataset.myList){state.store=b.dataset.myList;setView('lijst');return}if(b.dataset.favToggle){toggleFavorite({name:b.dataset.favName,pack_label:b.dataset.favPack,ean:b.dataset.favEan||null},b.dataset.favStore);if(state.view==='aanbiedingen')offersView();else render();return}if(b.dataset.offerMode){state.offerMode=b.dataset.offerMode;offersView();return}if(b.dataset.manageWatch){state.manageWatch=!state.manageWatch;offersView();return}if(b.dataset.openFavorites){state.offerMode='favorites';setView('aanbiedingen');return}if(b.dataset.moreOffers){state.pageSize[b.dataset.moreOffers]+=24;offersView();return}if(b.dataset.gotoOffers){state.store=b.dataset.gotoOffers;state.offerMode='all';setView('aanbiedingen');return}if(b.dataset.gotoStore){state.store=b.dataset.gotoStore;setView('recepten');return}
if(b.dataset.store){state.store=b.dataset.store;render();return}
if(b.dataset.kind){state.kind=b.dataset.kind;state.subtype='alle';render();return}if(b.dataset.subtype){state.subtype=b.dataset.subtype;render();return}
if(b.dataset.open){openRecipe(b.dataset.open);return}
if(b.dataset.add){let parts=b.dataset.add.split('|');let s=parts[0],id=parts.slice(1).join('|');state.selected[s]??=[];if(!state.selected[s].includes(id))state.selected[s].push(id);snapshotRecipe(s,id);save();$('#recipe-dialog').close();state.store=s;setView('lijst');return}
if(b.dataset.remove){unplanRecipe(state.store+'|'+b.dataset.remove);render();return}
if(b.dataset.copyList){copyList(b.dataset.copyList);return}
if(b.dataset.resetChecks){Object.keys(state.checks).filter(x=>x.startsWith(b.dataset.resetChecks+'|')).forEach(k=>delete state.checks[k]);save();render();return}
});
document.addEventListener('input',e=>{if(e.target.id==='find'){let x=e.target.value;state.query=x;let pos=e.target.selectionStart;state.view==='recepten'?recipeView():offersView();let inp=$('#find');inp.focus();inp.setSelectionRange(pos,pos)}});
document.addEventListener('change',e=>{if(e.target.matches('[data-watch-key]')){const k=e.target.dataset.watchKey;state.watchDisabled=state.watchDisabled.filter(x=>x!==k);if(!e.target.checked)state.watchDisabled.push(k);save();offersView();return}if(e.target.id==='recipe-quality'){state.recipeQuality=e.target.value;recipeView();return}if(e.target.id==='offer-category'){state.kind=e.target.value;offersView();return}if(e.target.id==='offer-sort'){state.offerSort=e.target.value;offersView();return}if(e.target.id==='offer-evidence'){state.offerEvidence=e.target.value;offersView();return}if(e.target.id==='recipe-sort'){state.sortBy=e.target.value;recipeView();return}if(e.target.id==='deal-filter'){state.dealFilter=e.target.value;recipeView();return}if(e.target.matches('[data-check]')){state.checks[e.target.dataset.check]=e.target.checked;save();e.target.closest('.list-line').querySelector('.item-name').classList.toggle('done',e.target.checked)}});
$('#dialog-close').addEventListener('click',()=>$('#recipe-dialog').close());
document.querySelector('#clock').textContent=new Date().toLocaleDateString('nl-NL',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Amsterdam'});
(async()=>{const res=await Promise.all([load('data/daily.json'),load('data/weekly.json'),load('data/library.json'),load('data/archive.json'),load('data/offers-catalog.json'),load('data/spotlight.json'),load('data/watchlist.json'),load('data/personal-prices.json'),load('data/verification.json'),load('data/supplemental-offers.json'),load('data/offer-audit.json')]);state.daily=res[0];state.weekly=res[1];state.library=Array.isArray(res[2]?.recipes)?res[2].recipes:[];state.archive=res[3];state.catalog=res[4];state.spotlight=res[5];state.watchlist=res[6];state.personalPrices=res[7];state.verification=res[8];state.supplemental=res[9];state.audit=res[10];state._offersCache.clear();state._matchCache.clear();state.view=['vandaag','aanbiedingen','recepten','lijst','mijn'].includes(location.hash.slice(1))?location.hash.slice(1):'vandaag';render()})();
})();
