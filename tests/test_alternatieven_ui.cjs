const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('recepten/alternatieven.html','utf8');
const js=html.match(/<script>([\s\S]*?)<\/script>/i)?.[1];
assert(js,'JavaScript in alternatievenpagina ontbreekt');
new vm.Script(js);
for(const id of ['focus','store','statusFilter','sort','query','priced','ideas',
                 'priceCount','ideaCount','morePriced','moreIdeas','status']){
 assert(html.includes('id="'+id+'"'),'Filter ontbreekt: '+id);
}
const start=js.indexOf('const names='),end=js.indexOf('let data=null',start);
assert(start>=0&&end>start,'Hulpfuncties ontbreken');
const api=new Function(js.slice(start,end)+ ';return {money,esc,safeLink,norm};')();
assert.equal(api.money(8.99),'€ 8,99');
assert(api.esc('<img src=x>')==='&lt;img src=x&gt;');
assert.equal(api.safeLink('javascript:alert(1)'),'#');
assert.equal(api.norm('Toníjn'),'tonijn');
assert(html.includes('Volledige kassaprijs'),'Prijszekerheid moet zichtbaar zijn');
assert(html.includes('Prijs niet doorgerekend'),'Bronideeën zonder verzonnen kosten');
assert(html.includes('checked_collections_this_run'),'Laat gecontroleerde brondekking zien');
console.log('Alternatieven-UI, navigatie, bronstatus en prijslabels: OK');
