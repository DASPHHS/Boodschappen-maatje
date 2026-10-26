const assert=require("node:assert/strict");
const fs=require("node:fs");
const W=require("../recepten/watchlist_engine.js");
const html=fs.readFileSync("recepten/watchlist.html","utf8");
const app=fs.readFileSync("recepten/watchlist_app.js","utf8");
const SOURCE="https://www.jumbo.com/producten/xxl-nutrition-fit-yoghurt-granola-aardbei-200g-660840CUP";
const AHXXL="https://www.ah.nl/producten/product/wi583038/xxl-nutrition-fit-yoghurt-protein-strawberry";
const AHPRO="https://www.ah.nl/producten/product/wi555458/ah-protein-kwark-met-yoghurt-framboos";
const MELK="https://www.jumbo.com/producten/melkunie-protein-yoghurt-perzik-framboos-735508ZK";
const POUCH="https://www.jumbo.com/producten/zuivelhoeve-xxl-nutrition-fit-quark-strawberry-protein-quark-205-g-685838ZK";
const p=id=>W.WATCH.find(x=>x.id===id);
const TEST_DAY="2026-10-26";
assert(p("knijp")&&p("xxl")&&p("highprotein")&&p("on_the_go"));
assert.equal(W.sku(SOURCE),"Jumbo-660840CUP");
assert.equal(W.sku(AHPRO),"AH-wi555458");
assert.equal(W.nutrition("XXL Nutrition Fit Yoghurt Granola Aardbei 200g",200,"g",SOURCE).proteinPerPackage,20);
assert.equal(W.nutrition("AH Protein kwark met yoghurt framboos",200,"g",AHPRO).proteinPerPackage,26);
assert.equal(W.nutrition("XXL Nutrition Fit Yoghurt Granola Aardbei 750g",750,"g",SOURCE),null,"200g-SKU is geen 750g-variant");
const XL750="https://www.jumbo.com/producten/xxl-nutrition-fit-yoghurt-aardbei-750g-735993EM";
assert.equal(W.nutrition("XXL Nutrition Fit Yoghurt Aardbei 750g",750,"g",XL750).proteinPerPackage,75);
assert.equal(W.nutrition("XXL Nutrition Fit Yoghurt Aardbei 750g",750,"g",XL750).serving,200);
assert.equal(W.nutrition("XXL Nutrition Fit Yoghurt Aardbei 750g",750,"g",XL750).proteinPerServing,20);
assert.equal(W.nutrition("Melkunie Breaker high protein vanille yoghurt",200,"g","https://www.ah.nl/producten/product/wi225290/melkunie-breaker-high-protein-vanille-yoghurt"),null);
assert.equal(W.nutrition("XXL Fit Yoghurt Granola 200g",200,"g","https://example.com/xxl"),null);
assert(W.matchProduct("Zuivelhoeve XXL Nutrition Fit Quark Strawberry Protein Quark 205g",p("knijp"),POUCH));
assert.equal(W.nutrition("Zuivelhoeve XXL Nutrition Fit Quark Strawberry Protein Quark 205g",205,"g",POUCH).proteinPerPackage,25);
assert(W.matchProduct("Melkunie Protein Yoghurt perzik framboos",p("on_the_go"),MELK));
assert(!W.matchProduct("Melkunie Protein Yoghurt perzik framboos",p("knijp"),MELK));
assert(!W.matchProduct("Halfvolle melk",p("vollemelk")));
assert(W.matchProduct("Jumbo Volle Melk",p("vollemelk")));
assert(W.matchProduct("Texels Skuumkoppe speciaalbier 6-pack",p("skuum")));
assert(!W.matchProduct("Texels Skuumkoppe 0.0 6-pack",p("skuum")));
assert(W.matchProduct("Texels Skuumkoppe 0.0 6-pack",p("skuum0")));
assert(W.matchProduct("Grace Ginger Beer Alcoholvrij 330 ML",p("gingerbeer")));
assert(!W.matchProduct("Grace Ginger Beer zonder vermelding 330 ML",p("gingerbeer")));
assert(W.volumeConsistent("Texels Skuumkoppe speciaalbier 6-pack",1799.9999999999998,"ml",7.04,p("skuum")));
assert(!W.volumeConsistent("Texels Skuumkoppe",330,"ml",5.49,p("skuum")));
const json={updated_at:new Date().toISOString(),stores:{
 ah:{ordinary:[
  ["XXL Nutrition Fit yoghurt protein strawberry",1.99,200,"g",AHXXL],
  ["AH Protein kwark met yoghurt framboos",0.99,200,"g",AHPRO],
  ["De Zaanse Hoeve Volle melk",1.05,1000,"ml","https://www.ah.nl/melk"],
  ["Texels Skuumkoppe speciaalbier 6-pack",7.04,1799.9999999999998,"ml","https://www.ah.nl/sku"],
  ["Melkunie Breaker high protein vanille yoghurt",1.59,200,"g","https://www.ah.nl/producten/product/wi225290/melkunie-breaker-high-protein-vanille-yoghurt"]
 ],promotions:[]},
 jumbo:{ordinary:[
  ["XXL Nutrition Fit Yoghurt Granola Aardbei 200g",1.99,200,"g",SOURCE],
  ["Jumbo Volle Melk",0.89,1000,"ml","https://www.jumbo.com/vol"],
  ["Melkunie Protein Yoghurt perzik framboos",1.79,200,"g",MELK],
  ["Zuivelhoeve XXL Nutrition Fit Quark Strawberry Protein Quark 205g",1.79,205,"g",POUCH],
  ["Texels Skuumkoppe Bier Fles 6 x 300 ml",9.99,1800,"ml","https://www.jumbo.com/sku"]
 ],promotions:[
  ["XXL Nutrition Fit Yoghurt Granola Aardbei 200g",1,200,"g",1.99,2,1.99,"1+1 gratis","2099-10-27",SOURCE,false],
  ["XXL Nutrition Fit Yoghurt Granola Aardbei 200g",0.8,200,"g",1.99,2,null,"1+1 gratis","2099-10-27",SOURCE,false],
  ["Zuivelhoeve XXL Nutrition Fit Quark Strawberry Protein Quark 205g",0.895,205,"g",1.79,2,1.79,"1+1 gratis","2099-10-27",POUCH,false],
  ["Jumbo Volle Melk",0.2,1000,"ml",0.89,2,0.4,"2 voor","2020-01-01","https://www.jumbo.com/vol",false]
 ]},
 lidl:{ordinary:[
  ["Texels Skuumkoppe",5.49,330,"ml","https://boodschaapje.nl/product/6614387"],
  ["Verse volle melk PP",0.94,1000,"ml","https://boodschaapje.nl/product/6606808"]
 ],promotions:[]}
}};
const jumbo=W.bestRows(json,"jumbo",p("xxl"),TEST_DAY);
assert.equal(jumbo[0].packages,2);
assert.equal(jumbo[0].price,1.99);
assert.equal(jumbo[0].promoKind,"1+1 gratis");
assert.equal(jumbo[0].discountPct,50);
assert.equal(jumbo[0].previousTotal,3.98);
assert.equal(jumbo[0].savings,1.99);
assert.equal(jumbo[0].validUntil,"2099-10-27");

assert.equal(jumbo[0].quantity,200);
assert.equal(jumbo[0].pricePerUnit,0.498);
assert.equal(jumbo[0].eurosPer20,0.995);
assert.equal(jumbo[1].packages,1);
const result=W.bestStores(json,p("xxl"),TEST_DAY);
assert.equal(result.winner.store,"jumbo");
assert.equal(result.stores.ah.best.pricePerUnit,0.995);
assert.equal(W.bestStores(json,p("highprotein"),TEST_DAY).winner.store,"jumbo");
assert.equal(W.bestStores(json,p("highprotein"),TEST_DAY).winner.protein,25);
assert.equal(W.bestStores(json,p("highprotein"),TEST_DAY).stores.ah.best.protein,26);
const AH450="https://www.ah.nl/producten/product/wi585919/ah-protein-kwark-met-yoghurt-framboos";
assert.equal(W.nutrition("AH Protein kwark met yoghurt framboos",450,"g",AH450).proteinPerPackage,45);
assert.equal(W.nutrition("AH Protein kwark met yoghurt framboos",450,"g",AH450).proteinPerServing,20);
const ahVariants=W.bestRows(json,"ah",p("highprotein"),TEST_DAY);
assert(ahVariants.some(x=>x.sku==="AH-wi555458"&&x.price===0.95));
assert(ahVariants.some(x=>x.sku==="AH-wi556289"&&x.price===1.39));
assert(ahVariants.some(x=>x.sku==="AH-wi585919"&&x.price===1.99&&x.quantity===450));
assert(ahVariants.some(x=>x.sku==="AH-wi585929")===true || W.bestRows(json,"ah",p("knijp"),TEST_DAY).some(x=>x.sku==="AH-wi585929"));
assert.equal(W.bestRows(json,"ah",p("highprotein"),"2026-10-28").some(x=>x.verifiedDirect),false);

assert.equal(W.bestStores(json,p("knijp"),TEST_DAY).winner.store,"jumbo");
assert.equal(W.bestStores(json,p("knijp"),TEST_DAY).winner.price,1.79);
assert.equal(W.bestStores(json,p("knijp"),TEST_DAY).winner.packages,2);
assert.equal(W.bestStores(json,p("on_the_go"),TEST_DAY).winner.store,"jumbo");
assert.equal(W.bestStores(json,p("vollemelk"),TEST_DAY).winner.store,"jumbo");
assert.equal(W.bestStores(json,p("skuum"),TEST_DAY).stores.lidl.best,null);
const bulk=JSON.parse(JSON.stringify(json));
bulk.stores.jumbo.ordinary.push(["XXL Nutrition Fit Yoghurt Aardbei 750g",3.99,750,"g",XL750]);
bulk.stores.jumbo.promotions.push(["XXL Nutrition Fit Yoghurt Aardbei 750g",1.995,750,"g",3.99,2,3.99,"1+1 gratis","2099-10-27",XL750,false]);
assert.equal(W.bestStores(bulk,p("xxl"),TEST_DAY).winner.price,3.99);
assert.equal(W.bestStores(bulk,p("xxl"),TEST_DAY).winner.quantity,750);
assert.equal(W.bestStores(bulk,p("xxl"),TEST_DAY).winner.protein,75);
assert.equal(W.bestStores(bulk,p("xxl"),TEST_DAY).winner.eurosPer20,0.532);
const large=W.bestStores(bulk,p("xxl"),TEST_DAY);
assert.equal(large.stores.jumbo.regular.sku,large.stores.jumbo.best.sku,
 "Geen verkeerde 205g-losseprijs bij de 750g-voordeelbak tonen");
const noAction=W.bestRows(bulk,"jumbo",p("xxl"),"2100-01-01");
assert(noAction.every(item=>!item.discount),
 "Actie mag niet na einddatum blijven gelden");


assert.equal(W.bestStores(json,p("skuum"),TEST_DAY).stores.ah.best.quantity,1800);
const milkNoPromo=W.bestRows(json,"jumbo",p("vollemelk"),TEST_DAY);
assert.equal(milkNoPromo.length,1,"Verlopen acties niet gebruiken");
for(const name of ["watchlist_engine.js","watchlist_app.js"])assert(html.includes('src="./'+name+'"'));
for(const id of ["watch-grid","toggle-followed","custom","custom-unit","add","freshness","favorites-list","save-status"])assert(html.includes('id="'+id+'"'));
assert(app.includes("bm_favoriete_producten_v1"));
assert(app.includes("Minimaal kassabedrag"));
assert(!html.includes("1799.9999999999998"));
console.log("Watchlist SKU, 1+1, kcal/eiwit, melk, knijpzuivel, Skuumkoppe en weergave: geslaagd");
