const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function script(path){
 const text=fs.readFileSync(path,'utf8');
 const scripts=[...text.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)].map(m=>m[1]);
 assert(scripts.length,'Geen JavaScript in '+path);
 const source=scripts.at(-1);
 new vm.Script(source);
 return source;
}
const source=script('recepten/boodschappen.html');
const start=source.indexOf('const stop='),end=source.indexOf('function compare()');
const context={};vm.createContext(context);
vm.runInContext(source.slice(start,end)+'\nthis.api={inputItems,relevance,pick};',context);
const {inputItems,relevance,pick}=context.api;
for(const [name,qty,unit] of [
 ['volle melk',1000,'ml'],['magere kwark',1000,'g'],
 ['kipfilet',500,'g'],['broccoli',500,'g'],['rijst',500,'g'],
 ['eieren',10,'st'],['bananen',1000,'g'],['yoghurt',1000,'g']
]){
 const x=inputItems(name)[0];
 assert.equal(x.qty,qty,name+' hoeveelheid');
 assert.equal(x.unit,unit,name+' eenheid');
}
const items=inputItems('iets onbekends');
assert.equal(items[0].unit,null,'Onbekende productsoort mag geen onterechte stuksmaat krijgen');
assert(relevance('volle melk','AH Volle Melk')>0);
assert.equal(relevance('volle melk','Arla Lactofree volle melk'),-1);
assert.equal(relevance('volle melk','AH Halfvolle Melk'),-1);
for(const [q,p] of [['blauwe bessen','Hero Fruitspread blauwe bessen'],['blauwe bessen',"Ella s Kitchen baby bosbessen"],['aardbeien','AH Terra Plantaardige soja gurt aardbeien'],['kipfilet','Knorr Trattoria kipfilet romana'],['rundergehakt','AH Half om half gehakt']])assert.equal(relevance(q,p),-1,'Onjuiste boodschappenproductmatch '+q+' / '+p);
const milk=inputItems('volle melk')[0];
vm.runInContext('data='+JSON.stringify({stores:{
 ah:{ordinary:[['AH Volle Melk',1.35,1000,'ml','']],promotions:[]},
 jumbo:{ordinary:[['Jumbo Volle Melk',1.28,1000,'ml','']],promotions:[]},
 lidl:{ordinary:[['Milbona Volle Melk',1.22,1000,'ml','']],promotions:[]}
}}),context);
for(const store of ['ah','jumbo','lidl'])assert(pick(milk,store),'Geen volle melk match: '+store);
const idx=script('recepten/index.html');
const from=idx.indexOf(' const DEAL_CATEGORIES='),to=idx.indexOf(' function offersForPeriod(',from);
assert(from>=0&&to>from,'Dealcategorie module niet gevonden');
const ctx={};vm.createContext(ctx);
vm.runInContext(idx.slice(from,to)+'\nthis.api={dealCategory,groupDealVariants};',ctx);
const category=name=>ctx.api.dealCategory({name});
assert.equal(category('Knorr Maaltijdmix kip madras'),'pantry');
assert.equal(category('Knorr Cup-a-soup Chinese kip'),'pantry');
assert.equal(category('Glade Geurglas vanille vegan raapzaadwas'),'care');
assert.equal(category('Jumbo Kipshoarma 750 g'),'protein');
const deals=[
 {name:'Robijn Color kokos wasmiddel',price:6.99,valid_from:'2026-10-26',valid_until:'2026-11-01',discount_verified:true,url:'https://example.org/a'},
 {name:'Robijn Color paradise secret wasmiddel',price:6.99,valid_from:'2026-10-26',valid_until:'2026-11-01',discount_verified:true,url:'https://example.org/b'},
 {name:'Robijn Color kokos wasmiddel',price:6.99,valid_from:'2026-10-26',valid_until:'2026-11-01',discount_verified:true,url:'https://example.org/a'}
];
const grouped=ctx.api.groupDealVariants(deals);
assert.equal(grouped.length,1);
assert.equal(grouped[0].variantNames.length,2);
console.log('Alle generieke zoektermen, varianten en dealgroepering: OK');
