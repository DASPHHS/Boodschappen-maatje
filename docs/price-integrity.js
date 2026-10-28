/* Price integrity rules shared by cards, recipes and the shopping list.
   Every visible number is recomputed from whole packs. Historical isn't live. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjePricing=api;
})(typeof window!=='undefined'?window:null,function(){
 const cents=n=>Math.round(n*100);
 const valid=n=>typeof n==='number'&&Number.isFinite(n)&&n>=0;
 function basket(recipe,today){
  const ingredients=Array.isArray(recipe?.ingredients)?recipe.ingredients:[];
  const missing=ingredients.filter(i=>!valid(i.pack_price));
  const priced=ingredients.filter(i=>valid(i.pack_price));
  const partial=cents(priced.reduce((x,i)=>x+i.pack_price,0))/100;
  const total=missing.length?null:partial;
  const declared=recipe?.cost?.basket_total;
  const consistent=total!==null&&valid(declared)&&Math.abs(cents(declared)-cents(total))<=1;
  const dated=priced.map(i=>i.price_observed_at||i.checked_at).filter(d=>/^\d{4}-\d{2}-\d{2}$/.test(d));
  const oldest=dated.length?dated.sort()[0]:null;
  const lacksDate=priced.some(i=>!i.price_observed_at&&!i.checked_at&&i.price_status!=='folder_current');
  const stale=oldest&&today?oldest<today:false;
  const explicitlyVerified=total!==null&&consistent&&recipe?.cost?.estimated===false&&recipe?.cost?.verified_today===true&&
    priced.every(i=>i.price_observed_at===today||i.checked_at===today)&&!lacksDate;
  const state=ingredients.length===0?'unpriced':missing.length===ingredients.length?'unpriced':
    missing.length?'partial':explicitlyVerified?'today_confirmed':'historical_estimate';
  return {state,total,partial,missing:missing.map(i=>i.name||'Onbekend'),priced_count:priced.length,
   declared_total:valid(declared)?declared:null,consistent,oldest_date:oldest,
   stale:!!stale,unverified:state!=='today_confirmed',
   warning:state==='partial'?'Niet alle ingrediënten hebben een verpakkingsprijs':
   state==='historical_estimate'?'Alle verpakkingen geprijsd, maar niet volledig onafhankelijk vandaag gecontroleerd':
   state==='unpriced'?'Geen complete prijsberekening beschikbaar':null};
 }
 // Generic pack comparison must not silently equate 6x300ml and 6x330ml.
 function liquidLitres(s){
  const text=String(s||'').toLowerCase().replace(/,/g,'.').replace(/×/g,'x');
  let m=text.match(/(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|cl|l)\b/);
  if(m){const unit={ml:1000,cl:100,l:1}[m[3]];return Number(m[1])*Number(m[2])/unit}
  m=text.match(/(\d+)\s*(?:flesjes|flessen|blikjes|blikken|stuks)\s*(?:a|van|à)?\s*(\d+(?:\.\d+)?)\s*(ml|cl|l)\b/);
  if(m)return Number(m[1])*Number(m[2])/{ml:1000,cl:100,l:1}[m[3]];
  m=text.match(/(\d+(?:\.\d+)?)\s*(ml|cl|l)\b/);
  return m?Number(m[1])/{ml:1000,cl:100,l:1}[m[2]]:null;
 }
 function unitCost(product){
  const litres=liquidLitres(product?.pack_label)||liquidLitres(product?.name);
  return litres&&valid(product.price)?{price:Math.round(product.price/litres*100)/100,unit:'L',quantity:litres}:null;
 }
 return {basket,liquidLitres,unitCost};
});
