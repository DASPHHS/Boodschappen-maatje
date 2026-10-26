/* Betekenisgestuurd zoeken naar boodschappen en aanbiedingen, zonder fictieve matches. */
(function(root){
"use strict";
const norm=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
const groups={
 eiwitrijk:["eiwit","protein","proteine","proteïne","kwark","skyr","cottage cheese","hutt","kipfilet","tonijn","zalm","eieren","magere yoghurt"],
 zuivel:["kwark","skyr","yoghurt","melk","kefir","kaas","cottage cheese"],
 avondeten:["kip","vis","zalm","gehakt","rijst","pasta","groente","aardappel","tofu","wereldgerechten","maaltijdmix","curry"],
 gezond:["groente","fruit","diepvriesgroente","spinazie","broccoli","peulvruchten","linzen","noten","kwark","skyr"],
 goedkoop:["budget","huismerk","voordeelpak","aanbieding","korting","actie"],
 schoonmaak:["allesreiniger","afwasmiddel","vaatwastabletten","wasmiddel","wc reiniger","ontkalker","spons","doekjes","vuilniszakken"],
 verzorging:["shampoo","douchegel","tandpasta","deo","deodorant","zeep","bodylotion"],
 koken:["koekenpan","pan","bakvorm","keukengerei","ovenschaal","maatbeker","spatel","snijplank","vershoudbak"],
 maaltijdpakket:["knorr","wereldgerecht","maaltijdmix","pakket","honig","naan","taco","wrap"],
 ontbijt:["havermout","kwark","skyr","granola","muesli","ei","brood","fruit"],
 lunch:["wrap","brood","salade","tonijn","kipfilet","hummus","kwark"]
};
function matches(item,query){
 const words=norm(query).split(" ").filter(Boolean);
 if(!words.length)return true;
 const text=norm(typeof item==="string"?item:[item.name,item.category_hint,item.description].filter(Boolean).join(" "));
 return words.every(word=>{
  if(text.includes(word))return true;
  const synonyms=groups[word];
  return Boolean(synonyms?.some(s=>text.includes(norm(s))));
 });
}
root.DealSearch={matches,norm,groups};
if(typeof module!=="undefined"&&module.exports)module.exports=root.DealSearch;
})(typeof window!=="undefined"?window:globalThis);
