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
const state={view:'vandaag',store:'alle',kind:'alle',query:'',daily:null,weekly:null,library:[],selected:read('bm_selected',{}),checks:read('bm_checks',{})};
function read(k,fallback){try{return JSON.parse(localStorage.getItem(k))||fallback}catch{return fallback}}
function save(){try{localStorage.setItem('bm_selected',JSON.stringify(state.selected));localStorage.setItem('bm_checks',JSON.stringify(state.checks))}catch{}}
async function load(path){try{const r=await fetch(path+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error(r.status);return await r.json()}catch{return null}}
function storeData(d,s){return (d&&d.stores&&d.stores[s])||{}}
function offers(s){return Array.isArray(storeData(state.daily,s).offers)?storeData(state.daily,s).offers.filter(o=>isOfferActive(o)):[]}
function isOfferActive(o){if(!o||typeof o.price!=='number'||!o.verified||!validdate(o.end_date)||!validdate(o.start_date))return false;return o.start_date<=today()&&o.end_date>=today()}
function recipes(s){let all=[];for(let [d,src] of [[state.daily,'dagactie'],[state.weekly,'weekinspiratie']]){let list=storeData(d,s).recipes;if(Array.isArray(list))list.forEach(r=>all.push({...r,store:s,origin:src}))}return all}
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
function kindControls(){return '<div class="control-row">'+['alle','kip','vlees','vis','vega'].map(k=>'<button class="pill '+(state.kind===k?'active':'')+'" data-kind="'+k+'">'+(KINDS[k]||'Alle soorten')+'</button>').join('')+'<input class="search" id="find" aria-label="Zoek producten of recepten" placeholder="Zoeken op naam of ingrediënt…" value="'+attr(state.query)+'"></div>'}
function featured(r){return '<div class="recipe-info"><span>4 porties</span><span>'+(Number(r.minutes)||'?')+' min</span><span>'+safe(KINDS[r.category]||'Maaltijd')+'</span></div>'}
function recipeCard(r){const id=(r.store||'library')+'|'+r.id;return '<article class="recipe-card"><div class="recipe-visual '+(r.category==='kip'?'chicken':r.category==='vis'?'fish':r.category==='vlees'?'meat':'vega')+'">'+statusTag(r)+'<span class="plate" aria-hidden="true">'+(SYMBOLS[r.category]||'🥗')+'</span></div><h3>'+safe(r.title)+'</h3><p>'+safe(r.cuisine||'Smakelijk & voedzaam')+' · '+(r.store?safe(NAMES[r.store]):'Inspiratie, nog niet per winkel geprijsd')+'</p>'+featured(r)+'<div class="recipe-bottom"><div><b>'+priceQuality(r)+'</b><small>4 porties · kassaprijs'+(r.macros?' · '+safe(r.macros.protein_g)+' g eiwit/p':' · macro’s volgen')+'</small></div><button class="button small" data-open="'+attr(id)+'">Bekijk →</button></div></article>'}
function dealCard(o,s){let cheaper=o.cheapest_alternative&&typeof o.cheapest_alternative.price==='number'&&o.cheapest_alternative.price<o.price;let alt=o.cheapest_alternative;let val=Number(o.price);return '<article class="deal-card"><div class="deal-card-top"><div>'+storePill(s)+'<h3>'+safe(o.name||'Product')+'</h3></div><span class="tag fresh">Actie gecontroleerd</span></div><div class="price-line"><span class="price">'+money(val)+'</span>'+(typeof o.regular_price==='number'&&o.regular_price>val?'<span class="oldprice">'+money(o.regular_price)+'</span>':'')+'</div><div class="deal-meta">'+safe(o.pack_label||'Verpakking onbekend')+(o.unit_price?(' · '+money(o.unit_price)+'/'+safe(o.unit||'kg')):'')+' · geldig t/m '+dateNL(o.end_date)+(o.member_required?' · klantenkaart nodig':'')+'</div>'+(cheaper?'<div class="deal-note bad">Let op: '+safe(alt.name)+' is goedkoper ('+money(alt.price)+'). Vergelijk verpakking en eenheidsprijs.</div>':alt?'<div class="deal-note">Vergeleken met '+safe(alt.name)+' ('+money(alt.price)+').</div>':'<div class="deal-note">Geen onafhankelijk vergelijkbare reguliere variant meegeleverd.</div>')+(o.source?.url?'<div class="deal-meta"><a href="'+attr(/^https:\/\//.test(o.source.url)?o.source.url:'#')+'" rel="noopener noreferrer" target="_blank">Controlebron ↗</a></div>':'')+'</article>'}
function empty(head,body){return '<div class="empty"><div class="empty-art">◌</div><strong>'+safe(head)+'</strong>'+safe(body)+'</div>'}
function overview(){
header('Jouw slimme boodschappenhulp','Wat eten we <span style="color:#719b66">deze week?</span>','Bekijk eerst alle drie de supermarkten. Kies straks zelf op basis van wat je lekker vindt.');
let x='<section class="hero"><div><div class="eyebrow" style="color:#c6e79b">GOED ETEN · SLIM KOPEN</div><h1>Meer smaak.<br><em>Minder uitgeven.</em></h1><p>Acties, nieuwe recepten en boodschappenlijsten per supermarkt. Altijd vier porties, genoeg voor twee dagen.</p></div><div class="hero-art" aria-hidden="true">✳</div></section>';
x+=title('Drie winkels, jouw keuze','Geen automatische winnaar. Bekijk per winkel wat er te koken valt.');
x+='<div class="store-grid">'+ORDER.map(s=>'<article class="store-card"><div class="store-top"><div class="store-logo">'+storeLogo(s)+safe(NAMES[s])+'</div><span class="tag">'+(storeRecipeCounts(s)?'Nieuwe recepten':'Prijscheck volgt')+'</span></div><p>'+ (storeRecipeCounts(s)?'Bekijk de nieuwe winkelrecepten en bijpassende acties.':'De eerste actuele winkelrapportage is nog niet beschikbaar.')+'</p><div class="store-metrics"><div class="metric"><b>'+offers(s).length+'</b><small>gecontroleerde deals</small></div><div class="metric"><b>'+storeRecipeCounts(s)+'</b><small>nieuwe recepten</small></div></div><button class="button full" data-goto-store="'+s+'">Bekijk '+safe(NAMES[s])+' →</button></article>').join('')+'</div>';
x+=title('Eerst zien wat lekker is','Bestaande recepten ter inspiratie, nog niet opnieuw geprijsd.','<button class="button secondary" data-view="recepten">Alle recepten →</button>');
x+='<div class="cards">'+state.library.slice(0,3).map(r=>recipeCard({...r,store:null})).join('')+'</div>';
x+='<div class="info-banner warning"><strong>Bronstatus:</strong> '+safe(status())+'. De app toont geen oude of onbevestigde aanbiedingen als actuele deal. Prijzen en macro’s verschijnen na de gecontroleerde publicatie.</div>';
$('#view-vandaag').innerHTML=x;
}
function offersView(){
header('Alle deals per supermarkt','Aanbiedingen die <span style="color:#719b66">echt tellen.</span>','Bekijk de deals van Lidl, Jumbo en Albert Heijn los van elkaar. Een actie is niet automatisch de voordeligste variant.');
let out=storeControls()+kindControls();
let any=false;
for(const s of ORDER.filter(s=>state.store==='alle'||state.store===s)){
const arr=offers(s).filter(o=>(state.kind==='alle'||o.category===state.kind)&&(!state.query||(o.name||'').toLowerCase().includes(state.query.toLowerCase()))).sort((a,b)=>a.price-b.price);
if(arr.length)any=true;
out+=title(NAMES[s],arr.length+' gecontroleerde aanbiedingen met geldige actieperiode');
out+=arr.length?'<div class="cards">'+arr.map(o=>dealCard(o,s)).join('')+'</div>':empty('Nog geen gecontroleerde aanbiedingen voor '+NAMES[s],'De actuele deals verschijnen zodra deze winkel een nieuwe geverifieerde publicatie heeft.');
}
out+='<div class="info-banner">We tonen alleen aanbiedingen met bevestigde prijs én lopende geldigheid. Een actie bij een andere winkel is geen reden om een extra winkel te bezoeken.</div>';
$('#view-aanbiedingen').innerHTML=out;
}
function allRecipes(){let found=ORDER.filter(s=>state.store==='alle'||state.store===s).flatMap(s=>recipes(s));let known=new Set(found.map(r=>r.title?.toLowerCase()));let suggestions=state.library.filter(r=>!known.has(r.title?.toLowerCase())).map(r=>({...r,store:null,origin:'bibliotheek'}));return found.concat(suggestions)}
function recipeView(){
header('Wereldkeuken op budget','Lekker koken.<br><span style="color:#719b66">Vier royale porties.</span>','Kip, vlees, vis of vega. Bekijk de recepten van elke supermarkt afzonderlijk en bepaal zelf waar je gaat winkelen.');
let out=storeControls()+kindControls();
let query=r=>(state.kind==='alle'||r.category===state.kind)&&(!state.query||(r.title+' '+(r.ingredients||[]).map(i=>i.name).join(' ')).toLowerCase().includes(state.query.toLowerCase()));
for(const s of ORDER.filter(s=>state.store==='alle'||state.store===s)){
let found=recipes(s).filter(query);
out+=title(NAMES[s]+' recepten',found.length+' nieuwe recepten specifiek voor deze winkel');
out+=found.length?'<div class="cards">'+found.map(recipeCard).join('')+'</div>':empty('Nieuwe recepten voor '+NAMES[s]+' volgen','Hier verschijnen gerechten op basis van de nieuwste acties en prijzen voor deze supermarkt.');
}
let library=state.library.filter(query);
out+=title('Extra inspiratie','40 recepten uit je bestaande collectie. Actuele winkelprijzen en macro’s ontbreken nog.');
out+='<div class="info-banner warning">Deze algemene gerechten zijn niet als actuele aanbieding of bevestigd € 10-recept gemarkeerd. Voeg ze aan de lijst van jouw gekozen supermarkt toe.</div>';
out+=library.length?'<div class="cards">'+library.map(recipeCard).join('')+'</div>':empty('Geen extra recepten gevonden','Probeer een ander filter.');
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
function openRecipe(key){let [s,id]=key.split('|');let r=s==='library'?state.library.find(x=>x.id===id):findRecipe(s,id);if(!r)return;
let list=normalize(r);let steps=Array.isArray(r.instructions)?r.instructions:typeof r.instructions==='string'?r.instructions.split(/[.;]\s+/):[];
let m=r.macros;let x='<div class="eyebrow">'+safe(KINDS[r.category]||'Recept')+' · '+safe(s==='library'?'Algemene inspiratie':NAMES[s])+'</div><h2>'+safe(r.title)+'</h2><p class="subhead">'+safe(r.cuisine||'')+' · 4 porties · '+(Number(r.minutes)||'?')+' minuten</p>';
x+='<div class="summary-tiles"><div class="summary-tile"><b>'+priceQuality(r)+'</b><span>KASSABEDRAG</span></div><div class="summary-tile"><b>'+(m&&Number.isFinite(Number(m.protein_g))?m.protein_g+' g':'—')+'</b><span>EIWIT / PORTIE</span></div><div class="summary-tile"><b>'+(m&&Number.isFinite(Number(m.carbs_g))?m.carbs_g+' g':'—')+'</b><span>KOOLHYDRATEN / PORTIE</span></div></div>';
if(m)x+='<p class="muted">Voedingswaarden per portie: '+safe(m.kcal)+' kcal, '+safe(m.protein_g)+' g eiwit, '+safe(m.carbs_g)+' g koolhydraten, '+safe(m.fat_g)+' g vet. '+(r.macro_status==='verified'?'Berekend':'Schatting')+'.</p>';
x+='<h3 style="margin-top:20px">Ingrediënten voor 4 porties</h3><ul class="ingredients">'+list.map(i=>'<li>'+safe(i.quantity)+' '+safe(i.unit)+' '+safe(i.name)+'</li>').join('')+'</ul>';
x+='<h3 style="margin-top:20px">Zo maak je het</h3><ol class="steps">'+steps.map(t=>'<li>'+safe(t)+'</li>').join('')+'</ol>';
x+='<div class="info-banner warning">'+(typeof r.cost?.basket_total==='number'?'Kosten op basis van de gepubliceerde prijsfeed. Controleer geldigheid en beschikbaarheid.':'Actuele winkel- en verpakkingsprijzen ontbreken nog. Dit is geen geverifieerd € 10-recept.')+'</div>';
x+='<div class="dialog-actions">'+(s==='library'?ORDER.map(ss=>'<button class="button secondary small" data-add="'+attr(ss+'|library|'+id)+'">Voeg toe bij '+safe(NAMES[ss])+'</button>').join(''):'<button class="button" data-add="'+attr(s+'|'+id)+'">Voeg toe aan '+safe(NAMES[s])+'-lijst</button>')+'</div>';
$('#dialog-content').innerHTML=x;$('#recipe-dialog').showModal();
}
function setView(v){if(!['vandaag','aanbiedingen','recepten','lijst'].includes(v))return;state.view=v;state.kind='alle';state.query='';history.replaceState(null,'','#'+v);render();window.scrollTo(0,0)}
function render(){clearPage();if(state.view==='vandaag')overview();if(state.view==='aanbiedingen')offersView();if(state.view==='recepten')recipeView();if(state.view==='lijst')shoppingView();let total=Object.values(state.selected).reduce((x,y)=>x+(y?.length||0),0);$('#nav-count').textContent=total||'';const st=$('#feed-status');st.textContent=status();st.classList.toggle('warn',!state.daily?.generated_at||String(state.daily.generated_at).slice(0,10)<today())}
function copyList(s){const picks=currentSelections(s);let m=new Map();picks.forEach(r=>normalize(r).forEach(i=>{let k=i.name+'|'+i.unit;let old=m.get(k);if(!old){old={...i,quantity:0};m.set(k,old)}old.quantity+=i.quantity;m.set(k,old)}));let txt='Boodschappenmaatje · '+NAMES[s]+'\n'+picks.map(x=>'• '+x.title).join('\n')+'\n\n'+[...m.values()].map(i=>'☐ '+i.quantity+' '+i.unit+' '+i.name).join('\n');navigator.clipboard?.writeText(txt).then(()=>alert('Boodschappenlijst gekopieerd.')).catch(()=>alert(txt))}
document.addEventListener('click',e=>{const b=e.target.closest('button,a[data-view]');if(!b)return;
if(b.dataset.view){e.preventDefault();setView(b.dataset.view);return}
if(b.dataset.gotoStore){state.store=b.dataset.gotoStore;setView('recepten');return}
if(b.dataset.store){state.store=b.dataset.store;render();return}
if(b.dataset.kind){state.kind=b.dataset.kind;render();return}
if(b.dataset.open){openRecipe(b.dataset.open);return}
if(b.dataset.add){let parts=b.dataset.add.split('|');let s=parts[0],id=parts.slice(1).join('|');state.selected[s]??=[];if(!state.selected[s].includes(id))state.selected[s].push(id);save();$('#recipe-dialog').close();state.store=s;setView('lijst');return}
if(b.dataset.remove){let s=state.store;state.selected[s]=(state.selected[s]||[]).filter(k=>k!==b.dataset.remove);save();render();return}
if(b.dataset.copyList){copyList(b.dataset.copyList);return}
if(b.dataset.resetChecks){Object.keys(state.checks).filter(x=>x.startsWith(b.dataset.resetChecks+'|')).forEach(k=>delete state.checks[k]);save();render();return}
});
document.addEventListener('input',e=>{if(e.target.id==='find'){let x=e.target.value;state.query=x;let pos=e.target.selectionStart;state.view==='recepten'?recipeView():offersView();let inp=$('#find');inp.focus();inp.setSelectionRange(pos,pos)}});
document.addEventListener('change',e=>{if(e.target.matches('[data-check]')){state.checks[e.target.dataset.check]=e.target.checked;save();e.target.closest('.list-line').querySelector('.item-name').classList.toggle('done',e.target.checked)}});
$('#dialog-close').addEventListener('click',()=>$('#recipe-dialog').close());
document.querySelector('#clock').textContent=new Date().toLocaleDateString('nl-NL',{weekday:'long',day:'numeric',month:'long',timeZone:'Europe/Amsterdam'});
(async()=>{const res=await Promise.all([load('data/daily.json'),load('data/weekly.json'),load('data/library.json')]);state.daily=res[0];state.weekly=res[1];state.library=Array.isArray(res[2]?.recipes)?res[2].recipes:[];state.view=['vandaag','aanbiedingen','recepten','lijst'].includes(location.hash.slice(1))?location.hash.slice(1):'vandaag';render()})();
})();
