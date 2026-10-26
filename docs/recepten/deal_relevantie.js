/* Boodschappen-maatje: relevantie is een keuzehulp, geen bewijs van korting. */
(function(root){
"use strict";
function norm(value){return String(value||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
const PACKAGE=/\b(?:wereldgerechten?|wereldgerecht|maaltijdpakket|maaltijdmix|knorr\s+(?:trattoria|spaghetteria|risotteria|foodtrips))\b/i;
const PROTEIN=/\b(?:fitquark|fitkwark|xxl\s*nutrition|high\s*protein|highprotein|prote[iï]ne\s*(?:kwark|pudding|yoghurt|shake|drink)|protein\s*(?:kwark|pudding|yoghurt|shake|drink)|skyr|kvarg|knijpkwark|melkunie\s+protein)\b/i;
const STARTER=/\b(?:naan(?:brood)?|tortilla|wraps?|couscous|rijst|volkoren\s+pasta|tomatenblokjes|kikkererwten|linzen|kokosmelk)\b/i;
const FRESH=/\b(?:broccoli|spinazie|bloemkool|champignons|pastinaak|boerenkool|spruiten|courgette|kipfilet|kipgehakt|zalmfilet|garnalen|tofu|eieren)\b/i;
const SWEETS=/\b(?:snoep|koek|kruidnoten|chips|frisdrank|chocoladereep|ijs|frikandel)\b/i;
const LABELS={maaltijdpakket:"Maaltijdpakket · kookidee",proteine:"Eiwitrijk product",basis:"Veelzijdig kookproduct",vers:"Gezonde maaltijdcomponent",overig:"Overige aanbieding"};
function classify(value){
 const name=norm(typeof value==="string"?value:value?.name);
 if(PACKAGE.test(name))return "maaltijdpakket";
 if(PROTEIN.test(name)&&/(?:kwark|quark|skyr|pudding|yoghurt|yogurt|shake|drink|kvarg)/.test(name))return "proteine";
 if(STARTER.test(name))return "basis";
 if(FRESH.test(name))return "vers";
 return "overig";
}
function validToday(d,today){
 const start=String(d.valid_from||"").slice(0,10),end=String(d.valid_until||"").slice(0,10);
 return Boolean(today&&end&&end>=today&&(!start||start<=today));
}
function bundleInfo(d){
 const n=String(d.promotion_type||"").toLowerCase();
 let match=n.match(/\b([1-9])\s*(?:\+|plus)\s*([1-9])\s*gratis\b/);
 if(match){
   const paid=Number(match[1]),free=Number(match[2]);
   return {required:paid+free,paid,free,label:paid+"+"+free+" gratis · koop "+(paid+free)};
 }
 const count=Number(d.multi_buy_quantity),total=Number(d.multi_buy_price);
 if(Number.isInteger(count)&&count>=2&&count<=40&&Number.isFinite(total)&&total>0)
   return {required:count,paid:count,free:0,label:count+" stuks voor € "+total.toFixed(2).replace(".",",")};
 return null;
}
function isVerified(d){
 // Bundelpercentages gelden niet bij de aankoop van één artikel.
 // Ook een geverifieerd kortingspercentage kan bij 2+3 misleidend zijn
 // zolang het exacte mandje en de deelnemende varianten onbekend zijn.
 if(bundleInfo(d))return false;
 return d.discount_verified===true && Number.isFinite(Number(d.verified_discount_pct)) &&
  Number(d.verified_discount_pct)>0;
}
function relevance(d){
 const name=norm(d.name);
 const kind=classify(name),base={maaltijdpakket:105,proteine:102,basis:70,vers:72,overig:15}[kind];
 const discount=isVerified(d)?Math.min(30,Number(d.verified_discount_pct)*0.4):0;
 const bundle=bundleInfo(d);
 let score=base+discount;
 if(bundle)score+=6;
 if(/\b(?:xxl|fitquark|fitkwark|wereldgerechten|knorr)\b/.test(name))score+=7;
 if(SWEETS.test(name))score-=25;
 if(d.is_loyalty)score-=7;
 return score;
}
function sort(items){return (items||[]).slice().sort((a,b)=>relevance(b)-relevance(a) ||
 Number(isVerified(b))-Number(isVerified(a)) ||
 String(a.name).localeCompare(String(b.name),"nl"))}
function reason(d){
 const kind=classify(d),bundle=bundleInfo(d);
 const parts=[LABELS[kind]];
 if(bundle)parts.push(bundle.label);
 if(!isVerified(d))parts.push("Korting niet volledig berekend");
 return parts.join(" · ");
}
const api={norm,classify,validToday,bundleInfo,isVerified,relevance,reason,sort};
root.DealRelevantie=api;
if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof globalThis!=="undefined"?globalThis:this);
