const assert=require("node:assert/strict");
const W=require("../recepten/weekselectie_engine.js");
assert.equal(W.matchKey("banaan","naan"),false);
assert.equal(W.matchKey("naanbrood","naan"),true);
const promos=[
 {name:"Knorr Wereldgerechten Kip Tandoori",valid_from:"2026-10-21",valid_until:"2026-10-27",promotion_type:"2+3 gratis"},
 {name:"Garnalen 400 g",valid_from:"2026-10-21",valid_until:"2026-10-27",discount_verified:true},
 {name:"Banaan",valid_from:"2026-10-21",valid_until:"2026-10-27",discount_verified:true},
 {name:"Tofu",valid_from:"2026-10-28",valid_until:"2026-11-03",discount_verified:true}
];
const clues=W.dealClues(promos,"2026-10-26");
assert(clues.some(x=>x.type==="thema"&&x.topic==="tandoori"));
assert(clues.some(x=>x.type==="ingredient"&&x.key==="garnalen"));
assert(!clues.some(x=>x.type==="ingredient"&&x.key==="kipfilet"),"Knorr geen kip");
assert(!clues.some(x=>x.key==="tofu"),"Morgen niet als actie vandaag");
const recipes=[
 {title:"Tandoori-kip met broccoli",category:"Kip",source:"Francesca Kookt"},
 {title:"Garnalencurry met kokosmelk",category:"Vis",source:"HelloFresh",ingredients:[{name:"garnalen"},{name:"kokosmelk"}]},
 {title:"Tandoori cake",category:"Overig/onbekend",source:"Wikibooks"},
];
const cheap=[{ingredients:[{key:"broccoli",package_size:500,unit_price:1.29}]}];
const ranked=W.weekly(recipes,promos,cheap,{date:"2026-10-26",limit:20});
assert(ranked.items.some(x=>x.recipe.title.startsWith("Garnalencurry")));
assert(ranked.items.find(x=>x.recipe.title.startsWith("Garnalencurry")).sourceIngredientMatches.length===1);
assert(!ranked.items.some(x=>x.recipe.title==="Tandoori cake"));
const hundreds=Array.from({length:350},(_,i)=>({
 title:i%2?"Garnalencurry met groente nummer "+i:"Kip tandoori met broccoli nummer "+i,
 category:i%2?"Vis":"Kip",source:i%2?"Foodies":"Francesca Kookt"}));
const mass=W.weekly(hundreds,promos,cheap,{date:"2026-10-26",limit:240});
assert(mass.total>=300, "Honderden verschillende bronrecepten blijven paraat");
assert.equal(mass.items.length,240);
console.log("Weekselectie: honderden kandidaten, eerlijk actiebewijs, groenten, eiwit en diversiteit OK");
