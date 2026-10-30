#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.join(__dirname,'../docs/data');
const catalog=JSON.parse(fs.readFileSync(path.join(root,'retailer-catalog.json')));
const profiles=JSON.parse(fs.readFileSync(path.join(root,'watchlist.json'))).items;
const search=require('../docs/catalog-search.js');
const semantic=require('../docs/product-semantics.js'),resolver=require('../docs/product-resolver.js'),pricing=require('../docs/price-observations.js');
const day=new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
const report={schema_version:1,policy_version:semantic.VERSION,generated_at:new Date().toISOString(),source_date:catalog.source_date,source_commit:catalog.source_commit,counts:{match:0,partial:0,reject:0},profiles:{},queue:[]};
const seen=new Set();
for(const profile of profiles){
 if(!profile.match)continue;
 const r=profile.match,summary={match:0,partial:0,reject:0,reasons:{},samples:[],groups:{}};
 for(const store of ['lidl','jumbo','ah'])for(const row of catalog.stores[store]){
  const n=row[0];
  if((r.all||[]).some(x=>!resolver.has(n,x))||r.any?.length&&!r.any.some(x=>resolver.has(n,x)))continue;
  const o=search.observation(row,store,catalog,day,pricing);
  const result=resolver.matching(o,profile,pricing);
  summary[result.status]++;report.counts[result.status]++;
  summary.reasons[result.reason]=(summary.reasons[result.reason]||0)+1;
  if(result.status==='match'){
   const key=result.comparison_key;
   const g=summary.groups[key]??={label:result.comparison_label,stores:{}};
   g.stores[store]=(g.stores[store]||0)+1;
  }else if(summary.samples.length<8)summary.samples.push({store,name:n,status:result.status,reason:result.reason});
  if((result.status==='partial'||result.status==='match')&&row[3]&&pricing.isDirectProductUrl(row[3],store)&&!seen.has(store+':'+o.product_id)){
   seen.add(store+':'+o.product_id);
   report.queue.push({profile:profile.key,priority:['kip','vis','vlees','groente','fruit'].includes(profile.category)?0:1,store,product_id:o.product_id,name:n,pack:row[2],url:o.url,reason:result.reason,
    fingerprint:crypto.createHash('sha256').update(n+'\n'+row[2]).digest('hex').slice(0,24)});
  }
 }
 report.profiles[profile.key]=summary;
}
// Fair per-store processing rather than exhausting the daily budget on one chain.
report.queue.sort((a,b)=>(a.priority||0)-(b.priority||0)||a.product_id.localeCompare(b.product_id)||a.store.localeCompare(b.store));
fs.writeFileSync(path.join(root,'semantic-review.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({policy:report.policy_version,counts:report.counts,review_queue:report.queue.length}));
