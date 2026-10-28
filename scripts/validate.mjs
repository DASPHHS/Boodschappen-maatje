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
