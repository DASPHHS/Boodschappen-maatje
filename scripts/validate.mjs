import fs from 'node:fs';
for(const f of ['daily','weekly']){
const d=JSON.parse(fs.readFileSync('docs/data/'+f+'.json','utf8'));
if(d.schema_version!==1||!d.stores||typeof d.stores!=='object')throw Error(f+': ongeldig schema');
for(const s of ['lidl','jumbo','ah']){
let st=d.stores[s];if(!st||!Array.isArray(st.offers)||!Array.isArray(st.recipes))throw Error(f+': ontbreekt '+s);
for(const offer of st.offers){
if(typeof offer.price!=='number'||!offer.start_date||!offer.end_date)throw Error(f+': onvolledige aanbieding '+s);
if(offer.verified!==true)console.warn(f+': aanbod niet geverifieerd: '+offer.name);
}
for(const r of st.recipes){
if(!r.id||!r.title||!Array.isArray(r.ingredients)||r.servings!==4)throw Error(f+': onvolledig recept '+s);
}
}
console.log(f+': schema en drie winkels aanwezig');
}
const lib=JSON.parse(fs.readFileSync('docs/data/library.json','utf8'));
if(!Array.isArray(lib.recipes)||lib.recipes.length<10)throw Error('receptenbibliotheek ontbreekt');
console.log('Receptenbibliotheek:',lib.recipes.length);

const archive=JSON.parse(fs.readFileSync('docs/data/archive.json','utf8'));
if(archive.schema_version!==1)throw Error('archief-schema ontbreekt');
for(const s of ['lidl','jumbo','ah'])if(!Array.isArray(archive.stores?.[s]))throw Error('archief ontbreekt '+s);
console.log('Archief per winkel beschikbaar');

const daily=JSON.parse(fs.readFileSync('docs/data/daily.json','utf8'));
for(const s of ['lidl','jumbo','ah']){
for(const r of daily.stores[s].recipes){
for(const link of r.offer_links||[]){
const o=daily.stores[s].offers.find(x=>x.id===link.offer_id);
const ingredient=r.ingredients.find(x=>x.name===link.ingredient_name);
if(!o||!o.verified||!ingredient||ingredient.price_status!=='folder_current'||link.match_type!=='exact')throw Error('onjuiste actieprijs-receptkoppeling: '+s+' '+r.id);
}
}
}
const counts={};for(const r of lib.recipes)counts[r.category]=(counts[r.category]||0)+1;
for(const k of ['kip','vlees','vis','vega'])if((counts[k]||0)<10)throw Error('te weinig recepten in categorie '+k);
console.log('Actiekoppelingen en minstens tien bibliotheekrecepten per hoofdgroep gecontroleerd');

const feed=JSON.parse(fs.readFileSync('docs/data/offers-catalog.json','utf8'));
if(feed.schema_version!==1)throw Error('Schema actiecatalogus ontbreekt');
for(const name of ['lidl','jumbo','ah']){
const shop=feed.stores?.[name];
if(!shop||!Array.isArray(shop.offers))throw Error('Actiecataloog onvolledig: '+name);
for(const o of shop.offers){
if(!o.id||!o.name||typeof o.price!=='number'||!o.source?.url||!o.start_date||!o.end_date)throw Error('Ongeldige actierij '+name);
if(o.verified===true)throw Error('Externe niet-onafhankelijke actie onterecht geverifieerd');
}
}
console.log('Brede promotiecatalogus gecontroleerd');

const spotlight=JSON.parse(fs.readFileSync('docs/data/spotlight.json','utf8'));
for(const s of ['lidl','jumbo','ah']){
  const st=spotlight.stores[s];
  if(!st||!Array.isArray(st.offers)||!Array.isArray(st.recipes))throw Error('spotlight winkel ontbreekt '+s);
  const byId=new Map(st.offers.map(x=>[x.id,x]));
  for(const recipe of st.recipes){
    const attached=recipe.offer_anchors?.length?recipe.offer_anchors:(recipe.offer_anchor_id?[{offer_id:recipe.offer_anchor_id,ingredient_name:recipe.offer_anchor_name,role:'eiwitbron'}]:[]);
    for(const link of attached){
      const offer=byId.get(link.offer_id);
      const ing=recipe.ingredients.find(i=>i.name===link.ingredient_name);
      if(!offer||!ing||ing.name!==offer.name)throw Error('FOUTE product-koppeling '+recipe.id);
      if(link.role==='eiwitbron'&&offer.category!==recipe.category)throw Error('onjuiste eiwitcategorie '+recipe.id);
      if(link.role==='groente'&&offer.category!=='groente')throw Error('onjuiste groentecategorie '+recipe.id);
      if(typeof offer.price!=='number')throw Error('Niet geprijsd actieproduct als bevestigd gekoppeld '+recipe.id);
    }
    if(recipe.cost?.basket_total!==undefined&&recipe.cost!==null)
      throw Error('prijs onbevestigd maar aanwezig '+recipe.id);
    const vg=recipe.ingredients.filter(i=>i.department==='Groente & fruit').reduce((n,i)=>n+i.quantity,0);
    if(vg<1200||recipe.servings!==4)throw Error('porties/groente onjuist '+recipe.id);
  }
}
console.log('Alle folderrecepten hebben exact aanwezig actie-hoofdproduct, voldoende groenten en geen verzonnen prijs');

const spotlight2=JSON.parse(fs.readFileSync('docs/data/spotlight.json','utf8'));
for(const r of spotlight2.stores.jumbo.recipes){
const known=r.ingredients.filter(i=>typeof i.pack_price==='number').reduce((n,i)=>n+i.pack_price,0);
if(Math.abs(known-r.minimum_known_spend)>0.01)throw Error('prijs-ondergrens verkeerd '+r.id);
if(known>10&&r.budget_feasibility!=='budget_above_10_even_without_remaining_ingredients')throw Error('onhaalbaar budget niet gemarkeerd '+r.id);
}
console.log('Bekende verpakkingsprijzen en budget-ondergrenzen sluiten aan');

const promo=JSON.parse(fs.readFileSync('docs/data/spotlight.json','utf8'));
for(const [store,v] of Object.entries(promo.stores)){
 const byId=new Map(v.offers.map(o=>[o.id,o]));
 for(const r of v.recipes){
  for(const l of r.offer_anchors||[]){
   const o=byId.get(l.offer_id),i=r.ingredients.find(i=>i.name===l.ingredient_name);
   if(!o||!i||i.name!==o.name)throw Error('Onjuiste actiekoppeling '+r.id+' -> '+l.offer_id);
  }
  const known=r.ingredients.reduce((n,i)=>n+(typeof i.pack_price==='number'?i.pack_price:0),0);
  if(typeof r.minimum_known_spend==='number'&&Math.abs(known-r.minimum_known_spend)>.015)throw Error('Pakketprijzen komen niet overeen '+r.id);
 }
}
const stamp=promo.stores.jumbo.recipes.find(r=>r.id==='jumbo-gehakt-boerenkool');
if(!stamp||stamp.offer_anchors?.length!==3||!stamp.ingredients.some(i=>/stamppotaardappelen/i.test(i.name)))throw Error('Boerenkoolactie of aardappel ontbreekt');
console.log('Recepten en meerdere exact gekoppelde actieproducten gevalideerd');

const library2=JSON.parse(fs.readFileSync('docs/data/library.json','utf8'));
const seenRecipes=new Set();
for(const r of library2.recipes){
 if(seenRecipes.has(r.id))throw Error('Dubbel recept '+r.id);
 seenRecipes.add(r.id);
 if(r.servings!==4||!Array.isArray(r.ingredients)||!Array.isArray(r.instructions))throw Error('Onvolledig basisrecept '+r.id);
 if(r.id.startsWith('basis-')){
  const vegetables=r.ingredients.filter(i=>i.department==='Groente & fruit'&&i.unit==='g').reduce((n,i)=>n+i.quantity,0);
  if(vegetables<1200)throw Error('Te weinig groente '+r.id);
  if(r.cost?.basket_total!==undefined||r.macros!==undefined)throw Error('Niet-berekende basisrecepten bevatten fictieve prijs/macro '+r.id);
  if(!/^https:\/\//.test(r.inspiration_source?.url||''))throw Error('Bron ontbreekt '+r.id);
 }
}
console.log('Receptenbibliotheek: '+library2.recipes.length+' recepten, nieuwe gerechten met bron en groentecontrole');

const sources=JSON.parse(fs.readFileSync('docs/data/daily.json','utf8'));
let externalCount=0;
for(const [s,d] of Object.entries(sources.stores)){
 for(const o of d.offers){
  if(!/^https:\/\//.test(o.source?.url||''))throw Error('Ongeldige of ontbrekende aanbiedingbron '+s+' '+o.id);
  const u=new URL(o.source.url);
  const h=u.hostname.toLowerCase().replace(/^www\./,'');
  const official=s==='lidl'?(h==='lidl.nl'||h.endsWith('.lidl.nl')):s==='jumbo'?(h==='jumbo.com'||h.endsWith('.jumbo.com')):(h==='ah.nl'||h.endsWith('.ah.nl'));
  if(o.verified===true&&!official)externalCount++;
 }
}
console.warn('Acties met verified-flag maar zonder officiële winkelbron (UI markeert als extern):',externalCount);

const ahSpot=JSON.parse(fs.readFileSync('docs/data/spotlight.json','utf8')).stores.ah;
const ahRecipes=ahSpot.recipes.filter(r=>r.id.startsWith('ah-w44-'));
if(ahRecipes.length<10)throw Error('Ontbrekende AH Bonusrecepten');
for(const r of ahRecipes){
 const known=r.ingredients.reduce((n,i)=>n+(typeof i.pack_price==='number'?i.pack_price:0),0);
 if(Math.abs(known-r.minimum_known_spend)>0.01)throw Error('AH kosten onjuist '+r.id);
 if(r.cost!==null||r.macros!==null)throw Error('Ongeverifieerd AH recept geprijsd '+r.id);
 const main=r.ingredients.filter(i=>['Eiwitbronnen','Vega & peulvruchten'].includes(i.department)).reduce((n,i)=>n+(i.unit==='g'?i.quantity:0),0);
 if(main<600)throw Error('AH eiwitbron onvoldoende '+r.id);
}
console.log('AH Bonus inclusief exacte actiekoppelingen gevalideerd');

const ev=JSON.parse(fs.readFileSync('docs/data/verification.json','utf8'));
if(ev.schema_version!==1||ev.source_audit?.length<9)throw Error('Broncontrolematrix ontbreekt');
for(const [s,entries] of Object.entries(ev.reviews)){
 for(const [id,info] of Object.entries(entries)){
  const offer=spotlight.stores[s].offers.find(o=>o.id===id);
  if(!offer)throw Error('Geen aanbieding bij broncheck '+id);
  if(info.listed_price!==offer.price)throw Error('Gepubliceerde prijs verschilt van broncheck '+id);
  if(!Array.isArray(info.checks)||!info.checks.length)throw Error('Geen broncheckregels '+id);
 }
}
const dreft=spotlight.stores.jumbo.offers.find(o=>o.id==='jumbo-w44-dreft');
if(!dreft||dreft.price!==37.98||dreft.pack_label!=='5 × 25 capsules = 125 capsules'||Math.abs(dreft.unit_price-0.30384)>0.0001)throw Error('Dreft 2+3 bundel onjuist');
const kiwi=spotlight.stores.jumbo.offers.find(o=>o.id==='jumbo-w44-kiwi');
if(!kiwi||Math.abs(kiwi.unit_price-kiwi.price/.75)>0.001)throw Error('Kiwi kiloprijs onjuist');
console.log('Broncontroles, bundels en eenheidsprijzen consistent');
