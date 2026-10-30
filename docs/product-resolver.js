/* Generic, evidence-first resolver. A product preference is a query, never a price.
 * Matching and coverage apply to all future products, not just named examples. */
(function(root,factory){
 const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeResolver=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const semantic=typeof module==='object'&&module.exports?require('./product-semantics.js'):window.MaatjeSemantics;
 const norm=x=>String(x||'').toLocaleLowerCase('nl-NL').normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const has=(text,term)=>(' '+norm(text)+' ').includes(' '+norm(term)+' ');
 const known={lidl:'lidl',jumbo:'jumbo',ah:'ah'};
 function interest(input){
  if(typeof input==='string')return {key:'search',title:input,match:{all:input.split(/\s+/).filter(Boolean)}};
  const p=input||{};
  return {...p,match:p.match||{all:String(p.title||p.name||'').split(/\s+/).filter(Boolean)}};
 }
 function traits(product){
  const name=norm(product?.name||'');
  const declared=norm(product?.type||product?.variant||'');
  const shelf=/\b(houdbare|houdbaar|uht|langlekker|langhoudbare)\b/.test(name+' '+declared)?'houdbaar':
    /\b(verse|vers|gepasteuriseerd)\b/.test(name+' '+declared)?'vers':null;
  const fat=/\b(halfvolle|halfvol)\b/.test(name)?'halfvol':/\b(magere|mager)\b/.test(name)?'mager':
    /\b(volle|vollemelk)\b/.test(name)?'vol':null;
  const zero=/\b(0 0|alcoholvrij)\b/.test(name+' '+declared)?'alcoholvrij':null;
  return {shelf_life:shelf,fat,alcohol:zero};
 }
 function matching(product,profile,pricing){
  const p=interest(profile),rule=p.match||{},name=norm(product?.name||'');
  if(product?.pack_conflict)return {status:'partial',reason:'winkelpagina noemt een andere verpakking; hercontrole nodig'};
  if(!name)return {status:'reject',reason:'naam ontbreekt'};
  const all=Array.isArray(rule.all)?rule.all:[];
  const any=Array.isArray(rule.any)?rule.any:[];
  const none=Array.isArray(rule.none)?rule.none:[];
  if(all.some(x=>!has(name,x))||(any.length&&!any.some(x=>has(name,x)))||none.some(x=>has(name,x)))
   return {status:'reject',reason:'productnaam of uitsluitingen passen niet'};
  if(rule.ean&&String(rule.ean)!==String(product.ean||''))return {status:'reject',reason:'EAN verschilt'};
  const meaning=semantic.evaluate(product,p,pricing);
  if(meaning.status!=='match')return meaning;
  const features=traits(product);
  // A required facet is a hard condition: absence cannot become a confirmed match.
  for(const [field,value] of Object.entries(rule.traits||{})){
   if(features[field]&&features[field]!==value)return {status:'reject',reason:'ander type: '+field};
   if(!features[field])return {status:'partial',reason:'producttype '+field+' niet uit naam of bron bevestigd'};
  }
  if(rule.pack){
   const unit=pricing?.pack?.(product);
   if(!unit||unit.approximate)return {status:'partial',reason:'exacte inhoud ontbreekt'};
   if(unit.unit!==rule.pack.unit||Math.abs(unit.amount-Number(rule.pack.amount))>0.00001)
    return {status:'reject',reason:'verpakkingsgrootte verschilt'};
  }
  return {...meaning,status:'match',reason:'productkenmerken en verpakking passen'};
 }
 function candidates(profile,store,records,offers,pricing,today){
  const p=interest(profile),valid=[],possible=[],seen=new Set();
  for(const x of [...(records||[]).filter(o=>o.store===store),...(offers||[])]){
   if(!x?.name||!Number.isFinite(x?.price)||x.price<=0)continue;
   const evaluation=matching(x,p,pricing);
   if(evaluation.status==='reject')continue;
   const o=pricing?.inspect?.(x,store,today);
   if(!o||o.status==='historisch'||o.isPromotion===false&&x.start_date)continue;
   const id=[x.ean||x.product_id||x.name,x.pack_label||'',x.price,x.url||x.source?.url||''].join('|');
   if(seen.has(id))continue;seen.add(id);
   const result={...o,match:evaluation,score:o.score+(evaluation.status==='match'?40:0)};
   if(evaluation.status==='match')valid.push(result);else possible.push(result);
  }
  const sort=(list)=>pricing?.choose?pricing.choose(list):list.sort((a,b)=>b.score-a.score);
  return {valid:sort(valid),possible:sort(possible)};
 }
 function resolution(profile,store,records,offers,pricing,today){
  const {valid,possible}=candidates(profile,store,records,offers,pricing,today);
  const current=valid.filter(x=>x.current&&!x.conflict&&x.status!=='niet-beschikbaar');
  const provisional=valid.filter(x=>!x.current||x.conflict||x.status==='niet-beschikbaar');
  const best=current[0]||provisional[0]||null;
  const state=current.length?'price_observed':provisional.length?'stale_or_unavailable':
    possible.length?'needs_variant_evidence':'needs_source';
  return {state,best,current,provisional,possible,
   checked_date:today,unresolved_reason:state==='needs_source'?'geen passende productprijs uit aangesloten bronnen':
    state==='needs_variant_evidence'?'product gevonden, productvorm of inhoud onvoldoende bewezen':
    state==='stale_or_unavailable'?'alleen oude, tegenstrijdige of niet-beschikbare waarnemingen':null};
 }
 return {norm,has,interest,traits,matching,candidates,resolution};
});