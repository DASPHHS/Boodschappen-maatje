/* Shared, deterministic product search. No keyword-based equivalence claims. */
(function(root){'use strict';
const norm=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
const categories=[['Vaatwas',/vaatwas|dishwash/],['Wasgoed',/wasmiddel|wasverzachter|waspoeder|wasgel|wasbeurt|pods|wascapsule|geurbooster/],['Papier',/toiletpapier|keukenrol|zakdoek/],['Haarverzorging',/shampoo|conditioner|haar/],['Mondverzorging',/tandpasta|tandenborstel|mondwater/],['Schoonmaak',/reiniger|schoonmaak|bleek|ontkalker/],['Koffie',/koffie|espresso|coffee|cappuccino/],['Zuivel & eieren',/kwark|skyr|yoghurt|melk|eieren|kaas/],['Groente & fruit',/spinazie|boerenkool|broccoli|groente|banaan|bessen|appel|tomaat|paprika/],['Vlees, vis & vega',/kip|gehakt|rookworst|zalm|tonijn|tofu|vega/]];
function category(name){return categories.find(([,rx])=>rx.test(norm(name)))?.[0]||'Overig';}
function day(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s||''))return null;const d=new Date(s+'T12:00:00Z');return Number.isFinite(+d)&&d.toISOString().slice(0,10)===s?s:null;}
function status(start,end,today){start=day(start);end=day(end);if(end&&end<today)return 'expired';if(start&&start>today)return 'upcoming';if(!start||!end||start>end)return 'unknown';return 'active';}
function measure(name,q,unit){
 const text=String(name).toLowerCase().replace(/,/g,'.');let m;
 if(/vaatwas/.test(text)&&(m=text.match(/(\d+)\s*(?:tabletten|tabs|capsules|stuks)/)))return {amount:+m[1],unit:'tablet'};
 if(/wasmiddel|waspoeder|wasgel|wasverzachter|pods|wascapsule|geurbooster/.test(text)&&(m=text.match(/(\d+)\s*(?:wasbeurten|wasbeurt|wassen)/)))return {amount:+m[1],unit:'wasbeurt'};
 if(/toiletpapier/.test(text)&&(m=text.match(/(\d+)\s*(?:rollen|rol)\s*(?:x|van)\s*(\d+)\s*(?:vellen|vel)/)))return {amount:+m[1]*+m[2],unit:'vel'};
 if(/toiletpapier/.test(text))return null;
 if(/vaatwas|wasmiddel|waspoeder|wasgel|wasverzachter|pods|wascapsule|geurbooster/.test(text))return null;
 if(!(Number(q)>0))return null;
 if(unit==='g')return {amount:Number(q)/1000,unit:'kg'};
 if(unit==='ml')return {amount:Number(q)/(/shampoo|conditioner/.test(text)?100:1000),unit:/shampoo|conditioner/.test(text)?'100 ml':'liter'};
 if(unit==='st')return {amount:Number(q),unit:'stuk'};return null;
}
const positive=x=>Number.isFinite(Number(x))&&Number(x)>0;
function catalog(snapshot,today){const out=[];
 for(const [store,data] of Object.entries(snapshot.stores||{})){
 for(const r of data.ordinary||[]){const [name,price,q,unit,url]=r;if(!positive(price))continue;out.push(make({name,price:+price,q,unit,url,store,state:'regular',packages:1}));}
 for(const r of data.promotions||[]){const [name,price,q,unit,previous,k,bundle,type,end,url,loyalty,start]=r;
 if(!positive(price))continue;const state=status(start,end,today);if(state!=='active')continue;
 const multi=Number.isInteger(+k)&&+k>=2&&positive(bundle);
 const ambiguous=!multi&&/gratis|multi|bundle|\d\s*voor|one.plus|two.for|1\s*\+\s*1/.test(String(type).toLowerCase());
 if(ambiguous)continue;
 out.push(make({name,price:multi?+bundle:+price,q,unit,url,store,state,packages:multi?+k:1,previous:positive(previous)?+previous:null,loyalty:!!loyalty,start,end,type}));}
 }
 function make(x){const m=measure(x.name,x.q,x.unit);const previous=x.previous*x.packages;return {...x,category:category(x.name),search:norm(x.name),measure:m,unitPrice:m?x.price/(m.amount*x.packages):null,discount:previous>x.price?100*(previous-x.price)/previous:null};}
 const seen=new Map();for(const x of out){const id=[x.store,x.url||x.search,x.q,x.unit,x.packages,x.state,x.loyalty].join('|');if(!seen.has(id)||seen.get(id).price>x.price)seen.set(id,x);}return [...seen.values()];}
function search(rows,{q='',brand='',store='',cat='',sale=false,loyalty=false,minDiscount=0,sort='relevance'}={}){
 const terms=norm(q).split(' ').filter(Boolean);const aliases={vaatwastabletten:['vaatwas','tablet'],wasmiddel:['wasmiddel'],kipfilet:['kipfilet']};const tokens=terms.flatMap(t=>aliases[t]||[t]);
 const results=rows.filter(x=>tokens.every(t=>x.search.includes(t))&&(!brand||x.search.includes(norm(brand)))&&(!store||x.store===store)&&(!cat||x.category===cat)&&(!sale||x.state==='active')&&(!x.loyalty||loyalty)&&(!minDiscount||(x.discount||0)>=minDiscount));
 results.sort((a,b)=>sort==='price'?a.price-b.price:sort==='unit'?String(a.measure?.unit||'zz').localeCompare(b.measure?.unit||'zz')||(a.unitPrice??Infinity)-(b.unitPrice??Infinity):sort==='discount'?(b.discount||0)-(a.discount||0):a.search.localeCompare(b.search));return results;}
const api={norm,category,day,status,measure,catalog,search};root.BMDeals=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
