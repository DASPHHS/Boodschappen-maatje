/* Persoonlijk weekmenu: pure regels, ook in Node testbaar. */
(function(root){
"use strict";
const DAYS=["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"];
const STORES=["ah","jumbo","lidl"];
function empty(){return {ah:{},jumbo:{},lidl:{}}}
function parse(value){
 const result=empty();let data={};
 try{data=typeof value==="string"?JSON.parse(value):value||{}}catch{return result}
 for(const store of STORES)for(const [day,x] of Object.entries(data?.[store]||{})){
  if(!/^[0-6]$/.test(day)||!x||!(typeof x.id==="string"||typeof x.id==="number"))continue;
  const portions=Number(x.portions);
  if(!Number.isInteger(portions)||portions<1||portions>8)continue;
  result[store][day]={id:x.id,portions,title:String(x.title||"").slice(0,180)};
 }
 return result;
}
function set(plan,store,day,recipe,portions){
 if(!STORES.includes(store)||!DAYS[Number(day)]||!recipe)return plan;
 const n=Number(portions);if(!Number.isInteger(n)||n<1||n>8)return plan;
 const next=parse(plan);
 next[store][String(day)]={id:recipe.id,title:String(recipe.title||""),portions:n};
 return next;
}
function remove(plan,store,day){
 const next=parse(plan);if(STORES.includes(store))delete next[store][String(day)];
 return next;
}
function portions(plan,store,id){
 return Object.values(plan?.[store]||{}).filter(x=>String(x.id)===String(id))
  .reduce((sum,x)=>sum+x.portions,0);
}
function dishType(recipe){
 const title=String(recipe.title||"").toLocaleLowerCase("nl");
 for(const [type,pattern] of [
 ["stamppot",/stamppot|hutspot|stoemp/],["curry",/curry|dahl|dal\b|masala/],
 ["pasta",/pasta|spaghetti|penne|lasagne|orzo|macaroni|risotto/],
 ["wok",/wok|roerbak|bami|nasi/],["soep",/soep|ramen|saoto/],
 ["oven",/oven|traybake|gratin/],["wrap",/wrap|taco|burrito|quesadilla/],
 ["salade",/salade|bowl/]])if(pattern.test(title))return type;
 return "overig";
}
/* Diversifieer uitsluitend binnen hetzelfde betrouwbaarheidsniveau:
   volledige gezonde recepten blijven altijd boven onvolledige records. */
function diversify(sorted){
 const buckets=[[],[],[],[]];
 for(const r of sorted){
  const bucket=r.complete?(r.nutrition?.priority?0:1):2;
  buckets[bucket].push(r);
 }
 const output=[];
 for(const bucket of buckets){
  const pool=bucket.slice(),usedCategory={},usedCuisine={},usedType={};
  while(pool.length){
   let best=0,bestScore=Infinity;
   for(let i=0;i<Math.min(pool.length,24);i++){
    const r=pool[i],c=r.category||"Overig",k=r.cuisine||"Onbekend",t=dishType(r);
    const score=i*0.65+(usedCategory[c]||0)*5+(usedCuisine[k]||0)*1.7+
     (usedType[t]||0)*3.5-(r.complete&&Number(r.saving)>0?1.5:0);
    if(score<bestScore){best=i;bestScore=score}
   }
   const [r]=pool.splice(best,1);
   output.push(r);
   const c=r.category||"Overig",k=r.cuisine||"Onbekend",t=dishType(r);
   usedCategory[c]=(usedCategory[c]||0)+1;usedCuisine[k]=(usedCuisine[k]||0)+1;usedType[t]=(usedType[t]||0)+1;
  }
 }
 return output;
}
root.PersonalWeekmenu={DAYS,empty,parse,set,remove,portions,dishType,diversify};
if(typeof module!=="undefined"&&module.exports)module.exports=root.PersonalWeekmenu;
})(typeof globalThis!=="undefined"?globalThis:this);
