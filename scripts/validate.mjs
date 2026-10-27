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
