'use strict';
// Audits 100% of AVAILABLE imported offers; this is not independent cashier verification.
const stores=['lidl','jumbo','ah'];
const validDate=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&!Number.isNaN(Date.parse(x));
const validPrice=x=>typeof x==='number'&&Number.isFinite(x)&&x>0;
const day=()=>{const p=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());const x=Object.fromEntries(p.map(k=>[k.type,k.value]));return x.year+'-'+x.month+'-'+x.day};
function auditItem(o,store,today){
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
 return {status:invalid?'needs_review':retailer?'retailer_page_reported':'external_feed_reported',issues,retailer_url:retailer};
}
function audit(data,today=day()){
 const result={schema_version:1,generated_at:new Date().toISOString(),day:today,method:'automatic_consistency_scan_not_cashier_price_verification',stores:{},status_by_id:{},exceptions:[]};
 for(const s of stores){
  const feed=data.catalog?.stores?.[s]||{},seen=new Set(),counts={retailer_page_reported:0,external_feed_reported:0,needs_review:0};
  const items=[...(feed.offers||[]),...(data.daily?.stores?.[s]?.offers||[]),...(data.spotlight?.stores?.[s]?.offers||[]),...(data.supplemental?.stores?.[s]?.offers||[])];
  const records={};let problemCount=0;
  for(const o of items){
    if(!o?.id||seen.has(o.id))continue;seen.add(o.id);
    const a=auditItem(o,s,today);records[o.id]=a;counts[a.status]++;
    if(a.issues.length){problemCount++;if(result.exceptions.length<150)result.exceptions.push({store:s,id:o.id,issues:a.issues});}
  }
  result.status_by_id[s]=records;
  result.stores[s]={evaluated:seen.size,raw_records:items.length,by_status:counts,with_issues:problemCount,feed_status:feed.status||'missing',feed_reported_total:feed.reported_total??null,feed_imported_total:feed.imported_total??null,scope:'Records received from available sources, NOT all store discounts and NOT independently verified prices'};
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
