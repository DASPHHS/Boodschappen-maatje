/* Boodschappen Maatje: meervoudige ingrediëntenzoeker.
 * Alle opgegeven betekenisvolle termen moeten in gerecht OF receptingrediënten
 * voorkomen; volgorde maakt niet uit. Geen matches op losstaande actieproducten.
 */
(function(root){
 "use strict";
 const alias={
  pasta:["pasta","penne","fusilli","spaghetti","macaroni","farfalle","tagliatelle","linguine","volkorenpasta"],
  tonijn:["tonijn","tuna"], olijven:["olijf","olijven","zwarteolijven","groeneolijven"],
  kip:["kip","kipfilet","kipdij","kipgehakt","kipshoarma"],
  gehakt:["gehakt","rundergehakt","kipgehakt"], aardappel:["aardappelen","aardappelschijfjes","krieltjes"],
  rijst:["rijst","zilvervliesrijst","risottorijst"], groenten:["groente","groenten","broccoli","spinazie","bloemkool","paprika"],
  ei:["ei","eieren"], wraps:["wrap","wraps","tortilla","tortillas"], salade:["salade","salades"],
  zalm:["zalm","zalmfilet"], bonen:["bonen","kidneybonen","zwartebonen"], tomaat:["tomaat","tomaten","tomatenblokjes"]
 };
 const stop=new Set(["en","met","of","de","het","een","voor","in","op","bij","van","recept","recepten","ik","wil","graag","lekker","gezond","wat","kan","maken"]);
 function norm(v){
  return String(v||"").toLocaleLowerCase("nl").normalize("NFD")
   .replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim();
 }
 function words(v){return norm(v).split(/\s+/).filter(t=>t&&!stop.has(t))}
 function canonical(t){
  if(t==="zwarte"||t==="groene")return t;
  for(const [key,variants] of Object.entries(alias)){
   if(t===key||variants.includes(t))return key;
  }
  return t;
 }
 function tokens(text){return [...new Set(words(text).map(canonical))]}
 function recipeWords(r){
  // Producttitels van prijsmatches zijn uitgesloten: een Knorr-kipmix maakt
  // geen groenterecept tot een kipgerecht.
  return words([r.title,r.category,r.cuisine,
    ...(r.ingredients||[]).flatMap(x=>[x.label||"",x.key||""])
  ].join(" "));
 }
 function matches(r,query){
  const terms=tokens(query);
  if(!terms.length)return true;
  const bag=recipeWords(r);
  const ingredientWords=words((r.ingredients||[]).flatMap(x=>[x.label||"",x.key||""]).join(" "));
  return terms.every(term=>{
   // Zoektermen die een concreet ingrediënt aanduiden moeten werkelijk in
   // de ingrediëntenlijst voorkomen. 'Knorr mix voor kip' is geen kipvlees.
   const source=Object.prototype.hasOwnProperty.call(alias,term)?ingredientWords:bag;
   return source.some(word=>canonical(word)===term||word===term||
      (word.startsWith(term)&&term.length>=4));
  });
 }
 function score(r){
  // Echte kassaprijzen boven onbevestigde subtotalen. Voordeel is
  // ondersteunend: meer actieproducten is niet per definitie goedkoper.
  const checkout=Number(r.checkout);
  if(!r.complete||!Number.isFinite(checkout)||checkout<=0)return Infinity;
  const saving=Math.max(0,Number(r.saving)||0);
  return checkout-Math.min(saving,checkout*0.3)*0.15;
 }
 function rank(a,b){
  if(Boolean(a.complete)!==Boolean(b.complete))return Number(b.complete)-Number(a.complete);
  const ap=Boolean(a.nutrition?.priority),bp=Boolean(b.nutrition?.priority);
  if(ap!==bp)return Number(bp)-Number(ap);
  return score(a)-score(b)||Number(b.sale_count||0)-Number(a.sale_count||0)||
   Number(a.minutes||999)-Number(b.minutes||999);
 }
 const api={norm,tokens,matches,rank,score};
 root.RecipeSearch=api;
 if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof globalThis!=="undefined"?globalThis:this);
