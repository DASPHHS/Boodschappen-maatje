/* Watchlist UI: kassabedrag, actie-eenheden en eiwitwaarde afzonderlijk. */
(function(){
"use strict";
const W=globalThis.BMWatchlist;
const $=id=>document.getElementById(id);
if(!W){$("freshness").textContent="De prijsberekening ontbreekt.";return;}
const names={ah:"Albert Heijn",jumbo:"Jumbo",lidl:"Lidl"};
const KEY="bm_favoriete_producten_v1",CUSTOM="bm_eigen_watchlist_v1";
const esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function safeLink(url){try{const u=new URL(String(url));return u.protocol==="https:"?u.href:"#"}catch{return "#"}}
function read(key,fallback){try{const x=JSON.parse(localStorage.getItem(key)||"null");return Array.isArray(x)?x:fallback}catch{return fallback}}
function save(){
 try{
  localStorage.setItem(KEY,JSON.stringify(followed));
  localStorage.setItem(CUSTOM,JSON.stringify(custom));
  $("save-status").textContent="Favorieten zijn op dit apparaat opgeslagen.";
 }catch{$("save-status").textContent="Browser blokkeert het bewaren van favorieten.";}
}
let followed=read(KEY,["knijp","on_the_go","xxl","highprotein","vollemelk","gingerbeer","skuum","skuum0"]);
let custom=read(CUSTOM,[]).filter(x=>x&&typeof x.name==="string"&&typeof x.id==="string"&&["g","ml"].includes(x.unit)).slice(0,30);
let snapshot=null,stale=true,onlyFollowed=false;
function catalog(){
 return W.WATCH.concat(custom.map(x=>({id:x.id,name:x.name,unit:x.unit,
  type:"custom",protein:false,note:"Handmatig toegevoegd. Producttype en prijseenheid zelf controleren."})));
}
function dateNL(text){
 if(!text)return "";
 const date=new Date(String(text)+"T12:00:00");
 return Number.isFinite(date.getTime())?date.toLocaleDateString("nl-NL",{
  weekday:"long",day:"numeric",month:"long",timeZone:"Europe/Amsterdam"
 }):String(text);
}
function htmlItem(item,unverified=false){
 const quantity=Math.round(item.quantity*100)/100;
 const volume=item.packages+" × "+quantity+" "+item.unit;
 const total=W.money(item.price);
 const offer=item.discount;
 let result="<div class='product'>"+(unverified?"<div class='unverified-label'>Eiwit per portie nog niet gecontroleerd · telt niet mee in winnaar</div>":"");
 result+="<div class='deal-status "+(offer?"deal-active":"deal-regular")+"'>"+
  (offer?"<strong>"+esc(item.promoKind||"AANBIEDING").toUpperCase()+"</strong>"+
   " · <strong>−"+item.discountPct+"%</strong>"+
   (item.validUntil?" · geldig t/m "+esc(dateNL(item.validUntil)):""):
   "<strong>NORMALE PRIJS</strong> · geen bevestigde actie")+"</div>";
 result+="<a class='product-title' target='_blank' rel='noopener noreferrer' href='"+
  esc(safeLink(item.url))+"'>"+esc(item.name)+"</a>";
 result+="<div class='row-top'><strong class='price'>"+total+"</strong>"+
  "<span>"+W.money(item.pricePerUnit)+" "+esc(item.unitLabel)+"</span></div>";
 result+="<div class='small'><strong>Te betalen: "+total+"</strong> voor "+
    volume+"</div>";
 if(offer){
  result+="<div class='deal-savings'>Normaal "+
   "<s>"+W.money(item.previousTotal)+"</s> · <strong>Je bespaart "+W.money(item.savings)+
   "</strong> bij aankoop van "+item.packages+" verpakking"+
   (item.packages===1?"":"en")+".</div>";
 }else{
  result+="<div class='small'>"+esc(item.source||"Schapprijs")+"</div>";
 }
 if(item.sku)result+="<div class='sku'>Productnummer: "+esc(item.sku)+"</div>";
 if(item.protein!==null)result+="<div class='protein'>"+
  item.protein+" g eiwit per verpakking, "+item.proteinPerServing+
  " g per "+item.proteinServing+" g portie. <strong>"+W.money(item.eurosPer20)+
  " per 20 g eiwit</strong> · <a target='_blank' rel='noopener noreferrer' href='"+
  esc(safeLink(item.proteinSource))+"'>Productinformatie</a></div>";
 return result+"</div>";
}
function htmlWatch(p){
 const isFollowed=followed.includes(p.id);
 const result=W.bestStores(snapshot,p);
 const winner=result.winner;
 let out="<article class='watch "+(isFollowed?"favorite":"")+"'><div class='watch-top'><h3>"+
  esc(p.name)+"</h3><button data-follow='"+esc(p.id)+"' type='button' aria-pressed='"+
  isFollowed+"'>"+(isFollowed?"★ Volgend":"☆ Volgen")+"</button></div>"+
  "<p class='note'>"+esc(p.note||"")+"</p>";
 if(winner&&!stale){
  out+="<div class='winner'><span class='pill'>"+(winner.discount?"VOORDEEL DOOR ACTIE":"GOEDKOOPSTE NORMALE PRIJS")+"</span>"+
   "<strong>"+names[winner.store]+" · "+W.money(p.protein?winner.eurosPer20:winner.pricePerUnit)+
   " "+(p.protein?"per 20 g eiwit":p.unit==="ml"?"per liter":"per 100 g")+
   "</strong><div class='small'>Minimaal kassabedrag: "+W.money(winner.price)+
   (winner.packages>1?" voor "+winner.packages+" verpakkingen":"")+"</div>"+(winner.discount?"<div class='small'><strong>"+esc(winner.promoKind)+" · Je bespaart "+W.money(winner.savings)+" · "+winner.discountPct+"% korting</strong></div>":"")+"</div>";
 }else{
  out+="<div class='warning'>"+(stale?"De prijzen zijn verouderd. Daarom geen actuele winnaar.":
   "Geen betrouwbaar geprijsd product met de vereiste kenmerken gevonden.")+"</div>";
 }
 for(const store of ["ah","jumbo","lidl"]){
  const entry=result.stores[store];
  out+="<section class='store'><h4>"+names[store]+"</h4>";
  if(entry.best){
   out+=htmlItem(entry.best);
   if(entry.best.discount&&entry.regular){
    out+="<div class='regular'><strong>Deze zelfde verpakking zonder actie:</strong> "+
     W.money(entry.regular.price)+" per "+entry.regular.quantity+
     " "+entry.regular.unit+".</div>";
   }
   const more=entry.alternatives.filter(x=>x!==entry.best&&
     !(entry.best.discount&&entry.regular&&x===entry.regular));
   if(more.length){
    out+="<details class='alternatives'><summary>Vergelijk "+more.length+
      " andere productvariant"+(more.length===1?"":"en")+
      " of aanbiedingen bij "+names[store]+"</summary>"+
      more.map(htmlItem).join("")+"</details>";
   }
   if(p.protein&&entry.unverified?.length){
    out+="<details class='unverified-products'><summary>"+
      entry.unverified.length+" extra eiwitproducten · voedingswaarde nog niet bevestigd"+
      "</summary><div class='note'>Deze producten zijn wel in de prijslijst gevonden, maar voldoen nog niet aantoonbaar aan minimaal 20 g eiwit per portie.</div>"+
      entry.unverified.map(x=>htmlItem(x,true)).join("")+"</details>";
   }
  }else {
   out+="<p class='notfound'>Geen betrouwbare eiwitmatch in deze prijsimport. Dit bewijst niet dat het product niet verkrijgbaar is.</p>";
   if(p.protein&&entry.unverified?.length){
    out+="<details class='unverified-products'><summary>"+entry.unverified.length+
      " gevonden alternatieven zonder gecontroleerde voedingswaarde</summary>"+
      entry.unverified.map(x=>htmlItem(x,true)).join("")+"</details>";
   }
  }
  out+="</section>";
 }
 if(p.id.startsWith("custom_"))out+="<button class='delete' type='button' data-remove='"+
   esc(p.id)+"'>Verwijder eigen product</button>";
 return out+"</article>";
}
function render(){
 const all=catalog();
 const shown=all.filter(x=>!onlyFollowed||followed.includes(x.id));
 $("watch-grid").innerHTML=shown.length?shown.map(htmlWatch).join(""):
  "<p>Geen gevolgde producten. Kies ‘Toon alle producten’ om iets te volgen.</p>";
 $("favorites-list").textContent=all.filter(x=>followed.includes(x.id)).map(x=>x.name).join(" · ")||
  "Je volgt momenteel geen producten.";
 $("toggle-followed").textContent=onlyFollowed?"Toon alle producten":"Alleen mijn favorieten";
 $("toggle-followed").setAttribute("aria-pressed",String(onlyFollowed));
}
$("toggle-followed").addEventListener("click",()=>{onlyFollowed=!onlyFollowed;render()});
$("watch-grid").addEventListener("click",event=>{
 const btn=event.target.closest("button");if(!btn)return;
 if(btn.dataset.follow){
  const id=btn.dataset.follow;
  followed=followed.includes(id)?followed.filter(x=>x!==id):followed.concat(id);
  save();render();
 }
 if(btn.dataset.remove){
  const id=btn.dataset.remove;
  custom=custom.filter(x=>x.id!==id);
  followed=followed.filter(x=>x!==id);
  save();render();
 }
});
$("add").addEventListener("click",()=>{
 const name=$("custom").value.trim(),unit=$("custom-unit").value;
 if(name.length<3||name.length>100||!["g","ml"].includes(unit))return;
 const id="custom_"+W.norm(name).replace(/\s+/g,"_").slice(0,70)+"_"+unit;
 if(!custom.some(x=>x.id===id)&&custom.length<30)custom.push({id,name,unit});
 if(!followed.includes(id))followed.push(id);
 $("custom").value="";save();render();
});
async function load(){
 try{
  const response=await fetch("./winkelprijzen.json",{cache:"no-store"});
  if(!response.ok)throw Error("HTTP "+response.status);
  const data=await response.json();
  if(!data?.stores)throw Error("Onjuiste gegevensindeling");
  snapshot=data;
  const time=Date.parse(data.updated_at||""),age=(Date.now()-time)/3600000;
  stale=!Number.isFinite(time)||age>36||age< -1;
  $("freshness").textContent="Laatste prijsimport: "+(Number.isFinite(time)?
   new Date(time).toLocaleString("nl-NL",{timeZone:"Europe/Amsterdam"}):"onbekend")+
   (stale?" · Verouderd: geen actuele winnaar.":" · Geldigheid acties afzonderlijk gecontroleerd.")+
   " · Geen winkelvoorraadgarantie.";
 }catch(e){
  snapshot=null;stale=true;
  $("freshness").textContent="Prijsbestand niet beschikbaar: "+e.message+". Geen prijzen geschat.";
 }
 render();
}
render();load();
})();