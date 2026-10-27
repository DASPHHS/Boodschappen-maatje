(function(root){
  'use strict';
  const cents=n=>Math.round((n+Number.EPSILON)*100)/100;
  function active(price,day){return Boolean(price&&price.sale&&price.valid_from&&price.valid_until&&price.valid_from<=day&&day<=price.valid_until);}
  function refresh(recipe,day){
    const r=JSON.parse(JSON.stringify(recipe));
    for(const ing of r.ingredients){if(ing.price?.sale&&!active(ing.price,day))ing.price=ing.price.ordinary_alternative||null;}
    r.sale_count=r.ingredients.filter(x=>active(x.price,day)).length;
    r.complete=r.ingredients.every(x=>x.price&&x.price.form_verified!==false);
    r.known_used=cents(r.ingredients.reduce((a,x)=>a+(x.price?.used||0),0));
    r.known_checkout=cents(r.ingredients.reduce((a,x)=>a+(x.price?.checkout||0),0));
    r.per_serving=r.complete?cents(r.known_used/4):null;
    r.used_total=r.complete?r.known_used:null;r.checkout=r.complete?r.known_checkout:null;
    return r;
  }
  function compare(a,b){return b.sale_count-a.sale_count||Number(b.complete)-Number(a.complete)||(a.complete&&b.complete?a.per_serving-b.per_serving:0)||a.title.localeCompare(b.title,'nl');}
  function select(data,store,category,day){return(data.stores[store]||[]).filter(x=>x.category===category).map(x=>refresh(x,day)).sort(compare).slice(0,10);}
  function stale(observed,now=Date.now()){const t=Date.parse(observed);return !Number.isFinite(t)||now-t>36*3600*1000||t-now>3600*1000;}
  function quantity(n,unit){return new Intl.NumberFormat('nl-NL',{maximumFractionDigits:2}).format(n)+' '+(unit==='st'?'stuks':unit);}
  function listText(r,store){return [r.title+' · '+store,'Voor vier royale porties',...r.ingredients.map(x=>{
    const p=x.price;return '- '+x.label+': '+quantity(x.quantity,x.unit)+(p?' | '+p.packages+' × '+quantity(p.package_quantity,p.unit)+' | '+p.product+(p.sale?' | ACTIE '+(p.condition||'')+' t/m '+p.valid_until:' | regulier'):' | prijs nog controleren');
  })].join('\n');}
  const api={active,refresh,compare,select,stale,quantity,listText};root.Winkelhulp=api;
  if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis==='object'?globalThis:this);
