const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('recepten/index.html','utf8');
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/gi)];
assert(scripts.length>0,'Inline JavaScript aanwezig');
for(const item of scripts)new vm.Script(item[1]);
const primary=html.slice(html.indexOf('<div class="primary-filters">'),
 html.indexOf('<details id="advanced-filters"'));
const advanced=html.slice(html.indexOf('<details id="advanced-filters"'),
 html.indexOf('<p class="discovery-note"'));
for(const id of ['sort','cuisine','category','health'])
 assert(primary.includes('id="'+id+'"'),'Hoofdfilter ontbreekt: '+id);
for(const id of ['selection','mealtype','duration','format','origin','mealprep-filter'])
 assert(advanced.includes('id="'+id+'"'),'Extra filter ontbreekt: '+id);
for(const option of ['chicken','redmeat','fish','vega','tofu'])
 assert(primary.includes('value="'+option+'"'),'Eiwitkeuze ontbreekt: '+option);
assert(html.includes('if(cat==="tofu")rs=rs.filter'), 'Tofu-filter moet op ingrediënten werken');
assert(html.includes('category:cat==="tofu"?"vega":cat'), 'HelloFresh vegetarisch filter behouden');
const ids=['sort','cuisine','category','health','selection','mealtype','duration','format','origin','mealprep-filter'];
for(const id of ids)assert.equal((html.match(new RegExp('id="'+id+'"','g'))||[]).length,1,'Dubbele filter: '+id);
console.log('Compacte mobiele receptenfilters getest');
