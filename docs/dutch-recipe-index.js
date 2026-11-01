/* Dutch-language recipe directory built exclusively from individually identified
 * publishers' links and clearly identified lower-confidence sitemap titles.
 * This module does not copy publisher photographs or recipe instructions. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.MaatjeDutchGuide=api;
})(typeof window!=='undefined'?window:null,function(){
 'use strict';
 const categories=[
  {key:'alle',title:'Alle recepten'},
  {key:'groenten',title:'Met groenten'},
  {key:'peulvruchten',title:'Peulvruchten & tofu'},
  {key:'kip',title:'Met kip'},
  {key:'vlees',title:'Met vlees'},
  {key:'vis',title:'Met vis'}
 ];
 const veg=new Set(['broccoli','bloemkool','spinazie','pompoen','paprika','courgette','aubergine','sperziebonen','tomaten','champignons','wortel','paksoi','prei','spitskool','boerenkool','venkel']);
 const legumes=new Set(['kikkererwten','linzen','bonen','tofu']);
 const meats=new Set(['riblappen','gehakt','varkenshaas','hamlappen']);
 const fish=new Set(['zalm','witvis','garnalen','makreel','forel']);
 const validStatus=new Set(['handmatig_gevonden_bij_uitgever','publisher_metadata_verified','publisher_sitemap_title_only']);
 const lower=x=>String(x||'').toLocaleLowerCase('nl-NL').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 function trusted(recipe){
  if(!recipe||!validStatus.has(recipe.review_status)||!Array.isArray(recipe.families)||!recipe.families.length||
    typeof recipe.title!=='string'||recipe.title.length<6||typeof recipe.url!=='string')return false;
  try{
   const u=new URL(recipe.url);
   return u.protocol==='https:'&&
    ((recipe.source==='Allerhande'&&u.hostname==='www.ah.nl'&&u.pathname.startsWith('/allerhande/'))||
     (recipe.source==='Jumbo'&&u.hostname==='www.jumbo.com'&&u.pathname.startsWith('/recepten/')));
  }catch{return false}
 }
 function suitable(recipe,category='alle'){
  const fam=new Set(recipe.families||[]);
  if(category==='alle')return true;
  if(category==='groenten')return [...fam].some(x=>veg.has(x));
  if(category==='peulvruchten')return [...fam].some(x=>legumes.has(x));
  if(category==='kip')return fam.has('kip');
  if(category==='vlees')return [...fam].some(x=>meats.has(x));
  if(category==='vis')return [...fam].some(x=>fish.has(x));
  return false;
 }
 function label(recipe){
  return recipe.review_status==='publisher_sitemap_title_only'?
   'Uit officiële sitemap · inhoud nog niet gecontroleerd':
   recipe.review_status==='publisher_metadata_verified'?
    'Uitgeversmetadata gecontroleerd':'Geselecteerde uitgeverslink';
 }
 function rank(recipe){
  const fam=recipe.families||[];
  const first=recipe.review_status==='publisher_sitemap_title_only'?0:100;
  return first+(recipe.course==='hoofdgerecht'?20:0)+
   Math.min(3,fam.filter(x=>veg.has(x)).length)*6+
   (fam.some(x=>legumes.has(x))?8:0)+
   (recipe.servings===4?3:0)+(recipe.minutes&&recipe.minutes<=45?3:0);
 }
 function browse(index,{category='alle',query='',onlySelected=false,limit=0}={}){
  const safeCategory=categories.some(c=>c.key===category)?category:'alle';
  const q=lower(query).trim();
  const seen=new Set(),rows=[];
  for(const r of index?.recipes||[]){
   if(!trusted(r)||!suitable(r,safeCategory))continue;
   if(onlySelected&&r.review_status==='publisher_sitemap_title_only')continue;
   if(q&&!lower([r.title,r.source,...r.families,r.method].join(' ')).includes(q))continue;
   if(seen.has(r.url))continue;
   seen.add(r.url);rows.push(r);
  }
  rows.sort((a,b)=>rank(b)-rank(a)||a.title.localeCompare(b.title,'nl'));
  return limit>0?rows.slice(0,limit):rows;
 }
 function overview(index){
  return categories.map(c=>({...c,count:browse(index,{category:c.key}).length}));
 }
 return {categories,trusted,suitable,label,rank,browse,overview};
});
