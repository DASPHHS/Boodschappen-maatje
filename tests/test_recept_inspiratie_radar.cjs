const assert=require("node:assert/strict");
const radar=require("../recepten/recept_inspiratie_radar.js");
assert.equal(radar.hasTerm("gebakken banaan","naan"),false,"Naan mag niet aan banaan gekoppeld zijn");
assert.equal(radar.hasTerm("naanbrood","naan"),true);
const rows=[
 {title:"Linzencurry met naan",source:"Mijn HelloFresh-archief",category:"Vegetarisch",cuisine:"Indiaas"},
 {title:"Kip uit de wok",source:"Kookschrift",category:"Kip",cuisine:"Thais",
  ingredients:[{name:"garnalen"},{name:"paprika"}]},
 {title:"Baka Bana",source:"Kookschrift",category:"Overig/onbekend",cuisine:"Surinaams"},
 {title:"Linzencurry met naan",source:"Mijn HelloFresh-archief",category:"Vegetarisch",cuisine:"Indiaas"}
];
assert.equal(radar.find(rows,{query:"naan"}).total,1);
assert.equal(radar.find(rows,{query:"garnalen"}).items[0].recipe.title,"Kip uit de wok");
assert.equal(radar.find(rows,{query:"naan",category:"chicken"}).total,0);
assert.equal(radar.find(rows,{query:"",limit:20}).total,0);
const offers=[
 {name:"Knorr Wereldgerechten Kip Tandoori",valid_from:"2026-10-21",valid_until:"2026-10-27",discount_verified:false,
  promotion_type:"2+3 gratis"},
 {name:"Naanbrood 2 st",valid_from:"2026-10-21",valid_until:"2026-10-27",discount_verified:true,verified_discount_pct:30},
 {name:"Knorr Wereldgerechten Kip Madras",valid_from:"2026-10-28",valid_until:"2026-11-03"},
 {name:"Banaan",valid_from:"2026-10-21",valid_until:"2026-10-27"}
];
const ideas=radar.offerIdeas(offers,"2026-10-26");
assert.equal(ideas.length,2);
assert(ideas.some(i=>i.query==="tandoori"));
assert(ideas.some(i=>i.query==="naan"));
assert(!ideas.some(i=>i.query==="madras"),"Toekomstige actie niet vandaag");
assert(!ideas.find(i=>i.query==="tandoori").discount_verified);
console.log("Receptinspiratie: titel-, ingrediënten- en actieherkenning OK");

// De bibliotheek staat echt in de hoofd-Recepten Radar, maar zoekt op verzoek
// zodat duizenden ongeprijsde recepten de actieselectie niet verdringen.
const fs=require("node:fs");
const html=fs.readFileSync("recepten/index.html","utf8");
for(const id of ["personal-weekmenu","weekmenu-panel","offer-inspiration","weekly-highlights",
                 "library-results","library-cards","library-load-more","offer-idea-list"]){
 assert(html.includes('id="'+id+'"'),"Ontbrekende interface: "+id);
}
assert(html.includes('<details id="personal-weekmenu"'),"Persoonlijk weekmenu moet inklapbaar zijn");
assert(html.includes('src="./recept_inspiratie_radar.js"'),"Volledige receptenbibliotheek gekoppeld");
assert(html.includes('fetch("./inspiratie.json"'),"Doorzoek de complete receptenindex");
assert(html.includes('renderOfferIdeas()'));
assert(html.includes('renderLibraryResults()'));
assert(!html.includes('id="weekmenu-panel" class="weekmenu-panel" hidden>\n <summary>Voorbeeldweekmenu'));
const dinner=radar.find([
 {title:"Madras Filter Coffee",source:"Kookboek",category:"Overig/onbekend"},
 {title:"Chicken Madras met paprika",source:"Kookboek",category:"Kip"}],
 {query:"madras",meal:"Avondeten"});
assert.equal(dinner.total,1,"Ontbijtrecepten niet als avondmaaltijd aanbieden");
const many=[
 {name:"champignons",valid_from:"2026-10-21",valid_until:"2026-10-27"},
 {name:"pastinaak",valid_from:"2026-10-21",valid_until:"2026-10-27"},
 {name:"garnalen",valid_from:"2026-10-21",valid_until:"2026-10-27"},
 {name:"kokosmelk",valid_from:"2026-10-21",valid_until:"2026-10-27"},
 {name:"Knorr Wereldgerechten Kip Madras",valid_from:"2026-10-21",valid_until:"2026-10-27"}];
const ranked=radar.offerIdeas(many,"2026-10-26",5);
assert.equal(ranked[0].kind,"pakket","Maaltijdpakket wordt als inspiratie herkend");
assert(ranked.length>=3,"Verschillende groepen behouden");
console.log("Actie-ideeën, grote receptenindex en inklapbaar weekmenu geïntegreerd");
