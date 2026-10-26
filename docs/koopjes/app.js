'use strict';
const $=id=>document.getElementById(id),E=BMDeals,names={ah:'Albert Heijn',jumbo:'Jumbo',lidl:'Lidl',action:'Action'};
const money=n=>'€ '+n.toLocaleString('nl-NL',{minimumFractionDigits:2,maximumFractionDigits:2});
let rows=[],limit=60,matches=[];const today=new Date().toLocaleDateString('sv-SE',{timeZone:'Europe/Amsterdam'});
function el(tag,text,cls){const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(cls)x.className=cls;return x;}
function render(){matches=E.search(rows,{q:$('q').value,brand:$('brand').value,store:$('store').value,cat:$('cat').value,sale:$('sale').checked,loyalty:$('loyalty').checked,minDiscount:+$('discount').value,sort:$('sort').value});$('status').textContent=matches.length+' resultaten · '+Math.min(limit,matches.length)+' getoond';$('results').replaceChildren(...matches.slice(0,limit).map(x=>{
 const card=el('article');card.append(el('div',names[x.store]||x.store,'muted'),el('h2',x.name),el('p',x.state==='active'?'Nu in aanbieding'+(x.loyalty?' · klantenkaart vereist':''):'Reguliere bronprijs','tag'),el('div',money(x.price),'price'));
 card.append(el('p',x.packages>1?x.packages+' verpakkingen voor dit kassabedrag':'1 verpakking'));
 card.append(el('p',x.unitPrice!==null?money(x.unitPrice)+' per '+x.measure.unit:'Eenheidsprijs onbekend: inhoud niet bevestigd'));
 if(x.discount)card.append(el('p','Referentie '+money(x.previous*x.packages)+' · '+Math.round(x.discount)+'% korting'));
 if(x.end)card.append(el('p','Geldig '+x.start+' t/m '+x.end,'muted'));
 if(/^https:\/\//.test(x.url||'')){const a=el('a','Bekijk product bij bron →');a.href=x.url;a.target='_blank';a.rel='noopener noreferrer';card.append(a);}return card;}));$('more').hidden=matches.length<=limit;}
for(const id of ['q','brand','store','cat','sale','loyalty','discount','sort'])$(id).addEventListener(['q','brand'].includes(id)?'input':'change',()=>{limit=60;render();});$('more').onclick=()=>{limit+=60;render();};
Promise.all([fetch('../recepten/winkelprijzen.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();}),fetch('./retailer-prices.json').then(r=>{if(!r.ok)throw Error();return r.json();}).catch(()=>null)]).then(([data,extra])=>{
 const age=extra?(Date.now()-Date.parse(extra.updated_at))/3600000:Infinity;
 if(extra&&age>=0&&age<36){data.stores={...data.stores,...extra.stores};$('updated').textContent='Action gecontroleerd: '+extra.updated_at+'. ';}
 else $('updated').textContent='Action-prijzen ontbreken of zijn ouder dan 36 uur. ';

 rows=E.catalog(data,today);$('updated').textContent+='Prijsimport: '+data.updated_at+' · controledag '+today;
 for(const [store,src] of Object.entries(data.stores||{})){const opt=el('option',names[store]||store);opt.value=store;$('store').append(opt);const tr=el('tr');for(const text of [names[store]||store,(src.ordinary||[]).length,rows.filter(x=>x.store===store&&x.state==='active').length])tr.append(el('td',String(text)));$('coverage').append(tr);}
 for(const cat of [...new Set(rows.map(x=>x.category))].sort()){const o=el('option',cat);o.value=cat;$('cat').append(o);}const q=new URLSearchParams(location.search).get('q');if(q)$('q').value=q;render();
}).catch(()=>{$('status').textContent='Productprijzen konden niet worden geladen. Probeer opnieuw of bekijk Scanstatus.';$('status').className='error';});
