// Live Pages freshness contract: alert if a successful build merely serves old offers.
'use strict';
const assert=require('node:assert/strict');
const base=process.env.BASE_URL||'https://dasphhs.github.io/Boodschappen-maatje/docs/';
const root=base.endsWith('/')?base:base+'/';
const today=new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
function daysSince(day){
 const t=Date.parse(today+'T12:00:00Z'),s=Date.parse(String(day||'').slice(0,10)+'T12:00:00Z');
 return Number.isFinite(s)?Math.round((t-s)/86400000):Infinity;
}
async function data(path){
 const res=await fetch(root+'data/'+path+'.json',{headers:{'Cache-Control':'no-cache'},signal:AbortSignal.timeout(45000)});
 assert.ok(res.ok,'Live feed missing: '+path+' HTTP '+res.status);
 return res.json();
}
(async()=>{
 const [promo,catalog,coverage]=await Promise.all([data('offers-catalog'),data('retailer-catalog'),data('product-resolution')]);
 assert.ok(daysSince(promo.generated_at)>=0&&daysSince(promo.generated_at)<=2,
  'Promotion catalog generation is more than two days old');
 assert.ok(daysSince(catalog.source_date)>=0&&daysSince(catalog.source_date)<=3,
  'Retailer price catalog is more than three days old');
 assert.ok(daysSince(coverage.generated_at)>=0&&daysSince(coverage.generated_at)<=2,
  'Product coverage has not been recomputed recently');
 for(const s of ['lidl','jumbo','ah']){
  const st=promo.stores?.[s];
  assert.equal(st?.status,'ok',s+' is using a stale or failed promotion import');
  assert.ok(daysSince(st.checked_at)<=2,s+' last successful source poll is old');
  assert.ok(st.offers?.some(x=>x.start_date<=today&&x.end_date>=today),
   s+' has no current valid promotions');
  assert.ok((catalog.stores?.[s]?.length||0)>1000,s+' retailer catalog unexpectedly tiny');
 }
 const summary=coverage.summary||{};
 assert.equal(summary.checked,summary.profiles*3,'Incomplete 3-store coverage');
 assert.ok(summary.price_observed>=35,'Coverage regression: only '+summary.price_observed+' matches');
 console.log(JSON.stringify({tested_at:today,promotions:Object.fromEntries(['lidl','jumbo','ah'].map(s=>[s,promo.stores[s].offers.length])),coverage:summary,source_date:catalog.source_date}));
})().catch(e=>{console.error('LIVE FRESHNESS FAILURE:',e);process.exitCode=1});
