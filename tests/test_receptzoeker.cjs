const assert=require("node:assert/strict"),fs=require("node:fs"),search=require("../recepten/recipe_search.js");
const s={title:"Volkoren tonijnpasta met zwarte olijven",category:"Vis",cuisine:"Italiaans",complete:true,checkout:11.25,saving:2,ingredients:[{key:"tonijn",label:"tonijn in blik"},{key:"pasta",label:"volkoren pasta"},{key:"olijven",label:"zwarte olijven zonder pit"},{key:"kappertjes",label:"kappertjes"}]};
const wrong={title:"Knorr mix voor kip met rijst",category:"Vegetarisch",complete:true,checkout:7,ingredients:[{key:"rijst",label:"rijst"}]};
assert(search.matches(s,"tonijn pasta"));
assert(search.matches(s,"pasta met tonijn"));
assert(search.matches(s,"tonijn en pasta zwarte olijven"));
assert(search.matches(s,"pasta tonijn kappertjes"));
assert(search.matches(s,"tonijn spaghetti"));
assert(search.matches(s,"tonijn olijf"));
assert(!search.matches(s,"kip pasta"));
assert(!search.matches(s,"tonijn broccoli"));
assert(!search.matches(wrong,"kip en rijst"));
assert(search.matches(s,""));
assert.equal(search.tokens("tonijn en pasta").join(","),"tonijn,pasta");
const healthy={...s,nutrition:{priority:true}};
const unhealthy={...s,nutrition:{priority:false},checkout:13};
assert(search.rank(healthy,unhealthy)<0);
assert(search.rank({...healthy,complete:false,checkout:null},unhealthy)>0);
const html=fs.readFileSync("recepten/index.html","utf8");
for(const id of ["recipe-filters","advanced-filters","search-shortcuts","search","clear-search","selection","cuisine","category","health","sort","duration","origin"]){assert(html.includes('id="'+id+'"'),"Ontbrekende UI: "+id)}
assert(html.includes('src="./recipe_search.js"'));
assert(html.includes('RecipeSearch.matches(r,q)'));
assert(!html.includes('id="tuna-all"'));
assert(!html.includes('70% eiwitgericht'));
assert(html.includes('data-recipe-query="tonijn pasta"'));
const catalog=fs.readFileSync("src/receptenradar_catalog.py","utf8");
for(const term of ["olijven","kappertjes","Volkoren tonijnpasta met zwarte olijven en kappertjes","RECIPE_SOURCES"]){assert(catalog.includes(term),term)}
console.log("Receptzoeker: combinaties, volgorde, veilige matching, filters en bronvermelding OK");
