const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('recepten/index.html','utf8');
const docs=fs.readFileSync('docs/recepten/index.html','utf8');
assert.equal(html,docs,'Bron- en publicatiepagina moeten gelijk zijn');
const code=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert(code,'Inline paginalogica ontbreekt');
new vm.Script(code);
for(const id of ['nav-recipes','nav-deals','nav-cart','cart-panel','cart-count','cart','category','cuisine'])
 assert(html.includes('id="'+id+'"'),'Vereist onderdeel ontbreekt: '+id);
assert(html.includes('data-cart-recipe'),'Geselecteerde recepten moeten open kunnen');
assert(html.includes('l.url?'), 'Productlink voor bronproducten ontbreekt');
assert(html.includes('nav-deals").addEventListener'), 'Actiesnavigatie niet aangesloten');
assert(html.includes('nav-cart").addEventListener'), 'Winkelmandnavigatie niet aangesloten');
assert(!html.includes('Zoek echte recepten en kookboeken'),'Onnodige bronzoeker moet weg');
assert(html.includes('Koken met voordeel'),'Eenvoudige kop ontbreekt');
console.log('Eenvoudige navigatie en winkelmand contract geslaagd');
