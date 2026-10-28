(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.MaatjeFreshness=api;})(typeof window!=='undefined'?window:null,function(){
const valid=x=>typeof x==='string'&&/^\d{4}-\d\d-\d\d$/.test(x)&&!Number.isNaN(Date.parse(x+'T12:00:00Z'));
function ageDays(source,today){if(!valid(source)||!valid(today))return Infinity;return Math.round((Date.parse(today+'T12:00:00Z')-Date.parse(source+'T12:00:00Z'))/86400000)}
function available(feed,generatedAt,today){const source=String(generatedAt||'').slice(0,10),age=ageDays(source,today);if(feed?.status!=='ok'||age<0||age>1||!Array.isArray(feed.offers))return [];return feed.offers.filter(o=>o?.start_date<=today&&o?.end_date>=today).map(o=>age===0?o:{...o,source_scan_stale:true,source_scan_date:source})}
return {ageDays,available};
});
