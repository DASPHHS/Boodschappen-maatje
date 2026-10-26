/* Doorzoekbare externe receptenindex en veilige inspiratie uit huidige aanbiedingen.
 * Recepttitel is geen bewezen ingrediënt en een pakketmix is nooit kip of groenten.
 */
(function(root){
"use strict";
function norm(v){return String(v||"").toLocaleLowerCase("nl").normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim()}
function tokens(v){return norm(v).split(/\s+/).filter(Boolean)}
function hasTerm(text,needle){
 const words=tokens(text);const q=norm(needle);
 return words.some(w=>w===q||(q==="naan"&&/^naan(?:brood|broodjes)?$/.test(w))||(q.length>=5&&w.startsWith(q)));
}
function matchWords(text,query){
 return tokens(query).filter(t=>!["met","en","de","een","in","op","voor","graag"].includes(t))
 .every(t=>hasTerm(text,t));
}
const CATS={chicken:["Kip"],redmeat:["Vlees"],meat:["Kip","Vlees"],fish:["Vis"],vega:["Vegetarisch"]};
function dishType(recipe){
 const title=norm(recipe.title);
 const groups=[["stamppot",/stamppot|hutspot|stoemp/],["curry",/curry|masala|dahl|dal/],
 ["pasta",/pasta|lasagne|orzo|risotto|spaghetti|gnocchi/],
 ["wok",/wok|bami|nasi|roerbak/],["stoof",/stoof|ragout/],
 ["oven",/ovenschotel|traybake|gratin/],["soep",/soep|saoto|ramen/],
 ["rijst",/rijst|paella|pilav/],["wrap",/wrap|burrito|taco|fajita|quesadilla/],
 ["salade",/salade/],["bowl",/bowl/]];
 for(const [key,pat] of groups)if(pat.test(title))return key;
 return "anders";
}
function find(items,options={}){
 const {query="",category="all",cuisine="all",format="all",duration="all",origin="all",meal="all",limit=24}=options;
 if(!norm(query))return {total:0,items:[]}; // Index met duizenden titels niet blind tonen.
 const candidates=[];
 const seen=new Set();
 for(const x of Array.isArray(items)?items:[]){
  if(!x||x.kind==="collection"||!x.title)continue;
  const lowerTitle=norm(x.title);
  if(meal==="Avondeten"&&
   ((x.meal_type&&x.meal_type!=="Avondeten")||
    x.category==="Ontbijt en snacks"||
    /^(?:ontbijt|breakfast|dessert|smoothie|koek|cake|pudding|koffie|coffee|pannenkoek)\b/.test(lowerTitle)||
    /\b(?:filter coffee|chocolademelk|cupcake)\b/.test(lowerTitle)))continue;
  if(meal!=="all"&&meal!=="Avondeten"&&x.meal_type&&x.meal_type!==meal)continue;
  if(category!=="all"&&CATS[category]&&!CATS[category].includes(x.category))continue;
  if(cuisine!=="all"&&x.cuisine!==cuisine)continue;
  if(format!=="all"&&dishType(x)!==format)continue;
  if(duration!=="all"&&!(Number(x.minutes)>0&&Number(x.minutes)<=Number(duration)))continue;
  if(origin!=="all"){
   const isHF=/hello\s*fresh/i.test(String(x.source||""));
   if(origin==="HelloFresh-variant"&&!isHF)continue;
   if(origin!=="HelloFresh-variant"&&String(x.source||"")!==origin)continue;
  }
  const ingredients=(x.ingredients||[]).map(z=>typeof z==="string"?z:z.name||"");
  const titleMatch=matchWords(x.title,query);
  const ingredientMatch=ingredients.length>0&&matchWords(ingredients.join(" "),query);
  const keywordMatch=(x.keywords||[]).length>0&&matchWords(x.keywords.join(" "),query);
  if(!titleMatch&&!ingredientMatch&&!keywordMatch)continue;
  // Per bron en titel één resultaat. Een link naar verwante editie is niet hetzelfde als de eigen kaart.
  const key=norm(x.title)+"|"+norm(x.source);
  if(seen.has(key))continue;seen.add(key);
  const evidence=ingredients.length?"Ingrediënten deels bekend":"Alleen titel/bron geïndexeerd";
  const score=(ingredientMatch?6:0)+(titleMatch?4:0)+(/hello\s*fresh/i.test(String(x.source||""))?2:0)+
   (x.url?0.5:0)+(x.category==="Overig/onbekend"?-1:0);
  candidates.push({recipe:x,evidence,score});
 }
 candidates.sort((a,b)=>b.score-a.score||String(a.recipe.title).localeCompare(String(b.recipe.title),"nl"));
 return {total:candidates.length,items:candidates.slice(0,Math.max(1,Math.min(120,Number(limit)||24)))};
}
const HINTS=[
 {pattern:/\bnaan(?:brood|broodjes)?\b/,label:"Naan",query:"naan",kind:"brood"},
 {pattern:/\b(?:wereldgerechten|wereldgerecht)\b.*\b(?:tandoori)\b|\b(?:tandoori)\b.*\bwereldgerechten\b/,label:"Tandoori-maaltijdpakket",query:"tandoori",kind:"pakket"},
 {pattern:/\b(?:wereldgerechten|wereldgerecht)\b.*\bmadras\b|\bmadras\b.*\bwereldgerechten\b/,label:"Madras-maaltijdpakket",query:"madras",kind:"pakket"},
 {pattern:/\b(?:wereldgerechten|wereldgerecht)\b.*\b(?:burrito|taco|enchilada)\b|\b(?:burrito|taco|enchilada)\b.*\bwereldgerechten\b/,label:"Mexicaans maaltijdpakket",query:"burrito",kind:"pakket"},
 {pattern:/\b(?:wereldgerechten|wereldgerecht)\b.*\brisotto\b|\brisotto\b.*\bwereldgerechten\b/,label:"Risotto-maaltijdpakket",query:"risotto",kind:"pakket"},
 {pattern:/\b(?:wereldgerechten|wereldgerecht)\b.*\b(?:teriyaki|siam)\b|\b(?:teriyaki|siam)\b.*\bwereldgerechten\b/,label:"Aziatisch maaltijdpakket",query:"teriyaki",kind:"pakket"},
 {pattern:/\b(?:pesto)\b/,label:"Pesto",query:"pesto",kind:"saus"},
 {pattern:/\b(?:wraps?|tortillas?)\b/,label:"Wraps",query:"wrap",kind:"brood"},
 {pattern:/\b(?:kokosmelk)\b/,label:"Kokosmelk",query:"curry",kind:"ingredient"},
 {pattern:/\b(?:pastinaak)\b/,label:"Pastinaak",query:"pastinaak",kind:"ingredient"},
 {pattern:/\b(?:champignons|kastanjechampignons)\b/,label:"Champignons",query:"champignons",kind:"ingredient"},
 {pattern:/\b(?:garnalen|gamba|scampi)\b/,label:"Garnalen",query:"garnalen",kind:"ingredient"},
 {pattern:/\b(?:boerenkool|zuurkool)\b/,label:"Stamppotgroenten",query:"stamppot",kind:"ingredient"},
];
function offerIdeas(deals,today,limit=8){
 const found=[],keys=new Set();const now=String(today||"").slice(0,10);
 for(const x of Array.isArray(deals)?deals:[]){
  if(!x?.name||!now)continue;
  const start=String(x.valid_from||"").slice(0,10),end=String(x.valid_until||"").slice(0,10);
  if(!end||end<now||(start&&start>now))continue;
  const label=norm(x.name);
  const hint=HINTS.find(h=>h.pattern.test(label));
  if(!hint||keys.has(hint.query))continue;
  keys.add(hint.query);
  found.push({...hint,product:x.name,url:x.url||"",valid_until:end,
   discount_verified:x.discount_verified===true,
   promotion_type:String(x.promotion_type||"").slice(0,100),
   verified_discount_pct:Number(x.verified_discount_pct)||0});
 }
 const priority={pakket:0,brood:1,saus:2,ingredient:3};
 found.sort((a,b)=>(priority[a.kind]??4)-(priority[b.kind]??4)||
   Number(b.discount_verified)-Number(a.discount_verified)||
   a.label.localeCompare(b.label,"nl"));
 const counts={};
 return found.filter(x=>{
   const max=x.kind==="pakket"?3:x.kind==="ingredient"?3:2;
   if((counts[x.kind]||0)>=max)return false;
   counts[x.kind]=(counts[x.kind]||0)+1;
   return true;
 }).slice(0,Math.max(1,Math.min(20,Number(limit)||8)));
}
const api={norm,hasTerm,matchWords,find,offerIdeas,dishType};
root.ReceptInspiratieRadar=api;
if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof globalThis!=="undefined"?globalThis:this);
