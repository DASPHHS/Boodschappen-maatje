(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.MaatjeFreshness=api;})(typeof window!=='undefined'?window:null,function(){
const valid=x=>typeof x==='string'&&/^\d{4}-\d\d-\d\d$/.test(x)&&!Number.isNaN(Date.parse(x+'T12:00:00Z'));
function ageDays(source,today){if(!valid(source)||!valid(today))return Infinity;return Math.round((Date.parse(today+'T12:00:00Z')-Date.parse(source+'T12:00:00Z'))/86400000)}
function available(feed,generatedAt,today){const source=String(generatedAt||'').slice(0,10),age=ageDays(source,today);if(feed?.status!=='ok'||age<0||age>1||!Array.isArray(feed.offers))return [];return feed.offers.filter(o=>o?.start_date<=today&&o?.end_date>=today).map(o=>age===0?o:{...o,source_scan_stale:true,source_scan_date:source})}
function summary(catalog,today){
const stores=['lidl','jumbo','ah'];
const dates=stores.map(s=>String(catalog?.stores?.[s]?.checked_at||'').slice(0,10));
const complete=stores.every((s,i)=>catalog?.stores?.[s]?.status==='ok'&&valid(dates[i])&&Array.isArray(catalog.stores[s].offers)&&catalog.stores[s].offers.some(o=>o.start_date<=today&&o.end_date>=today));
const date=dates.every(valid)?dates.slice().sort()[0]:null;
const age=ageDays(date,today);
return {text:!complete?'Actiescan onvolledig':age===0?'Acties bijgewerkt vandaag':age===1?'Actiescan van gisteren':age>1&&date?'Actiescan verouderd: '+date:'Actiescan controleren',warn:!complete||age!==0,detail:'Externe actiescan: '+(date||'onbekend')+'. Niet elke prijs is onafhankelijk geverifieerd.'};
}
return {ageDays,available,summary};
});
