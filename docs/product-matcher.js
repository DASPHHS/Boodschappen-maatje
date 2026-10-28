/* Shared strict product-identity checks. No name substring can certify a price. */
(function(root,factory){
 const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeProductMatcher=api;
})(typeof window!=='undefined'?window:null,function(){
 const norm=v=>String(v||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const families=[
  ['zalm',/\b(zalm|zalmfilet|wilde zalm)\b/],
  ['kabeljauw',/\b(kabeljauw|kabeljauwfilet)\b/],
  ['broccoli',/\bbroccoli\b/],
  ['bloemkool',/\bbloemkool\b/],
  ['boerenkool',/\bboerenkool\b/],
  ['spruitjes',/\bspruitjes?\b/],
  ['sperziebonen',/\b(sperziebonen?|sperzieboon|groene bonen)\b/],
  ['pompoen',/\b(flespompoen|pompoen)\b/],
  ['paprika',/\bpaprika\b/],
  ['wortel',/\b(waspeen|bospeen|wortel|wortelen)\b/],
  ['tofu',/\btofu\b/],
  ['tempeh',/\btempeh\b/],
  ['gehakt',/\b(gehakt|rundergehakt|varkensgehakt)\b/],
  ['kipfilet',/\b(kipfilet|kipfilethaasjes|kipfiletblokjes|kipfiletreepjes)\b/],
  ['kippenbouten',/\b(kippenbouten|kippenpoten|drumsticks)\b/],
  ['melk',/\bmelk\b/],
  ['pindakaas',/\bpindakaas\b/],
  ['skuumkoppe',/\bskuumkoppe\b/],
  ['soto boemboe',/\b(soto|saoto)\s?boemboe\b|\bboemboe\s?(soto|saoto)\b/],
  ['sereh',/\b(sereh|citroengras|lemongrass)\b/]
 ];
 function family(name){
  const n=norm(name);
  if(/\b(saus|soep|kruiden|kruidenmix|maaltijdmix|chips|burger|schnitzel|visstick)\b/.test(n))return null;
  for(const [family,regex] of families)if(regex.test(n))return family;
  return null;
 }
 function features(name){
  const n=norm(name),f=family(name);
  const plant=/\b(plantaardig|vegan|vega|vegetarisch|terra)\b/.test(n);
  return {family:f,retailer:/\b(jumbo)\b/.test(n)?'jumbo':/\b(ah|albert heijn)\b/.test(n)?'ah':/\blidl\b/.test(n)?'lidl':null,plant:plant?'plant':['zalm','kabeljauw','kipfilet','kippenbouten','gehakt'].includes(f)?'animal':null,
   skin:/\b(zonder huid|huidloos)\b/.test(n)?'without':/\b(op huid|met huid)\b/.test(n)?'with':null,
   wild:/\b(wild|wilde)\b/.test(n)?'wild':/\bkweek\b/.test(n)?'farmed':null,
   frozen:/\b(diepvries|bevroren)\b/.test(n)?'frozen':/\b(vers|verse)\b/.test(n)?'fresh':null,
   smoked:/\b(gerookt)\b/.test(n)?'smoked':null,
   bone:/\b(zonder bot|ontbeend)\b/.test(n)?'boneless':/\b(met bot|kippenpoten|kippenbouten|drumsticks)\b/.test(n)?'bonein':null,
   alcohol:/\b(0 0|alcoholvrij|0 procent)\b/.test(n)?'zero':/\b(bier|pils|strong|blond|sku umkoppe|skuumkoppe)\b/.test(n)?'alcohol':null,
   milk:/\b(halfvolle|halfvol)\b/.test(n)?'half':/\b(magere|mager)\b/.test(n)?'skim':/\b(volle|vol)\b/.test(n)?'full':null,
   meat:/\b(gemengd gehakt|half om half)\b/.test(n)?'mixed':/\brundergehakt\b/.test(n)?'beef':/\bvarkensgehakt\b/.test(n)?'pork':null};
 }
 function evaluate(offer,ingredient){
  if(!offer||!ingredient)return {status:'unrelated',reason:'product ontbreekt'};
  const a=features(offer.name),b=features(ingredient.name);
  const e1=String(offer.ean||''),e2=String(ingredient.ean||'');
  const id1=String(offer.product_id||''),id2=String(ingredient.product_id||'');
  if(e1&&e2&&e1===e2)return {status:'compatible',reason:'zelfde EAN',family:a.family||b.family};
  if(id1&&id2&&id1===id2)return {status:'compatible',reason:'zelfde product-ID',family:a.family||b.family};
  if(norm(offer.name)===norm(ingredient.name))return {status:'compatible',reason:'exact gelijkluidende productnaam',family:a.family||b.family};
  if(!a.family||!b.family||a.family!==b.family)return {status:'unrelated',reason:'andere productfamilie'};
  const critical=['retailer','plant','skin','wild','frozen','smoked','bone','alcohol','milk','meat'];
  const conflicts=critical.filter(k=>a[k]&&b[k]&&a[k]!==b[k]);
  if(conflicts.length)return {status:'incompatible',reason:'variant verschilt: '+conflicts.join(', '),family:a.family};
  const missing=critical.filter(k=>(a[k]&&!b[k])||(!a[k]&&b[k])).filter(k=>
    k==='skin'&&a.family==='zalm'||k==='alcohol'&&a.family==='skuumkoppe'||k==='meat'&&a.family==='gehakt'||
    k==='milk'&&a.family==='melk'||k==='bone'&&a.family==='kippenbouten'||
    k==='plant'&&['kipfilet','zalm','gehakt'].includes(a.family)||
    k==='frozen'&&['sperziebonen','zalm'].includes(a.family)||
    k==='smoked'&&['zalm','kabeljauw'].includes(a.family));
  if(missing.length)return {status:'uncertain',reason:'variant onvoldoende gespecificeerd: '+missing.join(', '),family:a.family};
  return {status:'compatible',reason:'zelfde productsoort en geen variantconflict',family:a.family};
 }
 function packGrams(offer){
   const x=norm(offer.pack_label);
   const m=x.match(/(\d+)\s*x\s*(\d+(?:[.,]\d+)?)\s*(kg|g)\b/);
   if(m)return Number(m[1])*Number(m[2].replace(',','.'))*(m[3]==='kg'?1000:1);
   const one=x.match(/(\d+(?:[.,]\d+)?)\s*(kg|g)\b/);
   return one?Number(one[1].replace(',','.'))*(one[2]==='kg'?1000:1):null;
 }
 function priceApplied(offer,ingredient){
  if(evaluate(offer,ingredient).status!=='compatible')return false;
  if(offer.price_conflict||ingredient.price_status!=='folder_current'||!Number.isFinite(offer.price)||!Number.isFinite(ingredient.pack_price))return false;
  const packages=Number(ingredient.package_count||1);
  if(!Number.isInteger(packages)||packages<1)return false;
  // Retailer's bundle offer is one purchased unit; never multiply a bundle's regular price.
  const grams=packGrams(offer);
  if(grams&&ingredient.unit==='g'&&Number(ingredient.quantity)>grams*packages+0.01)return false;
  const expected=offer.price*packages;
  return Math.abs(expected-ingredient.pack_price)<=0.015;
 }
 return {norm,family,features,evaluate,packGrams,priceApplied};
});
