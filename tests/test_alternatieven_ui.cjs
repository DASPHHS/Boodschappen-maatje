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
const begin=js.indexOf('function bestRecipePerTitle('),finish=js.indexOf('function filteredPriced(',begin);
assert(begin>=0&&finish>begin,'Ontdubbeling per winkel ontbreekt');
const bestRecipePerTitle=new Function('norm',js.slice(begin,finish)+';return bestRecipePerTitle;')(api.norm);
const samples=[
 {title:'Tonijnpasta',store:'ah',complete:true,checkout:7.89,health_priority:true},
 {title:'Tonijnpasta',store:'jumbo',complete:true,checkout:6.99,health_priority:true},
 {title:'Tonijnpasta',store:'lidl',complete:false,checkout:null,health_priority:true},
 {title:'Tonijnwraps',store:'jumbo',complete:true,checkout:5.55,health_priority:false}
];
const grouped=bestRecipePerTitle(samples,'all');
assert.equal(grouped.length,2,'Elke maaltijd één keer tonen');
const tuna=grouped.find(x=>x.title==='Tonijnpasta');
assert.equal(tuna.store,'jumbo','Goedkoopste volledig geprijsde winkel tonen');
assert.equal(tuna.comparisons.length,3,'Andere supermarktprijzen blijven beschikbaar');
assert.equal(bestRecipePerTitle(samples,'ah').length,4,'Winkelgerichte lijst mag niet onterecht dedupliceren');
assert(html.includes('<option value="all" selected>Alle ingrediënten</option>'),'Standaard geen enkel specifiek ingrediënt bevoordelen');
for(const key of ['cuisine','category'])assert(html.includes('id="'+key+'"'),'Filter ontbreekt: '+key);
assert(js.includes('function updateOptions()'),'Ingrediëntenfilter moet dynamisch uit de gegevens komen');
assert(js.includes('data.focus_counts'),'Dekking niet beperken tot twaalf handmatige producten');
assert(js.includes('r.title_original'),'Ook oorspronkelijke Engelstalige bronrecepten doorzoeken');
console.log('Alternatieven-UI, navigatie, bronstatus en prijslabels: OK');
