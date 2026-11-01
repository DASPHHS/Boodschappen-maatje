#!/usr/bin/env node
/* Rebuild the public Netherlands-first recipe directory from the exact
 * publisher index that Boodschappenmaatje displays. No publisher recipe copy. */
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const guide=require('../docs/dutch-recipe-index.js');
const index=JSON.parse(fs.readFileSync(path.join(root,'docs/data/publisher-recipes.json'),'utf8'));
const esc=x=>String(x??'').replace(/\\/g,'\\\\').replace(/\|/g,'\\|').replace(/\[/g,'\\[').replace(/\]/g,'\\]');
const stamp=index.generated_at||'niet bekend';
const count=guide.browse(index).length;
const selected=guide.browse(index,{onlySelected:true}).length;
const anchor=x=>x.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9 -]/g,'').trim().replace(/\s+/g,'-');
const cats=guide.categories.filter(c=>c.key!=='alle');
let lines=[
 '# Nederlandse receptengids – Boodschappenmaatje','',
 '> Een openbare, Nederlandstalige selectie van bestaande kookrecepten, geïnspireerd door de **overzichtsopzet** van [awesome-recipes](https://github.com/bbbenji/awesome-recipes), maar met eigen selectie en broncontrole.',
 '',
 '**'+count+' directe receptverwijzingen** · **'+selected+' geselecteerde uitgeverslinks** · '+(count-selected)+' aanvullende titels uit een officiële sitemap · laatste indexpublicatie '+stamp+'.',
 '',
 'Bekijk de [receptenzoeker in Boodschappenmaatje](https://dasphhs.github.io/Boodschappen-maatje/docs/#recepten) voor suggesties bij actuele aanbiedingen van **Lidl, Jumbo en Albert Heijn**.',
 '',
 '## Inhoud','',
 ...cats.map(c=>'- ['+c.title+'](#'+anchor(c.title)+')'),
 '- [Herkomst en kwaliteit](#herkomst-en-kwaliteit)',
 '',
 'Geen recepten met onrechtmatig overgenomen bereidingsteksten, foto’s of auteursrechtelijk beschermd uitgeversmateriaal. Open voor de volledige bereiding altijd het originele recept bij de uitgever.',
 ''
];
for(const cat of cats){
 const rows=guide.browse(index,{category:cat.key});
 lines.push('## '+cat.title,'',rows.length+' recepten binnen deze ingrediëntcategorie. Een recept kan onder meerdere ingrediënten voorkomen. De categorie is **geen garantie** voor vegetarisch, gezonde voedingswaarden, allergenen of bereidingsgeschiktheid.','');
 lines.push('| Recept | Bron | Onderbouwing | Bereiding / porties |','| --- | --- | --- | --- |');
 for(const r of rows){
  const summary=[r.minutes?String(r.minutes)+' min':'Tijd niet gecontroleerd',r.servings?String(r.servings)+' personen':'Porties niet gecontroleerd'].join(' · ');
  lines.push('| ['+esc(r.title)+']('+r.url+') | '+esc(r.source)+' | '+esc(guide.label(r))+' | '+esc(summary)+' |');
 }
 lines.push('');
}
lines.push(
 '## Herkomst en kwaliteit','',
 '- **Geselecteerde uitgeverslink:** rechtstreeks gevonden bij Allerhande of Jumbo. Titel, link en beperkte metadata opgenomen; geen proefkookcontrole en niet automatisch compleet geprijsd.',
 '- **Uitgeversmetadata gecontroleerd:** titel, receptschema, ingrediëntenfamilies en algemene bereidingseigenschappen uit publiek beschikbare gestructureerde metadata. Geen volledige tekst of foto’s overgenomen.',
 '- **Uit officiële sitemap · inhoud nog niet gecontroleerd:** de uitgever publiceerde een specifieke recept-URL, maar geautomatiseerde paginaopvraging werd geblokkeerd of gaf geen verifieerbare receptgegevens. Ingrediënten zijn **uitsluitend uit de recepttitel afgeleid** en kunnen onvolledig zijn; kooktijd en porties worden niet ingevuld.',
 '- **Voedingskwaliteit:** geen automatisch recept wordt als gezond, caloriearm, zoutarm, vegetarisch of proefgekookt aangemerkt zonder voldoende onafhankelijke voedingsinformatie.',
 '- **Winkelprijzen:** receptenlinks hebben geen complete kassamand. Aanbiedingen zijn externe winkelwaarnemingen en vereisen controle van prijs, productvariant en datum.',
 '',
 '### Bronnen en hergebruik','',
 '- [Allerhande (Albert Heijn)](https://www.ah.nl/allerhande/recepten-zoeken) en [Jumbo recepten](https://www.jumbo.com/recepten/zoeken) zijn rechthebbenden van hun eigen recepten en foto’s.',
 '- Voor de **openbare indelingsstructuur** is [bbbenji/awesome-recipes](https://github.com/bbbenji/awesome-recipes) geraadpleegd (CC0); de recepten zelf zijn niet uit dat project gekopieerd.',
 '- De publieke [Checkjebon](https://github.com/supermarkt/checkjebon)-data ondersteunen winkelprijswaarnemingen in onze app, maar niet de verificatie van deze recepten.',
 '',
 '### Onderhoud','',
 'Deze gids wordt automatisch gegenereerd met `node scripts/build_dutch_recipe_guide.cjs` uit `docs/data/publisher-recipes.json`. De wekelijkse ontdekker werkt de gids samen met de receptindex bij. Wijzig of controleer nieuwe recepten in de index in plaats van hier handmatig onbevestigde links toe te voegen.',''
);
const output=lines.join('\n');
const target=path.join(root,'NEDERLANDSE_RECEPTENGIDS.md');
if(process.argv.includes('--check')){
 const current=fs.readFileSync(target,'utf8');
 if(current!==output)throw Error('Nederlandse receptengids loopt achter op receptenindex');
 console.log('Nederlandstalige gids klopt: '+count+' recepten, '+selected+' geselecteerde bronnen');
}else{
 fs.writeFileSync(target,output,'utf8');
 console.log('Nederlandse receptengids gegenereerd: '+count+' recepten in '+cats.length+' categorieën');
}
