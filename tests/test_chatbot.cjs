const fs=require('node:fs'),assert=require('node:assert/strict'),vm=require('node:vm');
const html=fs.readFileSync('recepten/chat.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/i)?.[1];
assert(script,'Chatscript ontbreekt');
new vm.Script(script);
for(const path of ['docs/recepten/chat.html']){
 const page=fs.readFileSync(path,'utf8');
 assert.equal(page,html,'Pages en bronbestand moeten identiek zijn');
}
const start=script.indexOf('const $='),end=script.indexOf('$("form").addEventListener');
assert(start>=0&&end>start,'Pure chatfuncties moeten geladen kunnen worden');
const context={};vm.createContext(context);
vm.runInContext(script.slice(start,end)+
 '\nthis.api={detectStore,detectCuisine,parseShopping,productFit,findPrices,searchRecipes,searchDeals,interpret};',context);
const api=context.api;
assert.equal(api.detectStore('Wat kost melk bij Jumbo?'),'jumbo');
assert.equal(api.detectCuisine('Italiaanse recepten bij AH'),'Italiaans');
assert.equal(api.parseShopping('Wat kost volle melk 2 liter?').quantity,2000);
assert.equal(api.parseShopping('Wat kost volle melk 2 liter?').unit,'ml');
assert.equal(api.productFit('volle melk','Arla Lactofree volle melk'),-1);
assert.equal(api.productFit('volle melk','Jumbo Halfvolle Melk'),-1);
const data={stores:{
 ah:{ordinary:[['AH Volle Melk 1 liter',1.25,1000,'ml','https://example.org/ah']],promotions:[]},
 jumbo:{ordinary:[['Jumbo Volle Melk 1 liter',1.19,1000,'ml','https://example.org/jumbo']],promotions:[]},
 lidl:{ordinary:[['Lidl Volle Melk 1 liter',1.15,1000,'ml','https://example.org/lidl']],promotions:[]}
}};
const catalog={recipes:{
 ah:[],jumbo:[{
  id:'1',title:'Kip met broccoli',category:'Kip',cuisine:'Nederlands',
  checkout:8.50,complete:true,minutes:25,sale_count:2,
  nutrition:{priority:true},ingredients:[{label:'kipfilet',product:'Jumbo kipfilet'},{label:'broccoli',product:'broccoli'}]
 }],lidl:[]
},deals:{ah:[],jumbo:[],lidl:[]}};
vm.runInContext('prices='+JSON.stringify(data)+';recipes='+JSON.stringify(catalog),context);
assert.equal(api.findPrices('volle melk 2 liter')[0].total,2.3);
assert.equal(api.findPrices('volle melk 2 liter').length,3);
const result=api.interpret('Goedkoopste gezonde recepten bij Jumbo');
assert(result.lines?.some(x=>x.includes('Kip met broccoli')),'Receptantwoord ontbreekt');
const missing=api.interpret('Wat kost een onbestaand product 3 kg?');
assert(/geen betrouwbare prijs/i.test(missing.text));
const byStore=api.interpret('Recepten bij AH');
assert(!byStore.lines,'Geen fictieve recepten bij AH');
console.log('Chat: syntax, publicatie, querybegrip, prijscontrole, receptselectie: OK');
