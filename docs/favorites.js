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
function record(p,store){
const label=name(p?.name),packageLabel=String(p?.pack_label||'');
return {id:(ean(p)?'ean:'+ean(p):'product:'+label+'|'+fold(packageLabel)+'|'+(packageLabel?'':'shop:'+store)),
 name:String(p?.name||''),pack_label:packageLabel,ean:ean(p),store:String(store||''),added_at:new Date().toISOString()};
}
function find(favorites,p,store){return (Array.isArray(favorites)?favorites:[]).find(f=>same(f,p,store))}
root.MaatjeFavorites={same,record,find,name,pack,sungold};
})(window);
