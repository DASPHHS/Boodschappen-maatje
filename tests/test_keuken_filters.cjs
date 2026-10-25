/* Regressietests voor het gezamenlijke wereldkeukenfilter in de groene hoofdsite. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const html=fs.readFileSync("recepten/index.html","utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script,"Website heeft JS");
assert.doesNotThrow(()=>new Function(script));
for(const id of ["cuisine","cuisine-shortcuts","source-priority","source-count",
                 "source-matches","source-loadmore","source-more-link"]){
  assert.ok(html.includes('id="'+id+'"'),"Ontbreekt: "+id);
}
assert.ok(!html.includes('<option value="Latijns-Amerikaans">'),"Verouderde continentfilter");
assert.ok(!html.includes('<option value="Overig">Overig</option>'),"Verouderde restcategorie");
const begin=script.indexOf(" function updateCuisineOptions(){");
const end=script.indexOf(" function renderAudit(){",begin);
assert.ok(begin>=0&&end>begin,"Dynamische keukenlogica aanwezig");
const elements={
  cuisine:{value:"all",innerHTML:""},
  "cuisine-shortcuts":{innerHTML:""},
  "source-matches-panel":{hidden:true},
  "source-more-link":{href:""},
  "source-count":{textContent:""},
  "source-loadmore":{hidden:true,textContent:""},
  "source-matches":{innerHTML:""},
  search:{value:""},
  "source-priority":{value:"promising"},
};
const state={store:"ah",mode:"recipes",sourceVisible:8,
  data:{recipes:{ah:[{cuisine:"Surinaams"},{cuisine:"Nederlands"}]},source_recipe_matches:{
   ah:{candidates:[
     {title:"Chicken Bowls with Rice and Lentils",title_nl:"Kipbowls met rijst en linzen",
      source:"The Meal Prep Manual",cuisine:"Internationaal",match_terms:["kip","linzen"],
      health_priority:"kansrijk voor controle",matched_title_terms:2,url:"https://example.com/r"},
     {title:"Surinaamse roti met kip",source:"SurinamCooking",cuisine:"Surinaams",
      health_priority:"kansrijk voor controle",match_terms:["kip"],
      matched_title_terms:1,url:"https://example.com/roti"},
     {title:"Chicken Bacon Broccoli Alfredo Spaghetti",source:"Wikibooks",
      cuisine:"Internationaal",match_terms:["kip","broccoli"],
      health_priority:"lage prioriteit",matched_title_terms:2,url:"https://example.com/alfredo"},
     {title:"Marokkaanse tajine met kip",source:"Foodies",cuisine:"Marokkaans",
      health_priority:"nader beoordelen",matched_title_terms:1,match_terms:["kip"],
      url:"https://example.com/tajine"}
   ]}
 }}};
const esc=x=>String(x||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const $=id=>{assert.ok(elements[id],"Onbekend id "+id);return elements[id]};
const safeURL=x=>x;
const helpers=new Function("state","$","esc","safeURL",
  script.slice(begin,end)+"return {updateCuisineOptions,renderSourceMatches};")(state,$,esc,safeURL);
helpers.updateCuisineOptions();
assert.ok(elements.cuisine.innerHTML.includes("Surinaams (1 geprijsd · 1 inspiratie)"));
assert.ok(elements.cuisine.innerHTML.includes("Marokkaans (0 geprijsd · 1 inspiratie)"));
assert.ok(elements.cuisine.innerHTML.includes("Internationaal"));
assert.ok(elements["cuisine-shortcuts"].innerHTML.includes("Surinaams"));

helpers.renderSourceMatches();
assert.ok(elements["source-matches"].innerHTML.includes("Kipbowls met rijst en linzen"));
assert.ok(elements["source-matches"].innerHTML.includes("Originele titel: Chicken Bowls"));
assert.ok(!elements["source-matches"].innerHTML.includes("Chicken Bacon Broccoli Alfredo"));
assert.equal(elements["source-loadmore"].hidden,true);
elements.cuisine.value="Surinaams";
helpers.renderSourceMatches();
assert.ok(elements["source-matches"].innerHTML.includes("Surinaamse roti"));
assert.ok(!elements["source-matches"].innerHTML.includes("Kipbowls"));
assert.ok(elements["source-more-link"].href.includes("cuisine=Surinaams"));
elements.cuisine.value="Marokkaans";
helpers.renderSourceMatches();
assert.ok(elements["source-matches"].innerHTML.includes("Marokkaanse tajine"));
elements["source-priority"].value="strict";
helpers.renderSourceMatches();
assert.ok(elements["source-matches"].innerHTML.includes("Geen kandidaten voor deze keuze"));
assert.equal(elements["source-matches-panel"].hidden,false);
console.log("Keukens, vertaalde titels, gezondheidsvoorselectie en bronfilters OK");
