const fs=require("node:fs"),assert=require("node:assert/strict"),vm=require("node:vm");
const html=fs.readFileSync("recepten/watchlist.html","utf8");
const source=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert(source);new vm.Script(source);
const begin=source.indexOf("const P="),end=source.indexOf("function card(");
assert(begin>0&&end>begin);
const context={localStorage:{getItem:()=>null,setItem:()=>{}},Date,URL};
vm.createContext(context);
vm.runInContext(source.slice(begin,end)+"\nthis.api={P,inStore,proteinPerPortion,rows,setSnapshot:x=>snapshot=x};",context);
const {P,inStore,proteinPerPortion,rows,setSnapshot}=context.api;
function p(id){return P.find(x=>x.id===id)}
assert.equal(proteinPerPortion("XXL FIT Yoghurt Granola Vanille",200,"g"),20);
assert.equal(proteinPerPortion("XXL FIT Yoghurt Granola Vanille",400,"g"),20);
assert.equal(proteinPerPortion("Melkunie Protein aardbei kwark",200,"g"),20);
assert.equal(proteinPerPortion("Melkunie Breaker high protein",200,"g"),null,"Breaker 12g mag geen 20g worden");
assert.equal(proteinPerPortion("Hipro Protein Kwark",200,"g"),null,"Geen eiwitclaim zonder productbron");
assert(inStore("Texels Skuumkoppe 0.0",p("skuum0")));
assert(!inStore("Texels Skuumkoppe 0.0",p("skuum")));
assert(inStore("Texels Skuumkoppe 6.0",p("skuum")));
assert(!inStore("Halfvolle melk",p("vollemelk")));
assert(inStore("Jumbo Volle Melk",p("vollemelk")));
assert(!inStore("Fever Tree Ginger Beer",p("gingerbeer")),"Zonder expliciet 0% geen bewezen alcoholvrij");
assert(inStore("Gemberbier alcoholvrij 0.0",p("gingerbeer")));
setSnapshot({stores:{
 ah:{ordinary:[
   ["AH Volle Melk",1.39,1000,"ml","https://example.org/ah"],
   ["AH Halfvolle melk",0.99,1000,"ml","https://example.org/half"],
   ["Melkunie Breaker high protein",1.09,200,"g","https://example.org/breaker"],
   ["XXL Fit Yoghurt Granola Vanille",2.29,200,"g","https://example.org/xxl"]
 ],promotions:[]},
 jumbo:{ordinary:[
   ["Jumbo Volle Melk",1.29,1000,"ml","https://example.org/j"],
   ["Melkunie Protein aardbei kwark",1.59,200,"g","https://example.org/protein"]
 ],promotions:[]},
 lidl:{ordinary:[],promotions:[]}
}});
assert.equal(rows("ah",p("vollemelk")).length,1,"Halfvolle melk onterecht goedgekeurd");
assert.equal(rows("jumbo",p("vollemelk"))[0].perUnit,1.29);
assert.equal(rows("ah",p("knijp")).length,0,"Breaker met 12 g mag niet voldoen");
assert.equal(rows("ah",p("xxl"))[0].protein,20);
assert.equal(rows("ah",p("xxl"))[0].perUnit,1.145);
assert.equal(rows("jumbo",p("highprotein"))[0].protein,20);
const index=fs.readFileSync("recepten/index.html","utf8");
assert(index.includes("bm_recept_favorieten_v1"));
assert(index.includes("id=\"only-favorites\""));
assert(index.includes("data-favorite="));
assert(index.includes("function toggleFavorite("));
assert(index.includes("./watchlist.html"));
assert(index.includes("#source-matches-panel{display:none!important}"));
console.log("Watchlist: min 20g, merken, 0%, supermarktvergelijking en receptfavorieten OK");
