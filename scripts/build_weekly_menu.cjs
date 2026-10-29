#!/usr/bin/env node
/* Weekly editorially bounded rotation. No third-party recipe text is scraped.
 * No prices, offer claims, nutrition, or taste-testing are fabricated. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../docs/data');
const {format}=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit'});
const today=process.env.DATE_OVERRIDE||format.format(new Date());
if(!/^\d{4}-\d{2}-\d{2}$/.test(today)||Number.isNaN(Date.parse(today+'T12:00:00Z')))throw Error('Invalid Amsterdam-local date');
const anchor=new Date(today+'T12:00:00Z');
const monday=new Date(anchor);monday.setUTCDate(anchor.getUTCDate()-(anchor.getUTCDay()+6)%7);
const sunday=new Date(monday);sunday.setUTCDate(monday.getUTCDate()+6);
const iso=d=>d.toISOString().slice(0,10);
const start=iso(monday),end=iso(sunday);
const reference=new Date('2026-10-26T12:00:00Z');
const weekIndex=Math.floor((monday-reference)/604800000);
const data=JSON.parse(fs.readFileSync(path.join(root,'library.json'),'utf8'));
const kinds=['kip','vlees','vis','vega'],stores=['lidl','jumbo','ah'];
const eligible=data.recipes.filter(r=>r.id?.startsWith('basis-')&&
 r.quality_status==='uitgewerkt_niet_culinair_getest'&&
 r.source_status==='algemene_inspiratie_bron_geen_1_op_1_recept'&&
 r.servings===4&&Array.isArray(r.ingredients)&&r.ingredients.length>=4&&
 Array.isArray(r.instructions)&&r.instructions.length>=3&&r.inspiration_source?.url?.startsWith('https://'));
for(const kind of kinds)if(eligible.filter(r=>r.category===kind).length<2)
 throw Error('Cannot publish: fewer than two reviewed original base ideas in '+kind);
const previousPath=path.join(root,'weekly.json');
const week={
 schema_version:1,generated_at:new Date().toISOString(),week_start:start,week_end:end,
 editorial_status:'eigen_bewerkingen_niet_proefgekookt',
 notice:'Vier eigen weekideeën per supermarkt voor vier porties; gebaseerd op vooraf geselecteerde bibliotheekrecepten. Niet proefgekookt, geen overgenomen uitgeverstekst, geen actuele prijs of volledig kassabedrag bevestigd.',
 stores:{}
};
for(let si=0;si<stores.length;si++){
 const store=stores[si],recipes=[];
 for(let ci=0;ci<kinds.length;ci++){
  const kind=kinds[ci],pool=eligible.filter(r=>r.category===kind).sort((a,b)=>a.id.localeCompare(b.id));
  const src=pool[((weekIndex+si+ci)%pool.length+pool.length)%pool.length];
  recipes.push({...src,id:'week-'+start+'-'+store+'-'+kind,store,
   source_library_id:src.id,recipe_week_start:start,recipe_week_end:end,
   quality_status:'uitgewerkt_niet_culinair_getest',
   quality_issues:[...new Set([...(src.quality_issues||[]),'niet_proefgekookt'])],
   offer_anchors:[],offer_links:[],candidate_offer_links:[],
   source_note:'Eigen bewerking, niet proefgekookt. Inspiratiebron is geen 1-op-1 gereproduceerd recept. Productprijzen en productvarianten staan los van deze bereidingsinstructies.',
   cost:null,macros:null,macro_status:'niet_berekend',price_status:'onbekend'});
 }
 week.stores[store]={checked_at:new Date().toISOString(),status:'own_ideas_unverified',offers:[],recipes,
  notes:'Automatisch samengesteld uit reeds bestaande eigen ideeën. Controleer het oorspronkelijke recept en de winkelprijzen zelf.'};
}
if(process.argv.includes('--check')){
 const found=JSON.parse(fs.readFileSync(previousPath,'utf8'));
 if(found.schema_version!==1||found.week_start!==start||found.week_end!==end)throw Error('Published week is stale');
 for(const s of stores){
  const actual=found.stores?.[s]?.recipes||[];
  if(actual.length!==4||new Set(actual.map(x=>x.category)).size!==4||
    actual.some(x=>x.cost!==null||x.macros!==null||x.servings!==4))
   throw Error('Incomplete or incorrectly priced week menu for '+s);
 }
 console.log('Week menu verified: '+start+' to '+end);process.exit(0);
}
fs.writeFileSync(previousPath,JSON.stringify(week,null,2)+'\n');
console.log('Generated original week ideas: '+start+' to '+end+', 4 recipes × 3 stores (not taste-tested or priced)');
