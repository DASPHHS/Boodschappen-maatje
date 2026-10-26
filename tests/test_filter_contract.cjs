const fs=require('node:fs'),assert=require('node:assert/strict'),vm=require('node:vm');
const html=fs.readFileSync('recepten/index.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/i)?.[1];
assert(script,'Recepten-JavaScript ontbreekt');
new vm.Script(script);
for(const key of ['mealtype','cuisine','category','selection','health','duration','format','origin','sort',
                  'deal-category','deal-promotion','deal-status','deal-minimum','deal-period']){
 assert(html.includes('id="'+key+'"'),'Filter ontbreekt: '+key);
}
assert(!script.includes('if(noMatchingPromotions)rs=withoutPromoFilter'),'Actiefilter mag gewone recepten niet als aanbiedingen presenteren');
const first=script.indexOf('function savedSelection()');
const end=script.indexOf(' const emoji=',first);
assert(first>=0&&end>first);
const context={localStorage:{getItem:()=>'{"onjuist":true}'}};
vm.createContext(context);
vm.runInContext(script.slice(first,end)+'\nthis.selection=savedSelection();',context);
assert.equal(context.selection.length,0);
const broken={localStorage:{getItem:()=>'{'}};
vm.createContext(broken);
vm.runInContext(script.slice(first,end)+'\nthis.selection=savedSelection();',broken);
assert.equal(broken.selection.length,0,'Kapotte localStorage mag de site niet blokkeren');
assert(html.includes('./chat.html'),'Chatlink ontbreekt');
assert(html.includes('./boodschappen.html'),'Boodschappenlink ontbreekt');
console.log('Filters, strikte aanbiedingen en robuuste winkelmand: OK');
