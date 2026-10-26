const assert=require('node:assert/strict'),H=require('../recepten/shared_recipe_hits.js');
const row={title:'Knolselderijstamppot met boerenworst',search_text:'knolselderij aardappelen boerenworst spinazie kastanjechampignons',category:'Vlees',cuisine:'Nederlands',minutes:null,has_possible_offer:true};
assert.equal(H.select([row],{query:'knolselderij boerenworst'}).length,1);
assert.equal(H.select([row],{category:'vega'}).length,0);
assert.equal(H.select([row],{duration:'30'}).length,0);
assert.equal(H.select([row],{selection:'promos'}).length,0);
assert.equal(H.select([row],{strictHealth:true}).length,0);
assert.equal(H.select([row],{meal:'Ontbijt'}).length,0);
assert.equal(H.select([row],{format:'wrap'}).length,0);
assert.equal(H.select([{...row,has_possible_offer:false}],{onlyShared:true}).length,1);
assert.equal(H.select([{...row,has_possible_offer:false}],{}).length,0);
console.log('Gedeelde HelloFresh-hits: zoekcombinatie, filters en onbekende prijs/tijd correct');

const ingredientOnly={title:"Romige vegetarische curry",search_text:"romige vegetarische curry",ingredient_names:["garnalen","pastinaak"],category:"Vis",cuisine:"Indiaas",has_possible_offer:false};
assert.equal(H.select([ingredientOnly],{query:"garnalen"}).length,1,"Zoek op broningrediënt, niet alleen op titel");
assert.equal(H.select([ingredientOnly],{query:"pastinaak"}).length,1);
const stew={...ingredientOnly,title:"Pastinaakstamppot",ingredient_names:["pastinaak"]};
assert.equal(H.select([stew],{query:"pastinaak",format:"stamppot"}).length,1);
console.log("HelloFresh: zoeken op ingrediënten en stamppotfilter OK");
