const assert=require("node:assert/strict");
const fs=require("node:fs");
const html=fs.readFileSync("recepten/index.html","utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script);assert.doesNotThrow(()=>new Function(script));
for(const id of ["duration","mealprep-filter"]){
 assert.ok(html.includes('id="'+id+'"'),"Filter "+id);
}
for(const x of ["Tot 20 minuten","Tot 30 minuten","Tot 45 minuten","Mealprep: vooruit bereiden"]){
 assert.ok(html.includes(x),"Optie: "+x);
}
assert.ok(script.includes('r=>Number(r.minutes)<=Number(maxMinutes)'),"Bereidingstijdfilter werkt");
assert.ok(script.includes('rs.filter(r=>r.mealprep)'),"Mealpreponderdeel gebruikt echte classificatie");
assert.ok(script.includes('r.mealprep_note'),"Bewaaradvies zichtbaar");
assert.ok(!script.includes("r.prep_ahead?"),"Geen oude onnauwkeurige voorbereidingsbadge");
console.log("Mealprep- en bereidingstijdfilters gecontroleerd.");
