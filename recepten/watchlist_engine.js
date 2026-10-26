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
 {id:"AH-wi585919",protein100:10,portion:450,serving:200,source:"https://www.ah.nl/producten/product/wi585919/ah-protein-kwark-met-yoghurt-framboos"},
 {id:"AH-wi585929",protein100:12,portion:205,proteinPerPortion:25,source:"https://www.ah.nl/producten/product/wi585929/xxl-nutrition-fitquark-strawberry"},
 {id:"AH-wi555459",protein100:13,portion:200,source:"https://www.ah.nl/producten/product/wi555459/protein-kwark-met-yoghurt-perzik-passie"},
 {id:"AH-wi585917",protein100:10,portion:450,serving:200,source:"https://www.ah.nl/producten/product/wi585917/protein-kwark-met-yoghurt-vanillesmaak"},
 {id:"AH-wi585918",protein100:10,portion:450,serving:200,source:"https://www.ah.nl/producten/product/wi585918/protein-kwark-met-yoghurt-perzik"},
 {id:"AH-wi520225",protein100:12,portion:200,proteinPerPortion:25,source:"https://www.ah.nl/producten/product/wi520225/hipro-protein-kwark-banaan"},
 {id:"AH-wi597041",protein100:10,portion:450,serving:200,source:"https://www.ah.nl/producten/product/wi597041/lindahls-protein-kvarg-vanillesmaak"},
 {id:"Jumbo-590777CUP",protein100:10,portion:200,source:"https://www.jumbo.com/producten/melkunie-protein-aardbei-kwark-200-g-590777CUP"},
 {id:"Jumbo-735508ZK",protein100:10,portion:200,source:"https://www.jumbo.com/producten/melkunie-protein-yoghurt-perzik-framboos-735508ZK"},
 {id:"Jumbo-685838ZK",protein100:12,portion:205,proteinPerPortion:25,source:"https://www.jumbo.com/producten/zuivelhoeve-xxl-nutrition-fit-quark-strawberry-protein-quark-205-g-685838ZK"},
 {id:"Jumbo-685839ZK",protein100:12,portion:205,proteinPerPortion:25,source:"https://www.jumbo.com/producten/xxl-nutrition-fit-high-protein-kwark-perzik-passievrucht-205g-685839ZK"},
 {id:"Jumbo-735993EM",protein100:10,portion:750,serving:200,source:"https://www.jumbo.com/producten/xxl-nutrition-fit-yoghurt-aardbei-750g-735993EM"},
 {id:"Jumbo-735994EM",protein100:10,portion:750,serving:200,source:"https://www.jumbo.com/producten/xxl-nutrition-fit-yoghurt-mango-750g-735994EM"}
];
// Eenmalig op 26 oktober rechtstreeks bij AH gecontroleerde productprijzen.
 // Deze prijzen worden na 26 oktober NIET zonder nieuwe bevestiging gebruikt.
 // Een gemiste variant verschijnt op de dag van de controle alsnog, maar
 // is niet langer een grond om een 'actuele winnaar' te claimen na die dag.
const DIRECT_PRICES=[
 {id:"AH-wi555458",store:"ah",name:"AH Protein kwark met yoghurt framboos",price:0.95,quantity:200,unit:"g",url:"https://www.ah.nl/producten/product/wi555458/ah-protein-kwark-met-yoghurt-framboos"},
 {id:"AH-wi556289",store:"ah",name:"AH Protein kwark met yoghurt framboos",price:1.39,quantity:200,unit:"g",url:"https://www.ah.nl/producten/product/wi556289/ah-protein-kwark-met-yoghurt-framboos"},
 {id:"AH-wi585919",store:"ah",name:"AH Protein kwark met yoghurt framboos",price:1.99,quantity:450,unit:"g",url:"https://www.ah.nl/producten/product/wi585919/ah-protein-kwark-met-yoghurt-framboos"},
 {id:"AH-wi585929",store:"ah",name:"XXL Nutrition Fitquark strawberry",price:1.79,quantity:205,unit:"g",url:"https://www.ah.nl/producten/product/wi585929/xxl-nutrition-fitquark-strawberry"},
 {id:"AH-wi555459",store:"ah",name:"AH Protein kwark met yoghurt perzik passie",price:0.95,quantity:200,unit:"g",url:"https://www.ah.nl/producten/product/wi555459/protein-kwark-met-yoghurt-perzik-passie"},
 {id:"AH-wi585917",store:"ah",name:"AH Protein kwark met yoghurt vanillesmaak",price:1.99,quantity:450,unit:"g",url:"https://www.ah.nl/producten/product/wi585917/protein-kwark-met-yoghurt-vanillesmaak"},
 {id:"AH-wi585918",store:"ah",name:"AH Protein kwark met yoghurt perzik",price:1.99,quantity:450,unit:"g",url:"https://www.ah.nl/producten/product/wi585918/protein-kwark-met-yoghurt-perzik"},
 {id:"AH-wi520225",store:"ah",name:"HiPRO Protein kwark banaan",price:1.99,quantity:200,unit:"g",url:"https://www.ah.nl/producten/product/wi520225/hipro-protein-kwark-banaan"},
 {id:"AH-wi597041",store:"ah",name:"Lindahls Protein kvarg vanillesmaak",price:2.79,quantity:450,unit:"g",url:"https://www.ah.nl/producten/product/wi597041/lindahls-protein-kvarg-vanillesmaak"}
];
function directPriceFor(item,store,date=isoDate()){
 if(store!=="ah"||date!=="2026-10-26")return null;
 const skuId=sku(item.url);
 return DIRECT_PRICES.find(x=>x.store===store&&x.id===skuId&&x.quantity===exactQty(item.quantity))||null;
}
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
 if(!match||unit!=="g"||!Number.isFinite(Number(quantity))||quantity!==match.portion)return null;
 const n=norm(name);
 // Aanbiedingsbron en voedingsspecificatie moeten hetzelfde SKU én productsoort zijn.
 if(id?.startsWith("AH-")&&!/(protein|xxl|fit).*(kwark|quark|kvarg|yoghurt|yogurt)|(kwark|quark|kvarg|yoghurt|yogurt).*(protein|fit)/.test(n))return null;
 if(id?.startsWith("Jumbo-")&&!/(protein|xxl|fit).*(kwark|quark|yoghurt|yogurt)|(kwark|quark|yoghurt|yogurt).*(protein|fit)/.test(n))return null;
 return {proteinPer100g:match.protein100,proteinPerPackage:match.proteinPerPortion??round(match.protein100*quantity/100,1),
   proteinSource:match.source,serving:match.serving??match.portion,
  proteinPerServing:match.serving?round(match.protein100*match.serving/100,1):match.proteinPerPortion??round(match.protein100*match.portion/100,1)};
}
const WATCH=[
 {id:"knijp",name:"Knijpkwark ≥20 g eiwit per verpakking",unit:"g",type:"squeezequark",protein:true,
  note:"Alleen echte knijpkwarkzakjes met minimaal 20 g geverifieerd eiwit. Andere eiwitrijke knijpzuivel staat apart."},
 {id:"on_the_go",name:"Eiwitrijke knijpzuivel ≥20 g",unit:"g",type:"squeeze",protein:true,
  note:"Alternatief voor knijpkwark: een drink- of knijpverpakking met 20 g eiwit, expliciet herkend."},
 {id:"xxl",name:"XXL Nutrition / Zuivelhoeve Fit yoghurt",unit:"g",type:"xxl",protein:true,
  note:"200g-bekers bevatten 20g eiwit. De 750g-voordeelbak bevat 75g, oftewel 20g per zelf gekozen portie van 200g."},
 {id:"highprotein",name:"Eiwitrijke zuivel ≥20 g per portie",unit:"g",type:"protein",protein:true,
  note:"Alleen productvarianten waarvan voedingswaarden per SKU geverifieerd zijn."},
 {id:"vollemelk",name:"Volle koemelk",unit:"ml",type:"milk",protein:false,note:"Geen halfvolle, plantaardige of chocolademelk."},
 {id:"gingerbeer",name:"Gemberbier 0,0%",unit:"ml",type:"gingerbeer",protein:false,note:"Alleen expliciet alcoholvrij. Onbekend is niet hetzelfde als 0,0%."},
 {id:"skuum",name:"Texels Skuumkoppe (origineel)",unit:"ml",type:"skuum",protein:false,note:"Alcoholhoudend speciaalbier; 0.0 wordt afzonderlijk vergeleken."},
 {id:"skuum0",name:"Texels Skuumkoppe 0.0",unit:"ml",type:"skuum0",protein:false,note:"Alcoholvrije variant."}
];
function matchProduct(name,watch,url=''){
 const s=norm(name);
 const rejects=/\b(?:babyvoeding|baby|olvarit|knorr|maaltijd|poeder|soep|kruidenmix|smoothie)\b/;
 if(rejects.test(s))return false;
 switch(watch.type){
 case "squeezequark":return (/(knijpkwark|knijp kwark|quark pouch|kwark pouch|kwark zakje)/.test(s)||["Jumbo-685838ZK","Jumbo-685839ZK","AH-wi585929","AH-wi520225"].includes(sku(url)))&&!/(yoghurt|yogurt|drink)/.test(s);
 case "squeeze":return (/(knijp|breaker|pouch|zakje)/.test(s)||["Jumbo-735508ZK","Jumbo-685838ZK","Jumbo-685839ZK","AH-wi585929","AH-wi520225"].includes(sku(url)))&&/(protein|proteine|kwark|quark|yoghurt|yogurt)/.test(s);
 case "xxl":return /(xxl|zuivelhoeve)/.test(s)&&/(fit yog|fit yoghurt|fit yogurt|fityogurt)/.test(s);
 case "protein":return /(protein|proteine|hipro|high protein|fit yog|fit yoghurt|fit yogurt|skyr|kwark|quark)/.test(s)&&
   /(kwark|quark|kvarg|yoghurt|yogurt|skyr|protein pudding|proteine pudding)/.test(s)&&!/\b(drank|shake|poeder|snackreep)\b/.test(s);
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
function promoKind(type,quantity){
 const n=norm(type).replace(/\s+/g," ");
 if(/one plus one|one plus|1 1|1\+1/.test(String(type).toLowerCase())||n.includes("one plus one"))return "1+1 gratis";
 if(/(\d+)\s*voor/.test(n))return n.replace(/\bvoor\b/,"voor");
 if(/two for/.test(n))return "2 voor vaste prijs";
 if(/gratis/.test(n))return "Gratis product bij bundel";
 if(quantity>1)return quantity+" stuks voor één actieprijs";
 if(/percent|percentage|korting/.test(n))return "Korting";
 return "Aanbieding";
}
function sourceRows(src,watch,store="",today=isoDate()){
 const found=[];
 // Gebruik directe winkelcontrole alleen op de daadwerkelijke controledag.
 const direct=store==="ah"&&today==="2026-10-26"?DIRECT_PRICES.filter(x=>matchProduct(x.name,watch,x.url)):[];
 for(const raw of src.ordinary||[]){
  const [name,rawPrice,quantity,unit,url]=raw;
  if(!matchProduct(name,watch,url)||!Number(rawPrice)||!Number(quantity)||watch.unit!=="any"&&unit!==watch.unit)continue;
  const checked=directPriceFor({url,quantity},store,today);
  const price=checked?checked.price:Number(rawPrice);
  if(!volumeConsistent(name,quantity,unit,price,watch))continue;
  found.push({name,unit,quantity:exactQty(quantity),url,price:round(price),packages:1,
    source:checked?"Productpagina gecontroleerd 26 oktober":"Normale schapprijs",
    discount:false,verifiedDirect:!!checked,sku:sku(url)});
 }
 for(const item of direct){
  if(found.some(row=>row.sku===item.id))continue;
  found.push({name:item.name,unit:item.unit,quantity:item.quantity,url:item.url,price:item.price,
    packages:1,source:"Productpagina gecontroleerd 26 oktober",discount:false,
    verifiedDirect:true,sku:item.id});
 }
 for(const raw of src.promotions||[]){
  const [name,unitPrice,quantity,unit,previous,k,bundlePrice,type,until,url,loyalty,from]=raw;
  if(!matchProduct(name,watch,url)||!Number(unitPrice)||!Number(quantity)||watch.unit!=="any"&&unit!==watch.unit)continue;
  if(loyalty)continue;
  if(until&&String(until)<today||from&&String(from)>today)continue;
  const id=sku(url);
  const checked=directPriceFor({url,quantity},store,today);
  const regular=found.find(x=>x.sku&&x.sku===id&&x.quantity===exactQty(quantity)&&!x.discount);
  const baseline=checked?.price||regular?.price||Number(previous);
  const qty=Number(k),bundle=Number(bundlePrice);
  const goodBundle=Number.isInteger(qty)&&qty>=2&&qty<=12&&bundle>0&&
    Number.isFinite(baseline)&&baseline>0&&bundle<qty*baseline-0.005;
  const typeText=norm(type);
  const multi=/(gratis|one plus one|1 1|2 voor|3 voor|4 voor|bundel|multi)/.test(typeText);
  const goodUnit=!multi&&Number(unitPrice)>0&&Number.isFinite(baseline)&&
    baseline>Number(unitPrice)+0.005;
  if(!goodBundle&&!goodUnit)continue;
  const total=goodBundle?bundle:Number(unitPrice);
  const count=goodBundle?qty:1;
  if(!volumeConsistent(name,quantity,unit,total,watch))continue;
  const previousTotal=round(baseline*count);
  const savings=round(previousTotal-total);
  if(savings<=0)continue;
  found.push({name,unit,quantity:exactQty(quantity),url,
    price:round(total),packages:count,discount:true,
    sku:id,validUntil:until||null,validFrom:from||null,
    previousPrice:round(baseline),previousTotal,savings,
    discountPct:Math.round(savings/previousTotal*100),
    promoKind:goodBundle?promoKind(type,count):"Prijsverlaging",
    source:goodBundle?promoKind(type,count):"Prijsverlaging",
    verification:"Berekend op basis van bronprijzen en actievoorwaarden"});
 }
 // Dezelfde product-SKU mag niet tweemaal verschijnen door duplicaten in feeds.
 const seen=new Map();
 for(const row of found){
  const key=(row.sku||norm(row.name))+"|"+row.quantity+"|"+row.unit+"|"+
    row.packages+"|"+(row.discount?"actie":"normaal");
  const other=seen.get(key);
  if(!other||row.price<other.price)seen.set(key,row);
 }
 return [...seen.values()];
}

function normalizeRow(row,watch){
 const amount=exactQty(row.quantity);
 const bundles=row.packages;
 const totalContent=amount*bundles;
 const calcUnit=watch.unit==="any"?row.unit:watch.unit;
 const unitScale=calcUnit==="g"?100:calcUnit==="ml"?1000:1;
 const nutrient=watch.protein?nutrition(row.name,amount,row.unit,row.url):null;
 if(watch.protein&&(!nutrient||nutrient.proteinPer100g*nutrient.serving/100<19.99))return null;
 const eurosPer20=nutrient?round(row.price*20/(nutrient.proteinPerPackage*bundles),3):null;
 return {...row,unit:calcUnit,quantity:amount,
  pricePerUnit:round(row.price*unitScale/totalContent,3),
  unitLabel:calcUnit==="g"?"per 100 g":calcUnit==="ml"?"per liter":"per stuk",
  protein: nutrient?.proteinPerPackage??null,
  proteinServing: nutrient?.serving??null,
  proteinPerServing: nutrient?.proteinPerServing??null,
  proteinSource:nutrient?.proteinSource??null,
  eurosPer20,cartCost:row.price};
}
function compare(rows,watch){
 return rows.map(row=>normalizeRow(row,watch)).filter(Boolean)
  .sort((a,b)=>watch.protein?a.eurosPer20-b.eurosPer20||
   a.cartCost-b.cartCost :a.pricePerUnit-b.pricePerUnit||
   a.cartCost-b.cartCost);
}
function unverifiedRows(snapshot,store,watch,asOf=isoDate()){
 if(!watch.protein)return [];
 const data=snapshot?.stores?.[store];
 if(!data)return [];
 return sourceRows(data,watch,store,asOf)
  .filter(row=>nutrition(row.name,row.quantity,row.unit,row.url)===null)
  .map(row=>({...normalizeRow(row,{...watch,protein:false}),
    protein:null,verificationStatus:"Eiwitinhoud per productvariant nog niet bevestigd"}))
  .sort((a,b)=>a.pricePerUnit-b.pricePerUnit||a.price-b.price)
  .slice(0,8);
}
function bestRows(snapshot,store,watch,asOf=isoDate()){
 const data=snapshot?.stores?.[store];
 if(!data)return [];
 return compare(sourceRows(data,watch,store,asOf),watch);
}
function bestStores(snapshot,watch,asOf=isoDate()){
 const stores={};
 for(const store of ["ah","jumbo","lidl"]){
  const options=bestRows(snapshot,store,watch,asOf);
  const best=options[0]||null;
  const sameSkuRegular=best&&best.discount?options.find(x=>!x.discount&&
    x.sku&&x.sku===best.sku&&x.quantity===best.quantity):null;
  stores[store]={best,regular:sameSkuRegular||null,
   alternatives:options.slice(0,8),total:options.length,
   unverified:unverifiedRows(snapshot,store,watch,asOf)};
 }
 const candidates=Object.entries(stores).filter(([,v])=>Boolean(v.best))
  .map(([store,v])=>({store,...v.best}));
 candidates.sort((a,b)=>watch.protein?a.eurosPer20-b.eurosPer20||
   a.cartCost-b.cartCost :a.pricePerUnit-b.pricePerUnit||
   a.cartCost-b.cartCost);
 return {stores,winner:candidates[0]||null};
}
const API={WATCH,VERIFIED,DIRECT_PRICES,norm,money,sku,nutrition,matchProduct,volumeConsistent,
 sourceRows,promoKind,normalizeRow,compare,unverifiedRows,bestRows,bestStores,isoDate};
root.BMWatchlist=API;
if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof globalThis!=="undefined"?globalThis:this);
