/* Single source of truth for comparisons of observed prices, packs and source freshness.
   A promotion feed is not a complete regular shelf-price feed. Never synthesize a missing price. */
(function(root,factory){
 const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeObservations=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const fold=v=>String(v||'').toLocaleLowerCase('nl-NL').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const validPrice=v=>typeof v==='number'&&Number.isFinite(v)&&v>0;
 const validDay=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&!Number.isNaN(Date.parse(v+'T12:00:00Z'));
 const days=(a,b)=>validDay(a)&&validDay(b)?Math.round((Date.parse(a+'T12:00:00Z')-Date.parse(b+'T12:00:00Z'))/86400000):null;
 function pack(o){
  const raw=String(o?.pack_label||o?.name||'').toLowerCase().replace(/,/g,'.').replace(/×/g,'x');
  // A range describes variants, not an exact purchasable quantity.
  if(/\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?\s*(?:g|kg|ml|cl|l)\b/.test(raw))return null;
  const factor={ml:1,cl:10,l:1000,g:1,kg:1000};
  function result(count,size,unit,rough){
   if(!validPrice(count)||!validPrice(size))return null;
   return {amount:count*size*factor[unit]/1000,unit:['ml','cl','l'].includes(unit)?'L':'kg',pieces:count,approximate:rough};
  }
  let m=raw.match(/(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|cl|l|g|kg)\b/);
  if(!m)m=raw.match(/(\d+)\s*(?:flessen|flesjes|blikjes|blikken|stuks?)\s*(?:a|van|à)?\s*(\d+(?:\.\d+)?)\s*(ml|cl|l|g|kg)\b/);
  if(m)return result(Number(m[1]),Number(m[2]),m[3],/\bca\.?\b|circa|ongeveer|variabel/.test(raw));
  m=raw.match(/(\d+(?:\.\d+)?)\s*(ml|cl|l|g|kg)\b/);
  if(m)return result(1,Number(m[1]),m[2],/\bca\.?\b|circa|ongeveer|variabel/.test(raw));
  // Counts are a different dimension, never a guessed litre or kilogram.
  if(/\b(vaatwascapsules|vaatwastabletten|vaatwaspods|eieren)\b/.test(fold(o?.name))){
   const count=raw.match(/^(\d+)\s*(stuks?|st|stk|tabletten|capsules|pods|wasbeurten)\b/);
   if(count)return {amount:Number(count[1]),unit:count[2]==='wasbeurten'?'wasbeurt':'stuk',pieces:Number(count[1]),approximate:false};
  }
  if(/^per bos$/.test(raw))return {amount:1,unit:'bos',pieces:1,approximate:false};
  // An explicit but unmeasured count must never turn into a 1-litre or 1-kg product.
  if(/\b(stuks?|dozen|variabele|verschillende|inhoud onbekend)\b/.test(raw))return null;
  // Structured quantity is safe for manual observations without conflicting pack text.
  if(o?.status&&validPrice(o.quantity)){
   const unit=String(o.unit||'').toLowerCase();
   if(unit==='stuk')return {amount:o.quantity,unit:'stuk',pieces:o.quantity,approximate:false};
   if(unit==='ml'||unit==='g')return {amount:o.quantity/1000,unit:unit==='ml'?'L':'kg',pieces:1,approximate:false};
   if(unit==='l'||unit==='kg')return {amount:o.quantity,unit:unit==='l'?'L':'kg',pieces:1,approximate:false};
  }
  return null;
 }
 function packLabel(o){
  if(String(o?.pack_label||'').trim())return String(o.pack_label).trim();
  const p=pack(o);if(!p)return 'inhoud niet bevestigd';
  const number=x=>new Intl.NumberFormat('nl-NL',{maximumFractionDigits:3}).format(x);
  if(p.unit==='stuk')return number(p.amount)+' stuks (volgens productnaam)';
  const count=p.pieces||1,amount=p.amount/count;
  const unit=p.unit==='kg'&&amount<1?'g':p.unit==='L'&&amount<1?'ml':p.unit;
  const quantity=unit==='g'||unit==='ml'?amount*1000:amount;
  return (p.approximate?'circa ':'')+(count>1?number(count)+' × ':'')+number(quantity)+' '+unit+' (volgens productnaam)';
 }
 function unitCost(o){
  const p=pack(o);
  return p&&!p.approximate&&validPrice(o?.price)&&validPrice(p.amount)?
    {price:Math.round(o.price/p.amount*100)/100,unit:p.unit,amount:p.amount}:null;
 }
 function storeDomain(store){return {lidl:'lidl.nl',jumbo:'jumbo.com',ah:'ah.nl'}[store]||null}
 function retailerUrl(url,store){
  try{const host=new URL(url).hostname.replace(/^www\./,'').toLowerCase(),domain=storeDomain(store);
   return !!domain&&(host===domain||host.endsWith('.'+domain));
  }catch{return false}
 }
 function isDirectProductUrl(url,store){
  if(!retailerUrl(url,store))return false;
  const p=new URL(url).pathname.toLowerCase();
  if(store==='ah')return /\/producten\/product\/wi\d+/.test(p);
  if(store==='jumbo')return /\/producten\/[^?#]*[-/]\d{5,}[a-z0-9]*$/.test(p);
  return /\/p\/[^/]+/.test(p);
 }
 function inspect(o,store,today){
  if(!o||!validPrice(o.price))return null;
  const promo=!!o.start_date&&!!o.end_date&&!o.is_regular_low_price;
  const p=pack(o),unit=unitCost(o);
  const noted=String(o.checked_date||o.price_observed_at||o.observed_at||o.checked_at||'').slice(0,10);
  const age=days(today,noted);
  if(age!==null&&age<0)return null; // Future shelf observation is invalid evidence.
  const within=promo&&validDay(o.start_date)&&validDay(o.end_date)&&o.start_date<=today&&today<=o.end_date;
  const future=promo&&o.start_date>today;
  const expired=promo&&o.end_date<today;
  const officialSource=retailerUrl(o.url||o.source?.url,store);
  const direct= isDirectProductUrl(o.url||o.source?.url,store);
  const conflict=!!o.price_conflict;
  const unavailable=['discontinued','unavailable'].includes(o.availability_status);
  const reported=String(o.source_provider||'')==='PrijsProfeet'||String(o.source_provider||'')==='Biernet';
  const classified=unavailable?(o.availability_status==='discontinued'?'uit assortiment':'momenteel niet beschikbaar')+' · laatste bekende prijs':promo
    ?(within?(officialSource&&o.verified===true&&!conflict?'winkelactie':'externe actiemelding'):(future?'toekomstige actie':expired?'verlopen actie':'onzekere actiedatum'))
    :o.status==='official_discount_undated'?'korting zonder einddatum':
      o.status==='official_regular_observed'?(direct?'winkelprijswaarneming':'prijsregistratie zonder directe productverificatie'):
      o.status==='external_regular_observed'?'externe prijswaarneming':
      'prijswaarneming';
  const dated=age!==null&&age>=0;
  const fresh=!unavailable&&!o.source_scan_stale&&(within||(!promo&&dated&&age<=7));
  const status=unavailable?'niet-beschikbaar':promo&&!within?'historisch':!fresh?'oud':conflict?'conflict':officialSource&&direct?'winkelbron':'waarneming';
  const label=classified+(conflict?' · bronnen verschillen':'')+
    (!within&&dated?' · '+noted:within?' · t/m '+o.end_date:' · datum niet bevestigd');
  return {o,store,pack:p,unit,status,label,fresh,conflict,officialSource,direct,
   current:fresh,isPromotion:promo&&within&&!unavailable,checked:dated?noted:null,
   score:(unavailable?-1000:0)+(conflict?-100:0)+(within?70:0)+(!promo&&fresh?55:0)+
    (officialSource?20:0)+(direct?12:0)+(p&&!p.approximate?9:0)+
    (!promo&&!fresh?0:0)+(age!==null?Math.max(0,7-Math.max(0,age)):0)};
 }
 function matchesWatch(o,key){
  const n=fold(o?.name),p=pack(o);
  if(key==='volle_melk')return /\bvolle melk\b/.test(n)&&
    /\b(houdbare|houdbaar|uht|langlekker)\b/.test(n+' '+fold(o?.type))&&
    !/\b(verse|vers|halfvolle|halfvol|magere|mager|plantaardig|haver|geitenmelk)\b/.test(n)&&
    !!p&&p.unit==='L'&&Math.abs(p.amount-1)<0.001&&p.pieces===1&&!p.approximate;
  if(key==='skuumkoppe')return /\btexels\b/.test(n)&&/\bskuumkoppe\b/.test(n);
  if(key==='soto_boemboe')return /\b(soto|saoto)\b/.test(n)&&/\bboemboe\b/.test(n);
  if(key==='kippenpoten')return /\b(kippenbouten|kippenpoten|kipbouten|drumsticks)\b/.test(n)&&!/\b(kruiden|saus|soep)\b/.test(n);
  if(key==='sereh')return /\b(sereh|citroengras|lemongrass)\b/.test(n)&&!/\b(thee|saus|aroma|mix)\b/.test(n);
  return o?.group===key;
 }
 function choose(items){
  return [...items].sort((a,b)=>Number(b.fresh)-Number(a.fresh)||b.score-a.score||
    (a.unit&&b.unit&&a.unit.unit===b.unit.unit?a.unit.price-b.unit.price:0)||
    a.o.name.localeCompare(b.o.name,'nl'));
 }
 function apiBridge(){return {pack,packLabel,unitCost,inspect,choose};}
 function collect(store,key,records,offers,today,resolver){
  if(key&&typeof key==='object'&&key.match&&resolver){
   const result=resolver.candidates(key,store,records,offers,apiBridge(),today);
   return result.valid;
  }
  key=typeof key==='object'?key.key:key;
  const rows=[];
  for(const p of records||[])if(p.store===store&&p.group===key&&matchesWatch(p,key)){
    const x=inspect(p,store,today);if(x)rows.push(x);
  }
  for(const p of offers||[])if(matchesWatch(p,key)){
    const x=inspect(p,store,today);if(x&&x.isPromotion)rows.push(x);
  }
  return choose(rows);
 }
 function exactFavorite(observation,favorite,favorites){
  return !!favorites?.same?.(observation,favorite,favorite.store||observation.store);
 }
 function favoriteRows(store,saved,regular,active,favorites,today){
  const family=favorites?.familyKey(saved[0]);
  const candidates=[...(active||[]),...(regular||[]).filter(p=>p.store===store)]
    .filter(p=>favorites?.familyKey(p)===family);
  const seen=new Set(),out=[];
  for(const o of candidates){
   const x=inspect(o,store,today);
   if(!x||x.isPromotion===false&&o.start_date||x.status==='historisch')continue;
   const match=saved.some(f=>exactFavorite({...o,store},f,favorites));
   const id=[o.name,o.pack_label,o.price,o.status||o.source_provider||'',o.url||o.source?.url||''].join('|');
   if(seen.has(id))continue;seen.add(id);
   out.push({...x,exact:match,score:x.score+(match?40:0)});
  }
  return choose(out);
 }
 return {pack,packLabel,unitCost,inspect,matchesWatch,collect,favoriteRows,choose,retailerUrl,isDirectProductUrl,fold};
});