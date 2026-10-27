(function(root){
'use strict';
const CATEGORIES={
  vlees:/\\b(kip|kipfilet|kipdij|rund|gehakt|biefstuk|varkens|schnitzel|filetlap|shoarma|hamburger)\\b/i,
  vis:/\\b(zalm|tonijn|kabeljauw|koolvis|visfilet|garnalen|makreel|haring|pangasius)\\b/i,
  groente:/\\b(broccoli|bloemkool|paprika|courgette|wortel|spinazie|sla|komkommer|tomaat|champignons|sperziebonen|wokgroenten|groentemix|prei|ui|uien|andijvie)\\b/i,
  zuivel:/\\b(kwark|yoghurt|skyr|hüttenkäse|cottage cheese|melk|eieren|kaas)\\b/i,
  koolhydraten:/\\b(pasta|rijst|aardappel|volkoren|wrap|tortilla|havermout|brood|noedels|couscous)\\b/i,
  vega:/\\b(tofu|tempeh|vegetarisch|vegan|vega |plantaardig|vivera)\\b/i
};
function categoryOf(name){
 for(const [key,re] of Object.entries(CATEGORIES))if(re.test(name||''))return key;
 return 'overig';
}
function active(x,day){return x&&x.valid_from<=day&&day<=x.valid_until&&x.status==='active';}
function calc(x){
 const regular=Number(x.normal_price),price=Number(x.price),count=Number(x.multi_buy_quantity),bundle=Number(x.multi_buy_price);
 if(!Number.isFinite(regular)||regular<=0)return null;
 if(Number.isInteger(count)&&count>=2&&Number.isFinite(bundle)&&bundle>0&&bundle<regular*count){
   return {required:count,checkout:bundle,each:bundle/count,regularTotal:regular*count,saving:regular*count-bundle};
 }
 if(!x.multi_buy_quantity&&Number.isFinite(price)&&price>0&&price<regular){
   return {required:1,checkout:price,each:price,regularTotal:regular,saving:regular-price};
 }
 return null;
}
function unitPrice(x,each){
 const match=String(x.size_label||x.quantity_label||'').match(/(\\d+(?:[.,]\\d+)?)\\s*(kg|g|gram|l|liter|ml)\\b/i);
 if(!match)return null;
 const n=Number(match[1].replace(',','.')),u=match[2].toLowerCase();
 const size=(u==='kg'||u==='l'||u==='liter')?n:n/1000;
 if(!Number.isFinite(size)||size<=0)return null;
 return {value:each/size,unit:(u==='kg'||u==='g'||u==='gram')?'kg':'liter'};
}
function choose(feed,store,day,category='alle'){
 const data=feed?.stores?.[store];if(!Array.isArray(data))return[];
 const unique=new Map();
 for(const item of data){
  if(!active(item,day))continue;
  const deal=calc(item);if(!deal)continue;
  const group=categoryOf(item.name);if(category!=='alle'&&group!==category)continue;
  const p=unitPrice(item,deal.each);
  const key=[item.name,item.valid_until,deal.required].join('|');
  const result={...item,...deal,category:group,unitPrice:p};
  if(!unique.has(key)||unique.get(key).each>result.each)unique.set(key,result);
 }
 return [...unique.values()].sort((a,b)=>b.saving/b.regularTotal-a.saving/a.regularTotal||a.each-b.each);
}
function fresh(timestamp,now=Date.now()){
 const t=Date.parse(timestamp);
 return Number.isFinite(t)&&now>=t-3600000&&now-t<=36*3600000;
}
const api={choose,calc,active,categoryOf,unitPrice,fresh};
root.WinkelDeals=api;
if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis==='object'?globalThis:this);
