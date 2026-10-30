/* Published shelf-price catalog: source is Checkjebon public open data.
 * External evidence only. Search is exact-token + attribute constrained. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeCatalogSearch=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const norm=x=>String(x||'').toLocaleLowerCase('nl-NL').normalize('NFD')
   .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const token=(text,t)=>(' '+norm(text)+' ').includes(' '+norm(t)+' ');
 function valid(c,day){
  if(!c||c.schema_version!==1||!c.stores||!/^\d{4}-\d\d-\d\d$/.test(c.source_date||''))return false;
  const age=Math.round((Date.parse(day+'T12:00:00Z')-Date.parse(c.source_date+'T12:00:00Z'))/86400000);
  return age>=0&&age<=3;
 }
 const indexes=new WeakMap();
 function searchIndex(catalog,store){
  let stores=indexes.get(catalog);if(!stores){stores=new Map();indexes.set(catalog,stores)}
  if(stores.has(store))return stores.get(store);
  const words=new Map(),normalized=new Map(),memo=new Map();
  for(const row of catalog.stores?.[store]||[]){
   if(!Array.isArray(row)||typeof row[0]!=='string')continue;
   const name=norm(row[0]);normalized.set(row,name);
   for(const word of new Set(name.split(' '))){if(!words.has(word))words.set(word,[]);words.get(word).push(row)}
  }
  const index={words,normalized,memo};stores.set(store,index);return index;
 }
 function candidates(profile,store,catalog,pricing,resolver,today,limit=120){
  if(!valid(catalog,today)||profile?.requires_specific_variant)return [];
  const rule=profile?.match||{},all=rule.all||[],any=rule.any||[],none=rule.none||[];
  if(!all.length&&!any.length)return [];
  const index=searchIndex(catalog,store);
  const cacheKey=JSON.stringify([profile,today]);
  if(index.memo.has(cacheKey))return index.memo.get(cacheKey).slice(0,limit);
  const needed=all.flatMap(x=>norm(x).split(' ')).filter(Boolean);
  const lists=needed.map(x=>index.words.get(x)||[]);
  const rows=lists.length?lists.reduce((a,b)=>a.length<=b.length?a:b):
   [...new Set(any.flatMap(x=>index.words.get(norm(x).split(' ')[0])||[]))];
  const required=all.map(norm),alternatives=any.map(norm),excluded=none.map(norm);
  const found=[];
  for(const row of rows){
   if(!Array.isArray(row)||typeof row[0]!=='string'||!Number.isFinite(row[1]))continue;
   const name=row[0];
   const text=' '+index.normalized.get(row)+' ';
   const contains=x=>text.includes(' '+x+' ');
   if(required.some(x=>!contains(x))||alternatives.length&&!alternatives.some(contains)||excluded.some(contains))continue;
   const item={name,price:row[1],pack_label:row[2]||'',
     product_id:row[4],store,status:'external_regular_observed',
     checked_date:catalog.source_date,
     source_provider:'Checkjebon',
     source_verification:'published_catalog_snapshot',
     url:row[3]||catalog.source_url, source_catalog_url:catalog.source_url};
   const match=resolver.matching(item,profile,pricing);
   if(match.status!=='match')continue;
   const check=pricing.inspect(item,store,today);
   if(!check||!check.current)continue;
   found.push({...check,match,score:check.score+45});
  }
  // Cheapest comparable unit cost, then cheapest per purchase only when no
  // comparable quantity exists. Every displayed price retains its exact pack.
  found.sort((a,b)=>{
   const ua=a.unit,ub=b.unit;
   if(ua&&ub&&ua.unit===ub.unit)return ua.price-ub.price||a.o.price-b.o.price;
   if(ua&&!ub)return -1;
   if(ub&&!ua)return 1;
   return a.o.price-b.o.price||a.o.name.localeCompare(b.o.name,'nl');
  });
  index.memo.set(cacheKey,found);
  return found.slice(0,limit);
 }
 function combined(profile,store,catalog,observations,offers,pricing,resolver,today){
  const catalogRows=candidates(profile,store,catalog,pricing,resolver,today,150);
  const original=resolver?.candidates?.(profile,store,observations||[],offers||[],pricing,today).valid||[];
  // A matching current catalog product overrides an older, manually entered
  // third-party price for the same retailer product link/ID, not a proven official
  // retailer fetch. This fixes AH UHT 0.99 vs 1.29 for the exact same SKU.
  const indexedLinks=new Set(catalogRows.map(x=>x.o.url).filter(Boolean));
  const seen=new Set(),out=[];
  for(const candidate of [...catalogRows,...original]){
    const old=candidate.o;
    if(indexedLinks.has(old.url)&&old.source_provider!=='Checkjebon'&&
       old.source_verification!=='retailer_product_page_checked')continue;
    const key=old.url||[old.name,old.pack_label,old.price].join('|');
    if(seen.has(key))continue;seen.add(key);
    out.push(candidate);
  }
  out.sort((a,b)=>Number(b.current)-Number(a.current)||
    Number(b.o.source_verification==='retailer_product_page_checked')-
    Number(a.o.source_verification==='retailer_product_page_checked')||
    Number(b.o.source_provider==='Checkjebon')-Number(a.o.source_provider==='Checkjebon')||
    (a.unit&&b.unit&&a.unit.unit===b.unit.unit?a.unit.price-b.unit.price:0)||
    a.o.price-b.o.price);
  return out;
 }
 function compactResult(rows){
  if(!rows.length)return null;
  const x=rows[0],pack=x.pack;
  return {product:x.o.name,price:x.o.price,unit:x.unit,pack:x.o.pack_label,
    source:x.o.source_provider||x.o.status,url:x.o.url,date:x.checked,status:x.status};
 }
 function favoritePrices(store,saved,catalog,pricing,resolver,favorites,today){
  if(!valid(catalog,today))return [];
  const picked=[],seen=new Set();
  for(const f of saved||[]){
   const raw=norm(f.name).replace(/^(ah|jumbo|lidl|albert heijn)\s+/,'')
    .replace(/\b\d+\s*x\s*\d+\s*(ml|cl|l|g|kg)\b/g,'')
    .replace(/\b\d+\s*(ml|cl|l|g|kg)\b/g,'').trim();
   const words=raw.split(' ').filter(x=>x.length>1&&!/^\d+$/.test(x));
   if(!words.length)continue;
   const profile={match:{all:words}};
   for(const x of candidates(profile,store,catalog,pricing,resolver,today,100)){
    if(!favorites?.same({...x.o,store},f,store))continue;
    const key=x.o.url||[x.o.name,x.o.pack_label].join('|');
    if(!seen.has(key)){seen.add(key);picked.push({...x,exact:true})}
   }
  }
  return picked.sort((a,b)=>(a.unit&&b.unit&&a.unit.unit===b.unit?a.unit.price-b.unit.price:0)||a.o.price-b.o.price);
 }
 return {valid,candidates,combined,compactResult,favoritePrices};
});