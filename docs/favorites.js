/* Exact product favorites. Do not infer equivalence from generic keywords. */
(function(root){
'use strict';
function fold(s){return String(s||'').toLocaleLowerCase('nl-NL').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').trim()}
function name(s){return fold(s).replace(/^(?:ah|albert heijn|jumbo|lidl)\s+/,'')}
function ean(p){let v=String(p?.ean||'').replace(/\s/g,'');return /^\d{8,14}$/.test(v)?v:null}
function grams(raw){let txt=fold(raw);let m=txt.match(/(\d+(?:[.,]\d+)?)\s*(kg|g|ml|l)\b/);if(!m)return null;let n=Number(m[1].replace(',','.'));return m[2]==='kg'||m[2]==='l'?n*1000:n}
function pack(p){return fold(p?.pack_label||((p?.quantity&&p?.unit)?p.quantity+' '+p.unit:''))}
function sungold(p){let n=name(p?.name);if(!n.includes('zespri')||!n.includes('sungold')&&!n.includes('sun gold'))return false;let size=grams(pack(p))||grams(n);return size===750}
function same(a,b,store){
if(!a||!b)return false;
const x=ean(a),y=ean(b);
if(x&&y)return x===y;
if(sungold(a)&&sungold(b))return true; // explicit exact Zespri SunGold 750g only
const xName=name(a.name),yName=name(b.name);
const xPack=pack(a),yPack=pack(b);
if(!xName||!yName||xName!==yName)return false;
if(xPack&&yPack&&xPack===yPack)return true;
// Missing packaging means the observation is too weak for cross-store equivalence
return !xPack&&!yPack&&a.store===store;
}
// Families group only genuinely related products. A family is NOT an exact-price match.
function familyKey(p){
 const n=name(p?.name);
 const zero=/(?:\b0\s?0\b|\balcoholvrij\b)/.test(n)?'|alcoholvrij':'|regulier';
 if(/\btexels\b/.test(n)&&/\bskuumkoppe\b/.test(n))return 'beer:texels skuumkoppe'+zero;
 if(/\bla chouffe\b/.test(n)&&/\bblond(?:e)?\b/.test(n))return 'beer:la chouffe blond'+zero;
 const base=n.replace(/\b\d+\s*(?:x|×)\s*\d+(?:\s*\d+)?\s*(?:ml|cl|l|g|kg)\b/g,'')
  .replace(/\b\d+\s*(?:ml|cl|l|g|kg)\b/g,'').replace(/\b(bier fles|bier blik)\b/g,'')
  .replace(/\b(fles|blik|6 flesjes|6 blikjes)\b/g,'').replace(/\s+/g,' ').trim();
 return 'product:'+base+(n.includes('0 0')||n.includes('alcoholvrij')?'|alcoholvrij':'');
}
function familyLabel(p){
 const k=familyKey(p);
 if(k.startsWith('beer:texels skuumkoppe'))return 'Texels Skuumkoppe'+(k.endsWith('alcoholvrij')?' 0.0':'');
 if(k.startsWith('beer:la chouffe blond'))return 'La Chouffe Blond'+(k.endsWith('alcoholvrij')?' 0.0':'');
 return name(p?.name);
}
function familyMembers(products){
 const groups=new Map();
 for(const p of products||[]){const k=familyKey(p);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(p)}
 return [...groups].map(([key,items])=>({key,label:familyLabel(items[0]),items}));
}
function record(p,store){
const label=name(p?.name),packageLabel=String(p?.pack_label||'');
return {id:(ean(p)?'ean:'+ean(p):'product:'+label+'|'+fold(packageLabel)+'|'+(packageLabel?'':'shop:'+store)),
 name:String(p?.name||''),pack_label:packageLabel,ean:ean(p),store:String(store||''),added_at:new Date().toISOString()};
}
function find(favorites,p,store){return (Array.isArray(favorites)?favorites:[]).find(f=>same(f,p,store))}
root.MaatjeFavorites={same,record,find,name,pack,sungold,familyKey,familyLabel,familyMembers};
})(window);
