'use strict';
// Audits 100% of AVAILABLE imported offers; this is not independent cashier verification.
const stores=['lidl','jumbo','ah'];
const validDate=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&!Number.isNaN(Date.parse(x));
const validPrice=x=>typeof x==='number'&&Number.isFinite(x)&&x>0;
const day=()=>{const p=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());const x=Object.fromEntries(p.map(k=>[k.type,k.value]));return x.year+'-'+x.month+'-'+x.day};
function auditItem(o,store,today,fromBulkFeed=false){
 const issues=[];
 if(!o||!o.id||!o.name)issues.push('product_missing');
 if(!validPrice(o?.price))issues.push('price_missing');
 if(!validDate(o?.start_date)||!validDate(o?.end_date))issues.push('date_missing');
 else if(o.start_date>o.end_date||o.start_date>today||o.end_date<today)issues.push('date_invalid_or_expired');
 if(!o?.pack_label||/onbekend|verschillende|variabel/i.test(o.pack_label))issues.push('pack_uncertain');
 let host='';try{host=new URL(o.source?.url).hostname.toLowerCase().replace(/^www\./,'')}catch{issues.push('source_missing')}
 const domain={lidl:'lidl.nl',jumbo:'jumbo.com',ah:'ah.nl'}[store];
 const retailer=host===domain||host.endsWith('.'+domain);
 if(o?.date_estimated||o?.valid_until_estimated)issues.push('expiry_estimated');
 if(o?.price_conflict)issues.push('source_price_conflict');
 if(Number(o?.multi_buy_quantity)>1){
   if(!validPrice(o.multi_buy_price))issues.push('bundle_total_missing');
   else if(Math.abs(o.price-o.multi_buy_price)>0.02)issues.push('bundle_per_item_versus_total_check');
 }
 if(o?.loyalty_price&&!o?.loyalty_program)issues.push('loyalty_conditions_unknown');
 const invalid=issues.some(i=>['product_missing','price_missing','date_missing','date_invalid_or_expired','source_missing','source_price_conflict','bundle_total_missing'].includes(i));
 return {status:invalid?'needs_review':retailer&&!fromBulkFeed?'retailer_page_reported':'external_feed_reported',issues,retailer_url:retailer,independently_retailer_checked:retailer&&!fromBulkFeed,source_kind:fromBulkFeed?'external_bulk_with_possible_retailer_link':'direct_report'};
}
function audit(data,today=day()){
 const result={schema_version:1,generated_at:new Date().toISOString(),day:today,method:'automatic_consistency_scan_not_cashier_price_verification',stores:{},status_by_id:{},exceptions:[]};
 for(const s of stores){
  const feed=data.catalog?.stores?.[s]||{},seen=new Set(),counts={retailer_page_reported:0,external_feed_reported:0,needs_review:0};
  const bulkIds=new Set((feed.offers||[]).map(o=>o.id));
  const items=[...(feed.offers||[]),...(data.daily?.stores?.[s]?.offers||[]),...(data.spotlight?.stores?.[s]?.offers||[]),...(data.supplemental?.stores?.[s]?.offers||[])];
  const records={};let problemCount=0;
  for(const o of items){
    if(!o?.id||seen.has(o.id))continue;seen.add(o.id);
    const a=auditItem(o,s,today,bulkIds.has(o.id));records[o.id]=a;counts[a.status]++;
    if(a.issues.length){problemCount++;if(result.exceptions.length<150)result.exceptions.push({store:s,id:o.id,issues:a.issues});}
  }
  // A second listing can agree but may be copying the same retailer folder.
  // Only compare identical EAN+pack or entirely identical normalized name+pack.
  const norm=x=>String(x||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
  const groups=new Map();
  for(const [origin,entries] of [
   ['prijsprofeet',feed.offers||[]],
   ['daily',data.daily?.stores?.[s]?.offers||[]],
   ['spotlight',data.spotlight?.stores?.[s]?.offers||[]],
   ['supplemental',data.supplemental?.stores?.[s]?.offers||[]]
  ]){
   for(const offer of entries){
    if(!offer?.id||!validPrice(offer.price))continue;
    const pack=norm(offer.pack_label);
    if(!pack||/onbekend|verschillende|variabel/.test(pack))continue;
    const key=offer.ean?'ean:'+offer.ean+'|'+pack:'name:'+norm(offer.name)+'|'+pack;
    if(!groups.has(key))groups.set(key,[]);
    groups.get(key).push({origin,offer});
   }
  }
  let matchingPrices=0,differingPrices=0;
  for(const rows of groups.values()){
   if(new Set(rows.map(x=>x.origin)).size<2)continue;
   const prices=rows.map(x=>x.offer.price),agree=Math.max(...prices)-Math.min(...prices)<=0.015;
   for(const row of rows){
    const entry=records[row.offer.id];if(!entry)continue;
    entry.corrob={kind:agree?'sources_agree':'sources_disagree',count:new Set(rows.map(x=>x.origin)).size,explanation:'Same exact name/EAN and package observed in multiple feeds; these may use the same underlying store data.'};
    if(agree)matchingPrices++;else differingPrices++;
   }
  }
  result.stores[s]={cross_source_matching_records:matchingPrices,cross_source_disagreeing_records:differingPrices};
  result.status_by_id[s]=records;
  result.stores[s]={...result.stores[s],evaluated:seen.size,raw_records:items.length,by_status:counts,with_issues:problemCount,feed_status:feed.status||'missing',feed_reported_total:feed.reported_total??null,feed_imported_total:feed.imported_total??null,scope:'Records received from available sources, NOT all store discounts and NOT independently verified prices'};
 }
 return result;
}
module.exports={audit,auditItem};
if(require.main===module){
 const fs=require('node:fs'),path=require('node:path'),root=path.join(__dirname,'..','docs','data');
 const read=f=>JSON.parse(fs.readFileSync(path.join(root,f),'utf8'));
 const report=audit({catalog:read('offers-catalog.json'),daily:read('daily.json'),spotlight:read('spotlight.json'),supplemental:read('supplemental-offers.json')});
 fs.writeFileSync(path.join(root,'offer-audit.json'),JSON.stringify(report));
 for(const s of stores)console.log(s,report.stores[s].evaluated,'offers audited;',report.stores[s].with_issues,'with issues');
}
