/* Verifieer de UI-logica voor 3 winkels en de vooruitblik op aanbiedingen. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const html=fs.readFileSync("recepten/index.html","utf8");
const code=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(code);
assert.doesNotThrow(()=>new Function(code));
for(const id of ["weekmenu-panel","weekmenu-content","deal-period","cart-panel"]){
 assert.ok(html.includes('id="'+id+'"'),"Ontbrekend element "+id);
}
assert.ok(code.includes('state.data?.upcoming_deals?.[state.store]'),"Toekomstige deals in eigen dataset");
assert.ok(code.includes('d.valid_from===tomorrow'),"Preview alleen morgen geldige acties");
assert.ok(code.includes('valid_from')&&code.includes('Nog niet geldig'),"Startdatum gemarkeerd");
assert.ok(code.includes('m.meals.map'),"Exact dezelfde menu's per winkel");
assert.ok(code.includes('data-weekmenu-choose'),"Eén-klik winkelmand aanwezig");
const a=code.indexOf(' function renderWeekmenu(){');
const b=code.indexOf(' function renderSourceMatches(){',a);
assert.ok(a>=0&&b>a,"Weekmenu renderer aanwezig");
const els={"weekmenu-panel":{hidden:true},"weekmenu-content":{innerHTML:""}};
const state={mode:"recipes",data:{store_names:{ah:"Albert Heijn",jumbo:"Jumbo",lidl:"Lidl"},
weekmenu_advice:{status:"indicative_online_comparison",recipe_count:3,portion_count:12,
 cheapest_store:"lidl",order_cheapest_first:["lidl","jumbo","ah"],
 meals:[{title:"Kip met groenten",cuisine:"Internationaal",category:"Kip",passes_nutrition_preference:true},
 {title:"Zalm met broccoli",cuisine:"Internationaal",category:"Vis",passes_nutrition_preference:true},
 {title:"Tofu roerbak",cuisine:"Thais",category:"Vegetarisch",passes_nutrition_preference:true}],
 stores:{ah:{checkout:44.2,sale_line_count:2},jumbo:{checkout:40.1,sale_line_count:3},lidl:{checkout:35.5,sale_line_count:1}}}
}};
const $=id=>els[id];
const euro=n=>"€ "+n.toFixed(2).replace(".",",");
const esc=x=>String(x||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const f=new Function("state","$","euro","esc",code.slice(a,b)+"return renderWeekmenu")(state,$,euro,esc);
f();
assert.equal(els["weekmenu-panel"].hidden,false);
const txt=els["weekmenu-content"].innerHTML;
for(const word of ["Albert Heijn","Jumbo","Lidl","€ 35,50","Kip met groenten","12 porties","data-weekmenu-choose=\"lidl\""]){
 assert.ok(txt.includes(word),"Missen in overzicht: "+word);
}
state.mode="deals";f();assert.equal(els["weekmenu-panel"].hidden,true);
console.log("Vooruitkijkende deals en vergelijkbaar weekmenu: UI gecontroleerd.");
