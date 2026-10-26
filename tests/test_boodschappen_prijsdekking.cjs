const fs=require('node:fs'),assert=require('node:assert/strict'),vm=require('node:vm');
const html=fs.readFileSync('recepten/boodschappen.html','utf8');
const scripts=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)].map(m=>m[1]);
assert(scripts.length,'script ontbreekt');
const source=scripts.at(-1);
new vm.Script(source);
const start=source.indexOf('const stop='),end=source.indexOf('function compare()');
assert(start>=0&&end>start);
const context={};vm.createContext(context);
vm.runInContext(source.slice(start,end)+'\nthis.test={inputItems,relevance,pick};',context);
const {inputItems,relevance,pick}=context.test;
const milk=inputItems('volle melk')[0];
assert.equal(milk.qty,1000);
assert.equal(milk.unit,'ml');
assert.equal(inputItems('volle melk 2 liter')[0].qty,2000);
assert(relevance('volle melk','Jumbo Volle Melk 1 liter')>=0);
assert.equal(relevance('volle melk','Arla Lactofree volle melk 3-pack'),-1);
assert.equal(relevance('volle melk','Jumbo Halfvolle Melk'),-1);
assert.equal(relevance('volle melk','Havermelk'),-1);
const stores={ah:{ordinary:[['AH Volle Melk',1.39,1000,'ml','']],promotions:[]},
jumbo:{ordinary:[['Jumbo Volle Melk',1.29,1000,'ml','']],promotions:[]},
lidl:{ordinary:[['Milbona Volle Melk',1.19,1000,'ml','']],promotions:[]}};
vm.runInContext('data='+JSON.stringify({stores}),context);
for(const key of ['ah','jumbo','lidl'])assert(context.test.pick(milk,key),'Geen match bij '+key);
console.log('Melkparser, variantenfilter en 3 supermarktprijzen: OK');
