/* Wekelijkse receptenradar over duizenden bronvermeldingen.
 * Berekende kassaprijzen uitsluitend uit de bestaande prijsengine.
 * Dit model rangschikt BRONIDEEËN, zonder korting/eindgewicht te verzinnen.
 */
(function(root){
"use strict";
const N=s=>String(s||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim();
const TOKEN=v=>" "+N(v)+" ";
const WORDS={
 "garnalen":/(?:garnalen|gamba|scampi|shrimp|prawn)/,
 "kipfilet":/(?:kipfilet|kipfiletjes|chicken\s+breast|kiphaasjes)/,
 "kipgehakt":/(?:kipgehakt|chicken\s+mince)/,
 "kipdij":/(?:kipdij|kippendij|chicken\s+thigh)/,
 "gehakt":/(?:rundergehakt|gehakt|ground\s+beef|minced\s+beef)/,
 "zalm":/(?:zalm|salmon)/,
 "tonijn":/(?:tonijn|tuna)/,
 "tofu":/(?:tofu|tempeh)/,
 "linzen":/(?:linzen|lentils?)/,
 "kikkererwten":/(?:kikkererwten|chickpeas?)/,
 "bonen":/(?:bonen|beans?)/,
 "eieren":/(?:eieren|eggs?)/,
 "naan":/(?:naan|naanbrood|naanbroodjes)/,
 "broccoli":/broccoli/,
 "spinazie":/(?:spinazie|spinach)/,
 "paprika":/(?:paprika|bell\s+peppers?)/,
 "courgette":/(?:courgette|zucchini)/,
 "champignons":/(?:champignons|mushrooms?|paddenstoelen)/,
 "bloemkool":/(?:bloemkool|cauliflower)/,
 "pastinaak":/(?:pastinaak|parsnip)/,
 "boerenkool":/(?:boerenkool|kale)/,
 "spruiten":/(?:spruiten|spruitjes|brussels\s+sprouts)/,
 "wortel":/(?:wortel|wortelen|carrots?)/,
 "tomaten":/(?:tomaten|tomato(?:es)?)/,
 "kokosmelk":/(?:kokosmelk|coconut\s+milk)/,
 "risottorijst":/(?:risottorijst|arborio|carnaroli|risotto)/,
 "rijst":/(?:zilvervliesrijst|rijst|rice|pilav)/,
 "pasta":/(?:pasta|penne|spaghetti|fusilli|macaroni|lasagne|orzo)/,
 "wraps":/(?:wraps?|tortillas?|burritos?|tacos?)/,
 "aardappel":/(?:aardappelen?|potato(?:es)?|krieltjes)/,
 "kwark":/(?:kwark|quark|skyr|kvarg)/,
};
const EXCLUDE_TITLE=/^(?:ontbijt|breakfast|dessert|drank|juice|smoothie|koffie|coffee|cake|koek|chocoladereep|brood\b|milkshake|cookie|snack\b)|\b(?:filter coffee|ice cream|iced coffee|overnight oats)\b/;
const VEG=/(?:broccoli|spinazie|paprika|courgette|champignons|bloemkool|pastinaak|boerenkool|spruiten|wortel|tomaten|groente|spinach|vegetable|salade)/;
const PROTEIN=/(?:kip|chicken|garnalen|shrimp|zalm|salmon|tonijn|tuna|tofu|tempeh|gehakt|beef|bonen|beans|linzen|lentils|kikkererwten|chickpeas|eieren|eggs|vis|fish)/;
const THEME=/(?:tandoori|madras|burrito|taco|risotto|bobotie|roti|teriyaki|korma|paella|shanghai|siam|enchilada|lasagne|bami|nasi|noedels|ramen|orzo)/;
function matchKey(text,key){
 const pattern=WORDS[key];return Boolean(pattern&&new RegExp("\\b(?:"+pattern.source+")\\b","i").test(N(text)));
}
function keys(text){return Object.keys(WORDS).filter(key=>matchKey(text,key))}
function dealClues(deals,date){
 const out=new Map();
 for(const d of deals||[]){
  if(!d||!d.name||!d.valid_until)continue;
  const start=String(d.valid_from||"").slice(0,10),end=String(d.valid_until||"").slice(0,10);
  if(end<date||(start&&start>date))continue;
  const name=N(d.name);
  const kit=/(?:wereldgerecht|wereldgerechten|maaltijdpakket|knorr\s|maaltijdmix|foodtrips)/.test(name);
  if(kit){
    const terms=name.match(new RegExp(THEME.source,"g"))||[];
    for(const topic of terms){
      const key="thema:"+topic;
      if(!out.has(key))out.set(key,{type:"thema",topic,product:d.name,verified:false});
    }
    continue; // Een Knorr Kip Madras-pakket levert GEEN kipvlees.
  }
  for(const key of keys(name)){
    const label=key==="rijst"&&name.includes("risotto")?"risottorijst":key;
    const stored="ingredient:"+label;
    if(!out.has(stored))out.set(stored,{type:"ingredient",key:label,product:d.name,
      verified:d.discount_verified===true});
  }
 }
 return [...out.values()];
}
function shelfKeys(recipes){
 const out=new Map();
 for(const r of recipes||[])for(const l of r.ingredients||[]){
   const key=String(l.key||"");
   const size=Number(l.package_size),price=Number(l.unit_price);
   if(!key||!(size>0)||!(price>0))continue;
   const unitprice=price/size;
   const old=out.get(key);
   if(old===undefined||unitprice<old)out.set(key,unitprice);
 }
 return out;
}
function scoreRecipe(x,clues,known){
 const title=String(x.title_nl||x.title||"");
 const original=String(x.title||"");
 const titleWords=N(title+" "+original);
 const ingredientWords=(x.ingredients||[]).map(i=>typeof i==="string"?i:i.name||"").join(" ");
 const ingredientKeys=keys(ingredientWords);
 const titleKeys=keys(titleWords);
 const usable=new Set(ingredientKeys.length?ingredientKeys:titleKeys);
 const source=String(x.source||"");
 const recognized=[];
 const titleHits=[];
 const themed=[];
 for(const clue of clues){
  if(clue.type==="ingredient"){
   if(ingredientKeys.includes(clue.key))recognized.push(clue);
   else if(titleKeys.includes(clue.key))titleHits.push(clue);
  }else if(clue.type==="thema"&&new RegExp("\\b"+clue.topic+"\\b").test(titleWords))themed.push(clue);
 }
 const staples=[...usable].filter(k=>known.has(k));
 const healthy=VEG.test(titleWords+" "+N(ingredientWords))&&PROTEIN.test(titleWords+" "+N(ingredientWords));
 const minute=Number(x.minutes||0);
 const fast=minute>0&&minute<=45;
 const score=recognized.length*23+titleHits.length*11+themed.length*8+
   Math.min(3,staples.length)*2.7+
   (healthy?7:0)+(fast?4:0)+
   (/hellofresh|francesca|foodies|fitmen|voedingscentrum|budget bytes|meal prep/i.test(source)?3:0)+
   (x.ingredients?.length?4:0);
 const evidence=recognized.length?
   "Actieproduct herkend in broningrediënten; hoeveelheid en maaltijdprijs nog niet bevestigd":
   titleHits.length||themed.length?"Mogelijke actiematch op recepttitel; ingrediënt nog niet geverifieerd":
   "Inspiratie met gangbare ingrediënten; geen gebruikte korting bevestigd";
 return {recipe:x,score,evidence,
    sourceIngredientMatches:recognized,possibleOfferMatches:[...titleHits,...themed],
    shelfMatches:staples,healthyIndicative:healthy,hasOffer:recognized.length+titleHits.length+themed.length>0};
}
function weekly(items,deals,pricedRecipes,options={}){
 const {date="",limit=240,category="all",cuisine="all",format="all",origin="all",meal="Avondeten",maxMinutes="all"}=options;
 const matchCats={meat:["Vlees","Kip"],redmeat:["Vlees"],chicken:["Kip"],fish:["Vis"],vega:["Vegetarisch"]};
 const clues=dealClues(deals,date),known=shelfKeys(pricedRecipes);
 const candidates=[],seen=new Set();
 for(const x of items||[]){
  if(!x||!x.title||x.kind==="collection"||x.category==="Broncollectie")continue;
  const title=N(x.title);
  if(meal==="Avondeten"&&(EXCLUDE_TITLE.test(title)||/\b(?:cake|muffins?|brownies?|dessert|ijs|smoothie|milkshake)\b/.test(title)||x.meal_type&&x.meal_type!=="Avondeten"))continue;
  if(category!=="all"&&matchCats[category]&&!matchCats[category].includes(x.category))continue;
  if(cuisine!=="all"&&x.cuisine!==cuisine)continue;
  if(format!=="all"&&root.ReceptInspiratieRadar?.dishType&&
     root.ReceptInspiratieRadar.dishType(x)!==format)continue;
  if(origin!=="all"){
    const source=String(x.source||"");
    if(origin==="HelloFresh-variant"&&!/hellofresh/i.test(source))continue;
    if(origin!=="HelloFresh-variant"&&source!==origin)continue;
  }
  const mins=Number(x.minutes||0);
  if(maxMinutes!=="all"&&(!(mins>0)||mins>Number(maxMinutes)))continue;
  const uniq=N(x.title)+"|"+N(x.source);
  if(seen.has(uniq))continue;seen.add(uniq);
  const ranked=scoreRecipe(x,clues,known);
  // Productnamen zonder bewijs leveren hoogstens inspiratie op.
  if(ranked.score<4)continue;
  candidates.push(ranked);
 }
 candidates.sort((a,b)=>Number(b.hasOffer)-Number(a.hasOffer)||b.score-a.score||
  String(a.recipe.title).localeCompare(String(b.recipe.title),"nl"));
 const selected=[],groupCount=new Map();
 const pool=candidates.slice(0,1400);
 while(pool.length&&selected.length<Math.min(700,Math.max(24,Number(limit)||240))){
   let index=0,lowest=Infinity;
   for(let i=0;i<Math.min(45,pool.length);i++){
     const c=pool[i],key=(c.recipe.category||"onbekend")+"|"+
       (root.ReceptInspiratieRadar?.dishType?.(c.recipe)||"overig");
     const penalty=(groupCount.get(key)||0)*8;
     const score=i*0.9+penalty+(c.hasOffer?0:4);
     if(score<lowest){index=i;lowest=score}
   }
   const [picked]=pool.splice(index,1);
   selected.push(picked);
   const key=(picked.recipe.category||"onbekend")+"|"+
     (root.ReceptInspiratieRadar?.dishType?.(picked.recipe)||"overig");
   groupCount.set(key,(groupCount.get(key)||0)+1);
 }
 return {total:candidates.length,withOffer:candidates.filter(x=>x.hasOffer).length,
  available:items?.length||0,checkedIngredients:candidates.filter(x=>x.sourceIngredientMatches.length).length,
  items:selected};
}
const api={N,matchKey,keys,dealClues,shelfKeys,scoreRecipe,weekly};
root.WeekselectieEngine=api;
if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof globalThis!=="undefined"?globalThis:this);
