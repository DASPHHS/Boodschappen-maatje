/* Transparantiecontrole voor de gepubliceerde datastatus. */
const assert=require("node:assert/strict"),fs=require("node:fs");
const html=fs.readFileSync("recepten/status.html","utf8");
const js=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(js,"JavaScript aanwezig");
assert.doesNotThrow(()=>new Function(js),"Geldige browsercode");
for(const keyword of ["verified_discounts","upcoming_promotion_mentions",
 "external_recipe_strictly_verified","weekmenu_status",
 "other_stores_automatically_priced","local_inventory_checked",
 "email_delivery_verified_by_this_scan"]){
 assert.ok(js.includes(keyword),"Ontbrekende status: "+keyword);
}
const site=fs.readFileSync("recepten/index.html","utf8");
assert.ok(site.includes('./status.html'),"Statuslink op hoofdsite aanwezig");
const source=fs.readFileSync("src/receptenradar_v2.py","utf8");
assert.ok(source.includes('ROOT/"recepten"/"status.json"'));
assert.ok(source.includes('"verified_discounts"'));
console.log("Leesbare scanstatus en expliciete incomplete dekking gecontroleerd.");
