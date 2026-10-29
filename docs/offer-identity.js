/* Store-scoped listing identity and source conflict evidence.
   Match ONLY identical package sizes/types and known product families. */
(function(root,factory){
 const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeOfferIdentity=api;
})(typeof window!=='undefined'?window:null,function(){
 const fold=x=>String(x||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 function pack(o){
  const t=String(o?.pack_label||o?.name||'').toLowerCase().replace(/×/g,'x').replace(/,/g,'.');
  let m=t.match(/(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|cl|l|g|kg)\b/);
  if(!m)m=t.match(/(\d+)\s*(?:stuks?|flesjes|flessen|blikjes|blikken)\s*(?:a|van|à)?\s*(\d+(?:\.\d+)?)\s*(ml|cl|l|g|kg)\b/);
  if(m){const d={ml:1,cl:10,l:1000,g:1,kg:1000}[m[3]];const unit=['ml','cl','l'].includes(m[3])?'ml':'g';return m[1]+'x'+Math.round(Number(m[2])*d*100)/100+unit}
  m=t.match(/(\d+(?:\.\d+)?)\s*(ml|cl|l|g|kg)\b/);
  if(m){const d={ml:1,cl:10,l:1000,g:1,kg:1000}[m[2]];const unit=['ml','cl','l'].includes(m[2])?'ml':'g';return '1x'+Math.round(Number(m[1])*d*100)/100+unit}
  return fold(o?.pack_label||'');
 }
 function container(o){
  const t=fold((o?.name||'')+' '+(o?.pack_label||''));
  if(/\b(blik|blikje|blikjes|blikken)\b/.test(t))return 'blik';
  if(/\b(fles|flesje|flesjes|flessen)\b/.test(t))return 'fles';
  return 'verpakkingstype-onbekend';
 }
 function variantConflict(o){
  const label=fold(o?.name),variant=fold(o?.variant);
  const zero=/\b0\s+0\b|\balcoholvrij\b/.test(label);
  return (variant==='alcoholvrij'&&!zero)||(variant==='alcoholhoudend'&&zero);
 }
 function classify(o,today){
  if(!o||!o.id||!o.name||!Number.isFinite(o.price)||o.price<=0||
     !/^\d{4}-\d{2}-\d{2}$/.test(String(o.start_date||''))||
     !/^\d{4}-\d{2}-\d{2}$/.test(String(o.end_date||''))||
     !/^\d{4}-\d{2}-\d{2}$/.test(String(today||''))||
     o.start_date>today||o.end_date<today||o.start_date>o.end_date||o.online_only)return 'excluded';
  // A historical or regular-price observation is never a promotion.
  if(o.is_regular_low_price||o.status==='third_party_price_observation'||
     o.source_provider==='Biernet'||/^(historical|upcoming|regular|inactive)$/.test(String(o.promotion_status||'')))return 'observation';
  // A conflicting product variant must never be published as a promotion.
  if(variantConflict(o))return 'excluded';
  if(!/^https:\/\//.test(String(o.source?.url||'')))return 'excluded';
  // An explicit cross-source/retailer price conflict must never become a confirmed promotion.
  if(o.price_conflict)return 'reported';
  if(o.verified===true){
   const provider=String(o.source_provider||'');
   let host='';try{host=new URL(o.source.url).hostname.toLowerCase().replace(/^www\./,'')}catch{}
   const officialHost=['lidl.nl','jumbo.com','ah.nl'].some(d=>host===d||host.endsWith('.'+d));
   const retailerSource=['officiele_folder','jumbo_official','lidl_official','ah_official'].includes(provider);
   return officialHost||retailerSource?'confirmed':'reported';
  }
  if(o.source_provider==='PrijsProfeet'&&o.promotion_status==='active')return 'reported';
  if(o.source_provider==='user_folder_image'&&o.evidence_date&&o.evidence_date<=today)return 'reported';
  return 'excluded';
 }
 function key(o){
  const n=fold(o?.name);
  const brand=/(?:^|\s)(texels)\s+skuumkoppe\b/.test(n)?'texels-skuumkoppe':
              /\bla chouffe\b/.test(n)?'la-chouffe-'+(n.includes('blond')?'blond':'other'):null;
  if(brand){
   const alcohol=/\b0\s+0\b|\balcoholvrij\b/.test(n)?'zero':'alcohol';
   return 'known-brand:'+brand+'|'+alcohol+'|'+pack(o)+'|'+container(o);
  }
  return 'exact-name:'+n.replace(/^(ah|albert heijn|jumbo|lidl) /,'')+'|'+pack(o);
 }
 function merge(items){
  const seen=new Map(),results=[];
  for(const x of items){
   if(!x?.id||!Number.isFinite(x.price))continue;
   const k=key(x),a=seen.get(k);
   if(!a){
    const z={...x,source_observations:[{id:x.id,price:x.price,url:x.source?.url||null}]};
    seen.set(k,z);results.push(z);continue;
   }
   // Propagate conflict before same-ID deduplication: spotlight and daily may reuse an offer ID.
   if(x.price_conflict&&!String(a.price_conflict||'').includes(String(x.price_conflict)))
     a.price_conflict=a.price_conflict?a.price_conflict+' · '+x.price_conflict:x.price_conflict;
   if(a.source_observations.some(o=>o.id===x.id))continue;
   a.source_observations.push({id:x.id,price:x.price,url:x.source?.url||null});
   const prices=a.source_observations.map(o=>o.price),min=Math.min(...prices),max=Math.max(...prices);
   if(max-min>=0.02){
    const conflict='Exacte verpakking volgens meerdere bronnen: € '+min.toFixed(2).replace('.',',')+' tegenover € '+max.toFixed(2).replace('.',',')+'; actuele winkelprijs onbekend';
    a.price_conflict=a.price_conflict?a.price_conflict+' · '+conflict:conflict;
   }
  }
  return results;
 }
 return {key,pack,container,variantConflict,classify,merge};
});
