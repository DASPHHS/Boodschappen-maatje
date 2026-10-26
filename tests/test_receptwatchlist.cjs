const assert=require("node:assert/strict");
const fs=require("node:fs");
const W=require("../recepten/watchlist_engine.js");
const html=fs.readFileSync("recepten/watchlist.html","utf8");
const app=fs.readFileSync("recepten/watchlist_app.js","utf8");
const SOURCE="https://www.jumbo.com/producten/xxl-nutrition-fit-yoghurt-granola-aardbei-200g-660840CUP";
const AHXXL="https://www.ah.nl/producten/product/wi583038/xxl-nutrition-fit-yoghurt-protein-strawberry";
const AHPRO="https://www.ah.nl/producten/product/wi555458/ah-protein-kwark-met-yoghurt-framboos";
const MELK="https://www.jumbo.com/producten/melkunie-protein-yoghurt-perzik-framboos-735508ZK";
const p=id=>W.WATCH.find(x=>x.id===id);
assert(p("knijp")&&p("xxl")&&p("highprotein")&&p("on_the_go"));
assert.equal(W.sku(SOURCE),"Jumbo-660840CUP");
assert.equal(W.sku(AHPRO),"AH-wi555458");
assert.equal(W.nutrition("XXL Nutrition Fit Yoghurt Granola Aardbei 200g",200,"g",SOURCE).proteinPerPackage,20);
assert.equal(W.nutrition("AH Protein kwark met yoghurt framboos",200,"g",AHPRO).proteinPerPackage,26);
assert.equal(W.nutrition("XXL Nutrition Fit Yoghurt Granola Aardbei 750g",750,"g",SOURCE),null,"200g-SKU is geen 750g-variant");
assert.equal(W.nutrition("Melkunie Breaker high protein vanille yoghurt",200,"g","https://www.ah.nl/producten/product/wi225290/melkunie-breaker-high-protein-vanille-yoghurt"),null);
assert.equal(W.nutrition("XXL Fit Yoghurt Granola 200g",200,"g","https://example.com/xxl"),null);
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
  ["Texels Skuumkoppe Bier Fles 6 x 300 ml",9.99,1800,"ml","https://www.jumbo.com/sku"]
 ],promotions:[
  ["XXL Nutrition Fit Yoghurt Granola Aardbei 200g",1,200,"g",1.99,2,1.99,"1+1 gratis","2099-10-27",SOURCE,false],
  ["XXL Nutrition Fit Yoghurt Granola Aardbei 200g",0.8,200,"g",1.99,2,null,"1+1 gratis","2099-10-27",SOURCE,false],
  ["Jumbo Volle Melk",0.2,1000,"ml",0.89,2,0.4,"2 voor","2020-01-01","https://www.jumbo.com/vol",false]
 ]},
 lidl:{ordinary:[
  ["Texels Skuumkoppe",5.49,330,"ml","https://boodschaapje.nl/product/6614387"],
  ["Verse volle melk PP",0.94,1000,"ml","https://boodschaapje.nl/product/6606808"]
 ],promotions:[]}
}};
const jumbo=W.bestRows(json,"jumbo",p("xxl"));
assert.equal(jumbo[0].packages,2);
assert.equal(jumbo[0].price,1.99);
assert.equal(jumbo[0].quantity,200);
assert.equal(jumbo[0].pricePerUnit,0.498);
assert.equal(jumbo[0].eurosPer20,0.995);
assert.equal(jumbo[1].packages,1);
const result=W.bestStores(json,p("xxl"));
assert.equal(result.winner.store,"jumbo");
assert.equal(result.stores.ah.best.pricePerUnit,0.995);
assert.equal(W.bestStores(json,p("highprotein")).winner.store,"ah");
assert.equal(W.bestStores(json,p("highprotein")).winner.protein,26);
assert.equal(W.bestStores(json,p("knijp")).winner,null);
assert.equal(W.bestStores(json,p("on_the_go")).winner.store,"jumbo");
assert.equal(W.bestStores(json,p("vollemelk")).winner.store,"jumbo");
assert.equal(W.bestStores(json,p("skuum")).stores.lidl.best,null);
assert.equal(W.bestStores(json,p("skuum")).stores.ah.best.quantity,1800);
const milkNoPromo=W.bestRows(json,"jumbo",p("vollemelk"));
assert.equal(milkNoPromo.length,1,"Verlopen acties niet gebruiken");
for(const name of ["watchlist_engine.js","watchlist_app.js"])assert(html.includes('src="./'+name+'"'));
for(const id of ["watch-grid","toggle-followed","custom","custom-unit","add","freshness","favorites-list","save-status"])assert(html.includes('id="'+id+'"'));
assert(app.includes("bm_favoriete_producten_v1"));
assert(app.includes("Minimaal kassabedrag"));
assert(!html.includes("1799.9999999999998"));
console.log("Watchlist SKU, 1+1, kcal/eiwit, melk, knijpzuivel, Skuumkoppe en weergave: geslaagd");
