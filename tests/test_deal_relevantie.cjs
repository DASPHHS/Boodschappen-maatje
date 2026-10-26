const assert=require("node:assert/strict"),R=require("../recepten/deal_relevantie.js");
assert.equal(R.classify({name:"XXL Nutrition Fitquark Aardbei 200 ml"}),"proteine");
assert.equal(R.classify({name:"Melkunie Protein kwark naturel"}),"proteine");
assert.equal(R.classify({name:"Knorr Wereldgerechten Kip Tandoori 303 g"}),"maaltijdpakket");
assert.equal(R.classify({name:"Jumbo kipfilet 400 g"}),"vers");
assert.equal(R.classify({name:"Jumbo banaan 5 st"}),"overig");
assert.equal(R.bundleInfo({promotion_type:"2+3 gratis"}).required,5);
assert.equal(R.bundleInfo({promotion_type:"2+3 gratis"}).paid,2);
assert.equal(R.bundleInfo({multi_buy_quantity:2,multi_buy_price:5.99}).required,2);
assert.equal(R.bundleInfo({promotion_type:"1+1 gratis"}).required,2);
assert.equal(R.validToday({valid_from:"2026-10-21",valid_until:"2026-10-27"},"2026-10-26"),true);
assert.equal(R.validToday({valid_from:"2026-10-28",valid_until:"2026-11-04"},"2026-10-26"),false);
assert.equal(R.isVerified({discount_verified:false,verified_discount_pct:60}),false);
const ranked=R.sort([{name:"Koekjes",discount_verified:true,verified_discount_pct:65},
{name:"Knorr Wereldgerechten Bami",promotion_type:"2+3 gratis",discount_verified:false},
{name:"XXL Nutrition Fitquark",discount_verified:true,verified_discount_pct:25}]);
assert(ranked[0].name.includes("Fitquark")||ranked[0].name.includes("Knorr"));
assert(ranked[2].name==="Koekjes");
assert(R.reason(ranked.find(x=>x.name.includes("Knorr"))).includes("koop 5"));
console.log("Dealrelevantie: maaltijdpakketten, eiwitproducten, bundelregels en geldigheid OK");
