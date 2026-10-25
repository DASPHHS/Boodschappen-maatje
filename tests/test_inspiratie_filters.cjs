/* Regressiecontrole: keukenfilters, bronvermelding en voorzichtige titelmatches. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const html=fs.readFileSync("recepten/inspiratie.html","utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script,"JavaScript bestaat");
assert.doesNotThrow(()=>new Function(script),"Geldige JavaScript syntax");
for(const id of ["q","cuisine","source","cat","kind","actionstore","sort","cards","status","more"]){
 assert.ok(html.includes('id="'+id+'"'),"Ontbrekend filter: "+id);
}
assert.ok(html.includes("mogelijke matches op recepttitel"),"Geen schijnverificatie");
assert.ok(html.includes("niet publiek")||html.includes("privé"),"Eigen kookboek wordt beschermd");
const start=script.indexOf("const lower=");
const end=script.indexOf("function inferCuisine",start);
assert.ok(start>=0&&end>start,"Actiematcher ontbreekt");
const api=new Function(script.slice(start,end)+"return {offerTitleMatches,lower};")();
assert.equal(api.lower("Café"),"cafe");
const mini={deals:{ah:[
  {name:"AH Kipfilet 600 g",discount_verified:true},
  {name:"AH Boerenkool 500 g",discount_verified:false},
  {name:"AH Broccoli 750 g",discount_verified:true}
],jumbo:[],lidl:[]}};
const apiTest=new Function(script.slice(start,end).replace("let items=[],filtered=[],limit=36,deals=null,meta=null;","let items=[],filtered=[],limit=36,deals="+JSON.stringify(mini)+",meta=null;")+"return {offerTitleMatches};")();
assert.deepEqual(apiTest.offerTitleMatches("Kip met broccoli","ah").sort(),["broccoli","kip"]);
assert.deepEqual(apiTest.offerTitleMatches("Boerenkoolstamppot","ah"),[],"Onbevestigde actie telt niet");
assert.deepEqual(apiTest.offerTitleMatches("Roti zonder expliciet genoemd ingrediënt","ah"),[]);
console.log("Wereldkeukenfilters en voorzichtige actie-matches gecontroleerd.");
