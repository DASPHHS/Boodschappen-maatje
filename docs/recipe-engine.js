/* Recepten uit promotieproducten: ideeën, nooit zonder volledige mand geprijsd. */
(function(root){
'use strict';
const T={
 kip:[
  {name:'Griekse citroenkip met courgette en paprika',cuisine:'Grieks',veg:['courgette','paprika'],extras:[['magere yoghurt',400,'g'],['citroen',1,'stuk'],['oregano',5,'g']],steps:['Snijd de kip in hapklare stukken en kruid met oregano en citroen.','Rooster de courgette en paprika met een kleine hoeveelheid olie tot ze zacht zijn.','Bak de kip volledig gaar en serveer met een frisse yoghurtsaus.']},
  {name:'Thaise groene kipcurry met broccoli en champignons',cuisine:'Thais',veg:['broccoli','champignons'],extras:[['lichte kokosmelk',400,'ml'],['groene currypasta',40,'g']],steps:['Snijd kip en groente en fruit de currypasta kort aan.','Bak de kip goed gaar, voeg broccoli en champignons toe en stoof in kokosmelk.','Laat indikken en serveer zonder rijst of met bloemkoolrijst als extra groente.']},
  {name:'Mexicaanse fajitakip met paprika en spitskool',cuisine:'Mexicaans',veg:['paprika','spitskool'],extras:[['komijn',5,'g'],['paprikapoeder',5,'g'],['magere kwark',300,'g']],steps:['Snijd de kip in reepjes en breng op smaak met komijn en paprika.','Roerbak de paprika en fijngesneden spitskool beetgaar.','Bak de kip geheel gaar en serveer met kruidige kwark.']},
  {name:'Surinaamse masalakip met sperziebonen en paksoi',cuisine:'Surinaams',veg:['sperziebonen','paksoi'],extras:[['masala',15,'g'],['tomatenpuree',70,'g']],steps:['Bak de kip met masala en tomatenpuree goed aan.','Voeg de sperziebonen met een scheutje water toe en stoof gaar.','Roer de paksoi er op het einde door en laat de kip volledig garen.']},
  {name:'Turkse kruidige kip met aubergine en tomaat',cuisine:'Turks',veg:['aubergine','tomaten'],extras:[['komijn',6,'g'],['magere yoghurt',400,'g']],steps:['Snijd aubergine en tomaat en meng met komijn.','Bak de kip goed gaar; rooster de groenten in de oven of in een brede pan.','Serveer de kip met de groenten en yoghurtsaus.']}
 ],
 vlees:[
  {name:'Koreaanse bulgogipan met broccoli en champignons',cuisine:'Koreaans',veg:['broccoli','champignons'],extras:[['sojasaus',45,'ml'],['gember',20,'g']],steps:['Snijd het rund- of varkensvlees dun en meng met soja en gember.','Roerbak broccoli en champignons tot ze gaar zijn.','Bak het vlees door en door volgens het soort vlees en meng met de groenten.']},
  {name:'Spaanse paprikapan met courgette en tomaat',cuisine:'Spaans',veg:['courgette','tomaten'],extras:[['gerookt paprikapoeder',8,'g'],['knoflook',10,'g']],steps:['Snijd het vlees in kleine reepjes of blokjes.','Fruit knoflook en paprikapoeder, bak het vlees goed gaar.','Voeg de groente toe en stoof kort tot een sappige pan.']},
  {name:'Mexicaanse vleesreepjes met spitskool en paprika',cuisine:'Mexicaans',veg:['spitskool','paprika'],extras:[['komijn',6,'g'],['tomatenpuree',70,'g']],steps:['Snijd het vlees in dunne reepjes en kruid met komijn.','Roerbak de spitskool en paprika en voeg tomatenpuree toe.','Bak het vlees op veilige gaarheid en meng alles.']},
  {name:'Japanse gemberroerbak met paksoi en champignons',cuisine:'Japans',veg:['paksoi','champignons'],extras:[['sojasaus',35,'ml'],['gember',25,'g']],steps:['Snijd vlees en groenten in dunne stukken.','Bak het vlees naar de juiste gaarheid en haal uit de pan.','Roerbak de groenten met gember en soja; meng het vlees erdoor.']},
  {name:'Marokkaanse ras-el-hanout-pan met wortel en bloemkool',cuisine:'Marokkaans',veg:['wortel','bloemkool'],extras:[['ras el hanout',12,'g'],['magere yoghurt',300,'g']],steps:['Kruid het vlees rijkelijk met ras el hanout.','Stoom wortel en bloemkool en bak daarna kort in een pan.','Bereid het vlees volledig gaar en serveer met een kruidige yoghurtsaus.']}
 ],
 vis:[
  {name:'Mediterrane citroenvis met courgette en tomaat',cuisine:'Mediterraans',veg:['courgette','tomaten'],extras:[['citroen',1,'stuk'],['oregano',5,'g']],steps:['Verdeel de vis in vier royale porties.','Rooster courgette en tomaat met oregano in de oven.','Voeg de vis toe en bak voorzichtig tot deze gaar is en gemakkelijk uit elkaar valt.']},
  {name:'Japanse misovis met broccoli en paksoi',cuisine:'Japans',veg:['broccoli','paksoi'],extras:[['miso',35,'g'],['gember',20,'g']],steps:['Roer miso met warm water en gember tot een saus.','Stoom broccoli en paksoi beetgaar.','Gaar de vis zacht in de misosaus en serveer met alle groenten.']},
  {name:'Indiase tandoorivis met bloemkool en spinazie',cuisine:'Indiaas',veg:['bloemkool','spinazie'],extras:[['tandoorikruiden',12,'g'],['magere yoghurt',350,'g']],steps:['Meng tandoorikruiden met yoghurt en bestrijk de vis.','Rooster de bloemkool en laat spinazie slinken.','Bak de vis in de oven tot hij gaar is en serveer met de groenten.']},
  {name:'Noordse dillevis met prei en sperziebonen',cuisine:'Noords',veg:['prei','sperziebonen'],extras:[['dille',10,'g'],['magere kwark',300,'g']],steps:['Snijd prei en kook sperziebonen gaar.','Gaar de vis zacht met prei in een afgedekte pan.','Roer dille door kwark en serveer koud naast de warme groenten.']},
  {name:'Thaise limoenvis met paprika en champignons',cuisine:'Thais',veg:['paprika','champignons'],extras:[['limoen',1,'stuk'],['lichte kokosmelk',350,'ml']],steps:['Roerbak paprika en champignons.','Voeg lichte kokosmelk en limoensap toe en laat inkoken.','Pocheer de vis hierin rustig tot volledig gaar.']}
 ],
 vega:[
  {name:'Indonesische sambaltofu met broccoli en sperziebonen',cuisine:'Indonesisch',veg:['broccoli','sperziebonen'],extras:[['sambal',25,'g'],['sojasaus',35,'ml'],['magere kwark',600,'g']],steps:['Dep tofu of tempeh droog en bak krokant.','Stoom broccoli en sperziebonen tot beetgaar.','Meng met sambal en sojasaus en serveer de kwark als frisse saus.']},
  {name:'Koreaanse tofu met spinazie en champignons',cuisine:'Koreaans',veg:['spinazie','champignons'],extras:[['sojasaus',35,'ml'],['gember',20,'g'],['magere kwark',600,'g']],steps:['Bak de plantaardige eiwitbron goudbruin met gember.','Roerbak champignons en voeg spinazie toe tot deze geslonken is.','Serveer met sojasaus en een frisse kwarkdip.']},
  {name:'Mexicaanse chipotletofu met paprika en witte kool',cuisine:'Mexicaans',veg:['paprika','witte kool'],extras:[['chipotlekruiden',10,'g'],['cottage cheese',600,'g']],steps:['Kruid en bak de eiwitbron met chipotle.','Bak de paprika met fijngesneden witte kool tot ze zacht is.','Serveer met cottage cheese naast de warme groentepan.']},
  {name:'Marokkaanse harissatempeh met courgette en wortel',cuisine:'Marokkaans',veg:['courgette','wortel'],extras:[['harissa',40,'g'],['magere kwark',600,'g']],steps:['Snijd en bak de plantaardige eiwitbron krokant met harissa.','Rooster courgette en wortel tot ze gaar zijn.','Serveer met de kwark om het geheel frisser en eiwitrijker te maken.']},
  {name:'Italiaanse oregano-tofu met aubergine en tomaat',cuisine:'Italiaans',veg:['aubergine','tomaten'],extras:[['oregano',7,'g'],['cottage cheese',600,'g']],steps:['Snijd aubergine en tomaat en rooster met oregano.','Bak de plantaardige eiwitbron goudbruin.','Schep de cottage cheese ernaast en verdeel in vier porties.']}
 ]
};
const omit=/\b(gerookt|salami|schnitzel|gepaneerd|burger|nugget|worst|spek|bacon|saus|soep|kroket|maaltijd|mix|salade|filet americain|kippenvleugel|drumstick|kippenbout)\b/i;
const valid={
kip:/\b(kip|kalkoen|kipfilet|kipdij|kiphaas|kipgehakt)/i,
vlees:/\b(runder|rund|varkens|varken|biefstuk|ossenhaas|rosbief|entrecote|varkenshaas)/i,
vis:/\b(zalm|forel|koolvis|kabeljauw|witvis|heek|schol|makreel|haring|sardine|pangasius|tonijn)/i,
vega:/\b(tofu|tempeh|seitan|edamame|sojabrok|soja\s?stukjes)/i
};
const display={kip:'Kip',vlees:'Vlees',vis:'Vis',vega:'Vega'};
const euro=new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'});
const qty=(n)=>Math.max(1,Math.round(n));
const slug=s=>String(s||'').toLocaleLowerCase('nl-NL').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'-').slice(0,90);
function eligible(o,k){
 if(!o||!valid[k].test(o.name||'')||omit.test(o.name||''))return false;
 if(o.category&&o.category!==k)return false;
 if(o.online_only||o.promotion_status==='historical'||o.promotion_status==='upcoming')return false;
 return true;
}
function ingredient(name,quantity,unit,department){return {name,quantity,unit,department}}
function selectDistinct(offers,k){
let seen=new Set(),rows=[];
for(const offer of offers){
 if(!eligible(offer,k))continue;
 const v=slug((offer.name||'').replace(/\d+([.,]\d+)?\s*(g|kg|stuks|ml)\b/gi,''));
 if(seen.has(v))continue;
 seen.add(v);rows.push(offer);
}
return rows.sort((a,b)=>{
 const one=x=>x?.verified?1:0;
 return one(b)-one(a)||(Number(b?.regular_price||0)>Number(b?.price)?1:0)-(Number(a?.regular_price||0)>Number(a?.price)?1:0);
}).slice(0,6);
}
function build(store,offers){
if(!Array.isArray(offers))return [];
const result=[];
for(const k of ['kip','vlees','vis','vega']){
 const majors=selectDistinct(offers,k),usedIds=new Set(),cap=12;
 let count=0;
 for(let index=0;index<majors.length&&count<cap;index++){
  const main=majors[index],rounds=majors.length===1?5:3;
  for(let j=0;j<rounds&&count<cap;j++){
   const t=T[k][(index*2+j)%T[k].length],id='idee-'+store+'-'+slug(main.id)+'-'+slug(t.name);
   if(usedIds.has(id))continue;usedIds.add(id);
   const protein=ingredient(main.name,800,'g',k==='vega'?'Vega & peulvruchten':'Eiwitbronnen');
   const veg=t.veg.map(v=>ingredient(v,600,'g','Groente & fruit'));
   const extras=t.extras.map(([name,q,u])=>ingredient(name,q,u,'Kruiden & voorraad'));
   result.push({id,title:t.name+' met '+main.name,category:k,cuisine:t.cuisine,
    servings:4,minutes:35,vegetables_g_per_portion:300,
    animal_protein_g_per_portion:k==='vega'?null:200,
    ingredients:[protein,...veg,...extras],instructions:t.steps,
    offer_anchor_id:main.id,offer_anchor_name:main.name,
    offer_source:main.source?.url,offer_price:main.price,offer_pack_label:main.pack_label,
    origin:'actie-idee',idea_status:'actiehoofdingredient_alleen',
    cost:null,macros:null,macro_status:'niet_berekend',
    source_note:'Ingrediënten/hoeveelheden zijn een culinaire suggestie. Enkel het hoofdproduct is in de aanbiedingsfeed gezien. De volledige kassaprijs, exacte hoeveelheid per verpakking en macro’s zijn niet geverifieerd.'});
   count++;
  }
 }
}
return result;
}
root.BoodschapRecipeEngine={build,eligible};
})(window);
