/* Three-supermarket week-window selection, adapted from specialedeals/weekdeals.
 * No second bulk API feed: reuse the app's own dated promotions and explicitly
 * separated upcoming offers. Never infer availability or the checkout price. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeWeekdeals=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const stores=['lidl','jumbo','ah'];
 function week(today,which='now'){
  if(typeof today!=='string'||!/^\d{4}-\d\d-\d\d$/.test(today))return null;
  const day=new Date(today+'T12:00:00Z');
  if(Number.isNaN(day.valueOf()))return null;
  const monday=new Date(day);
  monday.setUTCDate(day.getUTCDate()-(day.getUTCDay()+6)%7+(which==='next'?7:0));
  const sunday=new Date(monday);sunday.setUTCDate(monday.getUTCDate()+6);
  return {from:monday.toISOString().slice(0,10),through:sunday.toISOString().slice(0,10)};
 }
 function eligible(o,store,today,period){
  if(!stores.includes(store)||!o||!Number.isFinite(o.price)||o.price<=0||!o.id||!o.name||
     !/^\d{4}-\d\d-\d\d$/.test(o.start_date||'')||
     !/^\d{4}-\d\d-\d\d$/.test(o.end_date||'')||o.start_date>o.end_date||
     o.online_only===true||o.price_conflict||o.is_regular_low_price||
     !/^https:\/\//.test(o.source?.url||''))return false;
  if(!['active','upcoming'].includes(o.promotion_status||'')&&o.source_provider==='PrijsProfeet')return false;
  const w=week(today,period);
  return !!w&&o.start_date<=w.through&&o.end_date>=w.from&&o.end_date>=today;
 }
 function next(store,scan,today){
  if(!stores.includes(store)||scan?.status!=='ok'||!Array.isArray(scan.offers))return [];
  const seen=new Set(),rows=[];
  for(const o of [...scan.offers,...(scan.upcoming_offers||[])]){
   if(!eligible(o,store,today,'next'))continue;
   const id=String(o.id);
   if(seen.has(id))continue;
   seen.add(id);rows.push(o);
  }
  return rows;
 }
 return {week,eligible,next};
});
