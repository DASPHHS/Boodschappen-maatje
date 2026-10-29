#!/usr/bin/env node
/* Daily coverage inventory: every followed product x every store; never invent a price.
 * Output is an audit/queue, NOT a product-price source. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const base=path.resolve(__dirname,'../docs/data');
const read=name=>JSON.parse(fs.readFileSync(path.join(base,name+'.json'),'utf8'));
const resolver=require('../docs/product-resolver.js');
const pricing=require('../docs/price-observations.js');
const identity=require('../docs/offer-identity.js');
const catalogSearch=require('../docs/catalog-search.js');
const retailerCatalog=fs.existsSync(path.join(base,'retailer-catalog.json'))?read('retailer-catalog'):null;
const now=new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
const tracks=read('watchlist').items||[];
const records=read('personal-prices').products||[];
const feeds=['daily','spotlight','offers-catalog','supplemental-offers'].map(read);
const stores=['lidl','jumbo','ah'];
const result={schema_version:1,generated_at:new Date().toISOString(),checked_date:now,
 summary:{profiles:tracks.length,checked:0,price_observed:0,stale_or_unavailable:0,needs_variant_evidence:0,needs_source:0},
 stores:{}};
for(const store of stores){
 const offers=feeds.flatMap(f=>f.stores?.[store]?.offers||[]).filter(o=>
  ['confirmed','reported'].includes(identity.classify(o,now)));
 const items={};
 for(const p of tracks){
  let state,match,unresolved;
  if(p.requires_specific_variant){
   state='needs_variant_evidence';match=null;unresolved='specificeer het exacte product of de verpakking';
  }else if(p.match){
   const found=catalogSearch.combined(p,store,retailerCatalog,records,offers,pricing,resolver,now);
   match=found[0]||null;
   if(match){state=match.current?'price_observed':'stale_or_unavailable';unresolved=null;}
   else{const evaluated=resolver.resolution(p,store,records,offers,pricing,now);
    state=evaluated.state;match=evaluated.best;unresolved=evaluated.unresolved_reason;}
  }else{
   // Legacy profiles retain existing group-based matching; new profiles use the
   // common declarative matcher. No automatic fuzzy guessing of unseen SKUs.
   const observed=pricing.collect(store,p.key,records,offers,now);
   match=observed[0]||null;
   state=match?(match.current&&!match.conflict?'price_observed':'stale_or_unavailable'):'needs_source';
   unresolved=match?null:'geen bron in de gekoppelde gegevens';
  }
  const best=match?.o;
  items[p.key]={
   state,reason:unresolved||null,source:best?.url||best?.source?.url||null,
   product_name:best?.name||null,price:Number.isFinite(best?.price)?best.price:null,
   price_status:match?.label||null,checked_date:match?.checked||null
  };
  result.summary.checked++;result.summary[state]++;
 }
 result.stores[store]=items;
}
if(process.argv.includes('--check')){
 if(result.summary.checked!==stores.length*tracks.length)throw Error('coverage incomplete');
 console.log(JSON.stringify(result.summary));process.exit(0);
}
const target=path.join(base,'product-resolution.json');
fs.writeFileSync(target,JSON.stringify(result,null,2)+'\n');
console.log('Product resolution status:',JSON.stringify(result.summary));
