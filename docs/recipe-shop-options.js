/* Per-ingredient shopping OPTIONS from dated external shelf observations.
 * Never write prices to a recipe, and never imply a complete verified basket. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeRecipeShopOptions=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const normalize=x=>String(x||'').toLocaleLowerCase('nl-NL').normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const forbidden=[
  'saus','soep','mix','maaltijd','burger','schnitzel','gerookt','gemarineerd',
  'gekruid','vulling','salade','pizza','chips','kruiden','dressing','baby','gepaneerd'
 ];
 const variants={
  'kipfilet':{all:['kipfilet'],none:['haasjes','reepjes','blokjes','diepvries']},
  'magere kwark':{all:['magere','kwark'],none:['drank','high protein','lactosevrij']},
  'mager rundergehakt':{all:['mager','rundergehakt'],none:['gemengd']},
  'kabeljauwfilet':{all:['kabeljauwfilet'],none:['vissticks','gerookt']},
  'zalmfilet':{all:['zalmfilet'],none:['gerookt','kruiden','gravad','burger']},
  'broccoli':{all:['broccoli'],none:['rijst','puree','schotel','wokmix','saus','diepvries']},
  'boerenkool':{all:['boerenkool'],none:['stamppot','gekruid','schotel']},
  'paprika':{all:['paprika'],none:['poeder','pasta','saus','chips','mix','puntpaprika']},
  'diepvries sperziebonen':{all:['sperziebonen'],any:['diepvries','bevroren']},
  'magere yoghurt':{all:['magere','yoghurt']},
  'tofu':{all:['tofu'],none:['gerookt']},
  'stevige tofu':{all:['tofu'],none:['gerookt','zijde']},
  'tempeh':{all:['tempeh']},
  'tomatenblokjes':{all:['tomatenblokjes']},
  'tomatenpuree':{all:['tomatenpuree']},
  'paksoi':{all:['paksoi'],none:['wokmix']},
  'courgette':{all:['courgette'],none:['gevuld']},
  'venkel':{all:['venkel'],none:['thee']},
  'wortel':{all:['wortel'],none:['taart','sap']},
  'spitskool':{all:['spitskool'],none:['maaltijd']},
  'harissa':{all:['harissa'],none:['kruidenmix']}
 };
 function recommend(recipe,store,catalog,pricing,resolver,today){
  const ingredients=Array.isArray(recipe?.ingredients)?recipe.ingredients:[];
  const blank={rows:[],matched:0,required:ingredients.length,source_date:catalog?.source_date||null,
   source:'Checkjebon',available:false};
  if(!['lidl','jumbo','ah'].includes(store)||!catalog||!pricing?.pack||!pricing?.inspect||
   !resolver?.matching||!(/^\d{4}-\d\d-\d\d$/.test(today))||
   !Array.isArray(catalog.stores?.[store])||!catalog.source_date)return blank;
  const age=Math.round((Date.parse(today+'T12:00:00Z')-Date.parse(catalog.source_date+'T12:00:00Z'))/86400000);
  if(!Number.isFinite(age)||age<0||age>3)return blank;
  const listed=catalog.stores[store],rows=[];
  for(const ing of ingredients){
   const label=normalize(ing?.name),q=Number(ing?.quantity);
   const requiredUnit=ing?.unit==='g'?'kg':ing?.unit==='ml'?'L':null;
   const rule=variants[label];
   if(!rule||!requiredUnit||!Number.isFinite(q)||q<=0)continue;
   const required=q/1000,profile={match:{all:rule.all,any:rule.any||[],none:[...forbidden,...(rule.none||[])]}};
   let chosen=null;
   for(const row of listed){
    if(!Array.isArray(row)||typeof row[0]!=='string'||!Number.isFinite(row[1])||row[1]<=0||
      typeof row[2]!=='string'||row[2].length>80)continue;
    const name=row[0];
    if(resolver.matching({name,pack_label:row[2]},profile,pricing).status!=='match')continue;
    const p=pricing.pack({name,pack_label:row[2]});
    if(!p||p.approximate||p.unit!==requiredUnit||p.amount<=0||p.amount>15)continue;
    const count=Math.ceil((required-1e-9)/p.amount);
    if(count<1||count>12)continue;
    const item={name,price:row[1],pack_label:row[2],store,
     status:'external_regular_observed',source_provider:'Checkjebon',
     checked_date:catalog.source_date,url:row[3]||catalog.source_url};
    const inspected=pricing.inspect(item,store,today);
    if(!inspected?.current||inspected.conflict)continue;
    const total=Math.round(count*row[1]*100)/100;
    if(!Number.isFinite(total)||total<=0||total>300)continue;
    if(!chosen||total<chosen.purchase_total-0.001||
      (Math.abs(total-chosen.purchase_total)<0.001&&count<chosen.pack_count)){
     chosen={ingredient:ing.name,quantity:q,unit:ing.unit,product:name,
      pack_label:row[2],pack_count:count,unit_price:Math.round(row[1]*100)/100,
      purchase_total:total,url:item.url,source_date:catalog.source_date};
    }
   }
   if(chosen)rows.push(chosen);
  }
  return {rows,matched:rows.length,required:ingredients.length,source_date:catalog.source_date,
   source:'Checkjebon',available:true};
 }
 return {recommend};
});
