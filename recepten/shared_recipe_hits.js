(function(root){'use strict';
const norm=x=>String(x||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
function select(rows,{query='',cuisine='all',category='all',duration='all',selection='all',strictHealth=false,onlyShared=false,meal='all',format='all',origin='all',mealprep=false}={}){
 if(strictHealth||selection!=='all'||mealprep||!['all','Avondeten'].includes(meal)||!['all','HelloFresh-variant'].includes(origin))return [];
 const terms=norm(query).split(' ').filter(x=>x&&!['met','en','recept','recepten','hello','fresh','hellofresh'].includes(x));
 const cats={chicken:['Kip'],fish:['Vis'],vega:['Vegetarisch'],redmeat:['Vlees'],meat:['Kip','Vlees']};
 return rows.filter(r=>terms.every(t=>norm(r.search_text||r.title).includes(t))&&
 (cuisine==='all'||r.cuisine===cuisine)&&(!cats[category]||cats[category].includes(r.category))&&
 (format==='all'||(/wrap/i.test(r.title)?'wrap':/bowl/i.test(r.title)?'bowl':/salade/i.test(r.title)?'salade':'anders')===format)&&
 (duration==='all'||Number.isFinite(r.minutes)&&r.minutes>0&&r.minutes<=Number(duration))&&
 (onlyShared||terms.length>0||r.has_possible_offer)).sort((a,b)=>Number(b.has_possible_offer)-Number(a.has_possible_offer)||a.title.localeCompare(b.title,'nl'));
}
const api={select,norm};root.SharedRecipeHits=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
