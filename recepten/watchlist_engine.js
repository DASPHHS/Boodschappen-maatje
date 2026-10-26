/* Prijswatchlist v2: concrete SKU-verificatie, volledige bundelafrekening,
 * geen merkbrede eiwitclaims, geen veronderstelde verpakkingsaantallen.
 * Browsermodule en Node.js-regressietests gebruiken exact dezelfde berekening.
 */
(function(root){
"use strict";
const norm=x=>String(x||"").toLocaleLowerCase("nl").normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim();
const round=(n,d=2)=>Math.round((Number(n)+Number.EPSILON)*10**d)/10**d;
const exactQty=n=>round(Number(n),2);
const money=n=>"€ "+Number(n).toLocaleString("nl-NL",{minimumFractionDigits:2,maximumFractionDigits:2});
const dateNL=()=>new Intl.DateTimeFormat("en-CA",{year:"numeric",month:"2-digit",day:"2-digit",timeZone:"Europe/Amsterdam"}).format(new Date()).split("/").join("-");
const isoDate=()=>new Date().toLocaleDateString("sv-SE",{timeZone:"Europe/Amsterdam"});
const VERIFIED=[
 {id:"AH-wi583038",protein100:10,portion:200,source:"https://www.ah.nl/producten/product/wi583038/xxl-nutrition-fit-yoghurt-protein-strawberry"},
 {id:"Jumbo-660840CUP",protein100:10,portion:200,source:"https://www.jumbo.com/producten/xxl-nutrition-fit-yoghurt-granola-aardbei-200g-660840CUP"},
 {id:"Jumbo-660843CUP",protein100:10,portion:200,source:"https://www.jumbo.com/producten/xxl-nutrition-fit-yoghurt-granola-vanille-200g-660843CUP"},
 {id:"AH-wi555458",protein100:13,portion:200,source:"https://www.ah.nl/producten/product/wi555458/ah-protein-kwark-met-yoghurt-framboos"},
 {id:"AH-wi556289",protein100:13,portion:200,source:"https://www.ah.nl/producten/product/wi556289/ah-protein-kwark-met-yoghurt-framboos"},
 {id:"Jumbo-590777CUP",protein100:10,portion:200,source:"https://www.jumbo.com/producten/melkunie-protein-aardbei-kwark-200-g-590777CUP"},
 {id:"Jumbo-735508ZK",protein100:10,portion:200,source:"https://www.jumbo.com/producten/melkunie-protein-yoghurt-perzik-framboos-735508ZK"}
];
// Houd de identiteit van het artikel aan, niet alleen 'protein' in een naam.
// Bronvoedingswaarde geldt per artikel; een 450g familiebak of andere smaak
// krijgt geen automatisch 20g-label.
function sku(url){
 const u=String(url||"");
 const ah=u.match(/\/(wi\d{4,9})\b/i);
 if(ah&&u.includes("ah.nl/"))return "AH-"+ah[1].toLowerCase();
 const jumbo=u.match(/-(\d{5,9}[a-z]{2,5})(?:[/?#]|$)/i);
 if(jumbo&&u.includes("jumbo.com/"))return "Jumbo-"+jumbo[1].toUpperCase();
 return null;
}
function nutrition(name,quantity,unit,url){
 const id=sku(url);
 const match=VERIFIED.find(v=>v.id.toLowerCase()===String(id||"").toLowerCase());
 if(!match||unit!=="g"||!Number.isFinite(Number(quantity))||quantity<=0)return null;
 const n=norm(name);
 // Aanbiedingsbron en voedingsspecificatie moeten hetzelfde SKU én productsoort zijn.
 if(id?.startsWith("AH-")&&!/(protein|xxl|fit).*(kwark|yoghurt)|(kwark|yoghurt).*(protein|fit)/.test(n))return null;
 if(id?.startsWith("Jumbo-")&&!/(protein|xxl|fit).*(kwark|yoghurt|yogurt)|(kwark|yoghurt|yogurt).*(protein|fit)/.test(n))return null;
 return {proteinPer100g:match.protein100,proteinPerPackage:round(match.protein100*quantity/100,1),
   proteinSource:match.source,serving:match.portion};
}
const WATCH=[
 {id:"knijp",name:"Knijpkwark ≥20 g eiwit per verpakking",unit:"g",type:"squeezequark",protein:true,
  note:"Alleen echte knijpkwarkzakjes met minimaal 20 g geverifieerd eiwit. Andere eiwitrijke knijpzuivel staat apart."},
 {id:"on_the_go",name:"Eiwitrijke knijpzuivel ≥20 g",unit:"g",type:"squeeze",protein:true,
  note:"Alternatief voor knijpkwark: een drink- of knijpverpakking met 20 g eiwit, expliciet herkend."},
 {id:"xxl",name:"XXL Nutrition / Zuivelhoeve Fit yoghurt",unit:"g",type:"xxl",protein:true,
  note:"De exacte 200g-verpakking bevat 20 g eiwit; een 750g-bak telt pas na bronverificatie mee."},
 {id:"highprotein",name:"Eiwitrijke zuivel ≥20 g per portie",unit:"g",type:"protein",protein:true,
  note:"Alleen productvarianten waarvan voedingswaarden per SKU geverifieerd zijn."},
 {id:"vollemelk",name:"Volle koemelk",unit:"ml",type:"milk",protein:false,note:"Geen halfvolle, plantaardige of chocolademelk."},
 {id:"gingerbeer",name:"Gemberbier 0,0%",unit:"ml",type:"gingerbeer",protein:false,note:"Alleen expliciet alcoholvrij. Onbekend is niet hetzelfde als 0,0%."},
 {id:"skuum",name:"Texels Skuumkoppe (origineel)",unit:"ml",type:"skuum",protein:false,note:"Alcoholhoudend speciaalbier; 0.0 wordt afzonderlijk vergeleken."},
 {id:"skuum0",name:"Texels Skuumkoppe 0.0",unit:"ml",type:"skuum0",protein:false,note:"Alcoholvrije variant."}
];
function matchProduct(name,watch){
 const s=norm(name);
 const rejects=/\b(?:babyvoeding|baby|olvarit|knorr|maaltijd|poeder|soep|kruidenmix|smoothie)\b/;
 if(rejects.test(s))return false;
 switch(watch.type){
 case "squeezequark":return /(knijpkwark|knijp kwark|quark pouch|kwark pouch|kwark zakje)/.test(s)&&!/(yoghurt|yogurt|drink)/.test(s);
 case "squeeze":return /(knijp|breaker|pouch|zakje)/.test(s)&&/(protein|proteine|kwark|quark|yoghurt|yogurt)/.test(s);
 case "xxl":return /(xxl|zuivelhoeve)/.test(s)&&/(fit yog|fit yoghurt|fit yogurt|fityogurt)/.test(s);
 case "protein":return /(protein|proteine|hipro|high protein|fit yog|fit yoghurt|fit yogurt|skyr|kwark|quark)/.test(s)&&
   /(kwark|quark|yoghurt|yogurt|skyr|protein pudding|proteine pudding)/.test(s)&&!/\b(drank|shake|poeder|snackreep)\b/.test(s);
 case "milk":return /\b(volle melk|vollemelk|volle houdbare melk)\b/.test(s)&&
   !/\b(halfvol|magere|karnemelk|chocolade|geit|lactosevrij|kokos|soja|amandel|haver|plantaardig|melkpoeder|melkdrank)\b/.test(s);
 case "gingerbeer":return /(ginger beer|gingerbeer|gemberbier)/.test(s)&&
   /\b(alcoholvrij|0 0|zero|non alcoholic)\b/.test(s);
 case "skuum":return /skuumkoppe/.test(s)&&!/\b(alcoholvrij|0 0|zero)\b/.test(s);
 case "skuum0":return /skuumkoppe/.test(s)&&/\b(alcoholvrij|0 0|zero)\b/.test(s);
 case "custom":{
   const words=norm(watch.name).split(" ").filter(w=>w.length>1);
   return words.length>0&&words.every(w=>s.split(" ").includes(w));
 }
 default:return false;
 }
}
function volumeConsistent(name,quantity,unit,cost,watch){
 const q=exactQty(quantity);
 if(!Number.isFinite(q)||q<=0||!Number.isFinite(cost)||cost<=0)return false;
 if(!watch.type.startsWith("skuum"))return true;
 const n=norm(name);
 const px=n.match(/\b(\d{1,2})\s*x\s*(\d{2,4})\s*(?:ml|cl)\b/);
 if(px){
   const ml=Number(px[2])*(n.includes(" cl")?10:1)*Number(px[1]);
   if(Math.abs(ml-q)>1)return false;
 }
 const packs=n.match(/\b(\d{1,2})\s*(?:pack|pak|flessen|blikjes)\b/);
 if(packs&&Number(packs[1])>=2&&q<=350)return false;
 // Verborgen 4-packs uit een foutieve Lidl-productimport mogen niet als
 // €5,49 per blik van 330 ml worden verkocht; verifiëren of uitsluiten.
 if(unit!=="ml"||q<500&&cost>3.49&&!packs)return false;
 return true;
}
function sourceRows(src,watch){
 const found=[];
 for(const raw of src.ordinary||[]){
  const [name,price,quantity,unit,url]=raw;
  if(!matchProduct(name,watch)||!Number(price)||!Number(quantity)||watch.unit!=="any"&&unit!==watch.unit)continue;
  if(!volumeConsistent(name,quantity,unit,Number(price),watch))continue;
  found.push({name,unit,quantity:exactQty(quantity),url,price:round(price),packages:1,
    source:"Reguliere prijs",discount:false});
 }
 for(const raw of src.promotions||[]){
  const [name,unitPrice,quantity,unit,previous,k,bundlePrice,type,until,url,loyalty,from]=raw;
  if(!matchProduct(name,watch)||!Number(unitPrice)||!Number(quantity)||watch.unit!=="any"&&unit!==watch.unit)continue;
  if(loyalty)continue;
  const now=isoDate();
  if(until&&String(until)<now||from&&String(from)>now)continue;
  const one=Number(previous),qty=Number(k),bundle=Number(bundlePrice);
  const goodBundle=Number.isInteger(qty)&&qty>=2&&qty<=12&&
   bundle>0&&one>0&&bundle<qty*one&&
   Number.isFinite(bundle);
  const typeText=norm(type);
  const multi=/(gratis|1 1|2 voor|3 voor|4 voor|bundel|multi)/.test(typeText);
  const single=one>Number(unitPrice)&&!multi&&
    Number(unitPrice)>=0.1*one;
  if(!goodBundle&&!single)continue;
  const total=goodBundle?bundle:Number(unitPrice);
  if(!volumeConsistent(name,quantity,unit,total,watch))continue;
  found.push({name,unit,quantity:exactQty(quantity),url,price:round(total),
   packages:goodBundle?qty:1,discount:true,
   source:goodBundle?(type||"Bundelactie")+" (minimaal "+qty+" verpakkingen)":type||"Actie",
   until:until||null});
 }
 return found;
}
function normalizeRow(row,watch){
 const amount=exactQty(row.quantity);
 const bundles=row.packages;
 const totalContent=amount*bundles;
 const calcUnit=watch.unit==="any"?row.unit:watch.unit;
 const unitScale=calcUnit==="g"?100:calcUnit==="ml"?1000:1;
 const nutrient=watch.protein?nutrition(row.name,amount,row.unit,row.url):null;
 if(watch.protein&&(!nutrient||nutrient.proteinPerPackage<20))return null;
 const eurosPer20=nutrient?round(row.price*20/(nutrient.proteinPerPackage*bundles),3):null;
 return {...row,unit:calcUnit,quantity:amount,
  pricePerUnit:round(row.price*unitScale/totalContent,3),
  unitLabel:calcUnit==="g"?"per 100 g":calcUnit==="ml"?"per liter":"per stuk",
  protein: nutrient?.proteinPerPackage??null,
  proteinSource:nutrient?.proteinSource??null,
  eurosPer20,cartCost:row.price};
}
function compare(rows,watch){
 return rows.map(row=>normalizeRow(row,watch)).filter(Boolean)
  .sort((a,b)=>watch.protein?a.eurosPer20-b.eurosPer20||
   a.cartCost-b.cartCost :a.pricePerUnit-b.pricePerUnit||
   a.cartCost-b.cartCost);
}
function bestRows(snapshot,store,watch){
 const data=snapshot?.stores?.[store];
 if(!data)return [];
 return compare(sourceRows(data,watch),watch);
}
function bestStores(snapshot,watch){
 const stores={};
 for(const store of ["ah","jumbo","lidl"]){
  const options=bestRows(snapshot,store,watch);
  stores[store]={best:options[0]||null,regular:options.find(x=>x.packages===1)||null,
                 alternatives:options.slice(0,3)};
 }
 const candidates=Object.entries(stores).filter(([,v])=>Boolean(v.best))
  .map(([store,v])=>({store,...v.best}));
 candidates.sort((a,b)=>watch.protein?a.eurosPer20-b.eurosPer20||
   a.cartCost-b.cartCost :a.pricePerUnit-b.pricePerUnit||
   a.cartCost-b.cartCost);
 return {stores,winner:candidates[0]||null};
}
const API={WATCH,VERIFIED,norm,money,sku,nutrition,matchProduct,volumeConsistent,
 sourceRows,normalizeRow,compare,bestRows,bestStores,isoDate};
root.BMWatchlist=API;
if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof globalThis!=="undefined"?globalThis:this);
