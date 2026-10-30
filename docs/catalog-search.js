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
 function observation(row,store,catalog,today,pricing){
   const meta=row[5];
   const age=meta?.checked_at?(Date.parse(today+'T12:00:00Z')-Date.parse(String(meta.checked_at).slice(0,10)+'T12:00:00Z'))/86400000:Infinity;
   const pack=pricing?.pack?.({pack_label:row[2],name:row[0]}),livePack=pricing?.pack?.({pack_label:meta?.product_pack||meta?.name});
   const knownPacks=pack&&livePack&&!pack.approximate&&!livePack.approximate;
   const packConflict=!!knownPacks&&(pack.unit!==livePack.unit||Math.abs(pack.amount-livePack.amount)>.000001);
   const packVerified=!!knownPacks&&!packConflict;
   const official=packVerified&&meta?.verified_identity===true&&meta?.status==='ok'&&age>=0&&age<=1&&Number.isFinite(meta.observed_price)&&meta.observed_price>0;
   const item={name:row[0],price:official?meta.observed_price:row[1],pack_label:row[2]||'',
     pack_conflict:packConflict,product_id:row[4],semantic_evidence:row[5]||null,store,status:'external_regular_observed',
     checked_date:official?meta.checked_at.slice(0,10):catalog.source_date,
     source_provider:official?'Winkelpagina':'Checkjebon',
     source_verification:official?'retailer_product_page_checked':'published_catalog_snapshot',
     url:row[3]||catalog.source_url, source_catalog_url:catalog.source_url};
   return item;
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
   const item=observation(row,store,catalog,today,pricing);
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
 function productKey(o,store){
  const direct=o.url||o.source?.url||'';
  const raw=String(o.product_id||direct);
  const id=store==='ah'?raw.match(/wi\d+/i)?.[0]:store==='jumbo'?raw.replace(/[?#].*$/,'').match(/(\d{5,}[a-z0-9]*)$/i)?.[0]:o.product_id;
  return store+'|'+(id||o.product_id||[norm(o.name),o.pack_label||''].join('|'));
 }
 function combined(profile,store,catalog,observations,offers,pricing,resolver,today){
  const catalogRows=candidates(profile,store,catalog,pricing,resolver,today,150);
  const original=resolver?.candidates?.(profile,store,observations||[],offers||[],pricing,today).valid||[];
  // Resolve a stable retailer identity before ranking prices. A cheaper stale
  // observation of the same SKU must not defeat a newer source check.
  const byIdentity=new Map();
  const authority=x=>x.o.source_verification==='retailer_product_page_checked'&&x.checked===today?3:x.checked===today?2:1;
  for(const candidate of [...catalogRows,...original]){
   const o=candidate.o,key=productKey(o,store);
   const prior=byIdentity.get(key);
   if(!prior){byIdentity.set(key,candidate);continue;}
   const rank=authority(candidate)-authority(prior);
   const date=String(candidate.checked||'').localeCompare(String(prior.checked||''));
   if(rank>0||rank===0&&date>0){byIdentity.set(key,candidate);continue;}
   if(rank===0&&date===0&&Math.abs(o.price-prior.o.price)>.001){
    byIdentity.set(key,{...prior,conflict:true,current:false,label:'Bronprijzen verschillen; hercontrole nodig'});
   }
  }
  const out=[...byIdentity.values()];
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
    const key=productKey(x.o,store);
    if(!seen.has(key)){seen.add(key);picked.push({...x,exact:true})}
   }
  }
  return picked.sort((a,b)=>(a.unit&&b.unit&&a.unit.unit===b.unit?a.unit.price-b.unit.price:0)||a.o.price-b.o.price);
 }
 return {productKey,observation,valid,candidates,combined,compactResult,favoritePrices};
});