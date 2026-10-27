(()=>{
  'use strict';
  const E=window.Winkelhulp,$=id=>document.getElementById(id);
  const names={ah:'AH',jumbo:'Jumbo',lidl:'Lidl'},categories={kip:'Kip',vlees:'Vlees',vis:'Vis',vega:'Vega'};
  const money=n=>new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'}).format(n);
  const day=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const storage={get(k){try{return JSON.parse(localStorage.getItem(k));}catch{return null;}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch{}}};
  let data,store=storage.get('bm-store')||'ah',category='kip',selected,oldPrices=false;
  if(!names[store])store='ah';
  function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
  function link(text,url){const n=el('a',text);try{const u=new URL(url);if(u.protocol!=='https:')return el('span',text);n.href=u.href;n.target='_blank';n.rel='noopener noreferrer';}catch{return el('span',text);}return n;}
  function badge(text,cls=''){return el('span',text,'tag '+cls);}
  function sourceName(r){const f=r.source.file_name;return /surinaam/i.test(f)?'Uit je Surinaamse receptenboek':/meal.prep/i.test(f)?'Uit je mealprep-boek':'Gebaseerd op jouw HelloFresh-recept';}
  function render(){
    if(!data)return;
    for(const b of document.querySelectorAll('[data-store]'))b.setAttribute('aria-pressed',String(b.dataset.store===store));
    for(const b of document.querySelectorAll('[data-category]'))b.setAttribute('aria-pressed',String(b.dataset.category===category));
    $('results-heading').textContent=categories[category]+' bij '+names[store];
    const recipes=E.select(data,store,category,day()),host=$('recipes');host.replaceChildren();$('luxury-recipes').replaceChildren();$('pending-recipes').replaceChildren();
    $('status').textContent=recipes.length+' gerechten · '+recipes.filter(r=>r.complete).length+' volledig geprijsd'+(oldPrices?' op de waarnemingsdatum':'');
    if(recipes.every(r=>!r.sale_count))$('status').textContent+=' · geen voordeligere actie bevestigd';
    if(!recipes.length){host.append(el('p','Voor deze keuze zijn nog geen gecontroleerde bronrecepten beschikbaar.'));return;}
    for(const r of recipes){
      const card=el('article',undefined,'recipe'),left=el('div'),badges=el('div',undefined,'badges');
      if(r.sale_count)badges.append(badge((oldPrices?'Eerder: ':'')+r.sale_count+' actieproduct'+(r.sale_count===1?'':'en'),'sale'));
      badges.append(badge('± '+r.minutes+' min'));
      if(r.portion_note)badges.append(badge('150 g kip p.p.'));
      if(r.complete)badges.append(badge(r.used_total<=10?'Doel gehaald':r.used_total<=13?'Binnen budget':r.used_total<=20?'Boven €13':'Uitzondering · boven €20',r.used_total>13?'warn':''));
      left.append(badges,el('h3',r.title));
      const price=el('div',undefined,'price'+(!r.complete?' pending':''));
      if(r.complete){price.append(document.createTextNode(money(r.per_serving)),el('small',(oldPrices?'eerder, ':'')+'per portie'),el('small',money(r.used_total)+' voor 4'));}
      else price.append(document.createTextNode('Prijs nog open'),el('small','mist prijs of productcontrole'));
      const bottom=el('div',undefined,'recipe-bottom');bottom.append(el('span',sourceName(r),'provenance'));
      const button=el('button','Boodschappen →','open-list');button.setAttribute('aria-label','Boodschappen voor '+r.title);button.addEventListener('click',()=>openRecipe(r));bottom.append(button);
      card.append(left,price,bottom);(r.complete?(r.used_total<=13?host:$('luxury-recipes')):$('pending-recipes')).append(card);
    }
    const luxury=recipes.filter(r=>r.complete&&r.used_total>13).length,pending=recipes.filter(r=>!r.complete).length;
    $('luxury-section').hidden=!luxury;$('pending-section').hidden=!pending;
    $('luxury-heading').textContent='Duurder dan €13 · '+luxury+' gerechten voor af en toe';
    $('pending-heading').textContent='Nog te prijzen · '+pending+' gerechten';
    if(!host.children.length)host.append(el('p','Nog geen volledig geprijsd gerecht binnen €13. Bekijk de andere opties hieronder.','notice'));
  }
  function checkKey(r){return 'bm-checked:'+store+':'+r.id;}
  function showTotals(r){
    const host=$('shopping-totals');host.replaceChildren();
    const entries=r.complete?[[money(r.used_total),'verbruik voor 4 porties'],[money(r.per_serving),'per portie'],[money(r.checkout),'kassa: hele verpakkingen']]:[[money(r.known_used),'bekend verbruik: alleen subtotaal'],[money(r.known_checkout),'bekende verpakkingen: subtotaal']];
    for(const [value,label] of entries){const n=el('div');n.append(el('strong',value),el('span',label));host.append(n);}
    if(!r.complete)host.append(el('p','De volledige maaltijdprijs staat nog open.','muted'));
    if(oldPrices)host.append(el('p','Oudere prijswaarneming; controleer de prijzen in de winkel.','muted'));
  }
  function openRecipe(r){
    selected=r;$('shopping-store').textContent=names[store]+' · '+categories[r.category];$('shopping-title').textContent=r.title;
    showTotals(r);const host=$('shopping-list');host.replaceChildren();$('copy-status').textContent='';
    const checked=new Set(storage.get(checkKey(r))||[]);
    for(const x of r.ingredients){
      const row=el('div',undefined,'shopping-row'),input=el('input');input.type='checkbox';input.id='item-'+x.key;input.checked=checked.has(x.key);row.classList.toggle('checked',input.checked);
      input.addEventListener('change',()=>{input.checked?checked.add(x.key):checked.delete(x.key);row.classList.toggle('checked',input.checked);storage.set(checkKey(r),[...checked]);});
      const label=el('label');label.htmlFor=input.id;label.append(el('strong',x.label),el('span','Nodig: '+E.quantity(x.quantity,x.unit),'needed'));
      const p=x.price,price=el('div',undefined,'row-price');
      if(p){
        label.append(el('span','Pak '+p.packages+' × '+E.quantity(p.package_quantity,p.unit)+' · '+p.product,'product'));
        label.append(badge(p.sale?'ACTIE · '+p.condition+(p.loyalty?' · klantenkaart':''):'Reguliere prijs',p.sale?'sale':''));
        if(p.sale)label.append(el('span','Geldig t/m '+p.valid_until,'product'));
        if(p.sale&&p.source==='Foldercontrole')label.append(link('Gecontroleerde folderprijs',p.url));
        if(p.form_note)label.append(el('span',p.form_note,'product form-warning'));
        if(p.leftover)label.append(el('span','Over: '+E.quantity(p.leftover,p.unit),'product'));
        if(p.cheaper_regular)label.append(el('span','Goedkoper regulier alternatief: '+p.cheaper_regular.product+' · '+money(p.cheaper_regular.used)+' verbruik.','alternative'));
        price.append(document.createTextNode(money(p.checkout)),el('small','bij de kassa'));
      }else{label.append(el('span','Verpakking en prijs in de winkel controleren.','product'));price.append(badge('PRIJS OPEN','warn'));}
      row.append(input,label,price);host.append(row);
    }
    const info=$('recipe-info');info.replaceChildren();
    info.append(el('p',r.instructions),el('p','Aanpassing: '+r.adaptation),el('p','De hoeveelheden zijn een eigen vierportiesvariant; de aanpassingen staan hierboven.'));
    if(r.portion_note)info.append(el('p',r.portion_note));
    info.append(el('strong','Oorspronkelijk recept'),el('p',r.source.title),link('Open '+r.source.file_name,r.source.url));
    $('shopping').querySelector('.recipe-info').open=false;
    if(!$('shopping').open)$('shopping').showModal();
    $('shopping').scrollTop=0;
  }
  async function load(){
    $('load-error').hidden=true;$('status').textContent='Je recepten worden geladen…';let offline=false;
    try{const response=await fetch('data.json',{cache:'no-cache'});if(!response.ok)throw Error('http');const value=await response.json();if(value.schema_version!==1||!value.stores)throw Error('schema');data=value;storage.set('bm-last-data',data);}
    catch{data=storage.get('bm-last-data');offline=true;if(!data?.stores){$('load-error').hidden=false;$('status').textContent='';return;}}
    oldPrices=E.stale(data.prices_observed_at);
    $('freshness').hidden=!oldPrices&&!offline;
    $('freshness').textContent=offline?'Je bekijkt een bewaard overzicht. Controleer prijzen en acties in de winkel.':'De prijsgegevens zijn ouder dan 36 uur. Bedragen zijn eerdere waarnemingen.';
    const date=new Date(data.prices_observed_at);$('price-date').textContent='Prijswaarneming: '+(Number.isFinite(date.getTime())?date.toLocaleString('nl-NL',{timeZone:'Europe/Amsterdam',dateStyle:'medium',timeStyle:'short'}):'nog niet bekend');
    $('source-summary').textContent=data.coverage_note;
    const files=$('source-files');files.replaceChildren();
    const labels={text_read:'Tekst ontsloten',ocr_needs_review:'OCR: controle nodig',not_processed:'Nog niet verwerkt'};
    for(const f of data.source_files){const n=el('li',f.title);n.append(el('small',(labels[f.status]||'Status onbekend')+' · '+f.used_in_selection+' geselecteerde recepten'));files.append(n);}
    render();
  }
  $('stores').addEventListener('click',e=>{const b=e.target.closest('[data-store]');if(!b)return;store=b.dataset.store;storage.set('bm-store',store);render();});
  $('categories').addEventListener('click',e=>{const b=e.target.closest('[data-category]');if(!b)return;category=b.dataset.category;render();});
  for(const b of document.querySelectorAll('[data-close]'))b.addEventListener('click',()=>$(b.dataset.close).close());
  $('sources-button').addEventListener('click',()=>$('sources').showModal());$('retry').addEventListener('click',load);
  $('reset-list').addEventListener('click',()=>{if(selected){storage.set(checkKey(selected),[]);openRecipe(selected);}});
  $('copy-list').addEventListener('click',async()=>{if(!selected)return;try{await navigator.clipboard.writeText(E.listText(selected,names[store]));$('copy-status').textContent='Gekopieerd. Plak de lijst in je notities.';}catch{$('copy-status').textContent='Kopiëren lukt hier niet. Je kunt de producten in deze lijst afvinken.';}});
  load();
})();
