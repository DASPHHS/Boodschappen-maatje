# Boodschappenmaatje

Een nieuwe mobiele GitHub Pages-app voor Lidl, Jumbo en Albert Heijn. **De gebruiker bekijkt alle drie winkels en kiest zelf één winkel voor de boodschappenronde.** Er wordt nooit stilzwijgend één winnaar gekozen.

**App:** https://dasphhs.github.io/Boodschappen-maatje/

## Navigatie

- **Vandaag**: aparte statuskaarten voor de drie supermarkten.
- **Aanbiedingen**: echte actieve acties per winkel, met prijsvergelijking en geldigheidscontrole.
- **Recepten**: dagelijkse en wekelijkse, winkelgebonden recepten plus een bestaande algemene receptenbibliotheek.
- **Mijn lijst**: één gekozen supermarkt, gekozen recepten en afvinkbare samengevoegde ingrediënten.

De eerdere implementatie is bewaard op branch \`backup/voor-herbouw-2026-10-28\`. De nieuwe hoofdbranch bevat uitsluitend het overzichtelijke platform.

## Dagelijkse publicatie vanuit ChatGPT-taken

Schrijf op elke dagelijkse uitvoering **docs/data/daily.json**; schrijf op de wekelijkse uitvoering **docs/data/weekly.json**. Gebruik de GitHub-connector om het bestaande bestand te lezen en vervolgens te vervangen. GitHub Pages toont na publicatie automatisch de nieuwe JSON. **Er is geen aparte server of API-sleutel nodig om de gepubliceerde gegevens te lezen**. De inhoud moet wel door de taken van correcte, actuele bronnen worden voorzien. Als een taak niet naar GitHub kan schrijven, is de website niet bijgewerkt: dat moet expliciet worden gemeld.

De taken in ChatGPT moeten toegang behouden tot GitHub. Omdat toekomstige schrijfacties pas bij uitvoering gebeuren, kan hun slagen niet vooraf worden gegarandeerd. De initiële bestanden zijn bewust leeg: **geen verzonnen aanbiedingen of prijzen**.

### JSON-contract, \`docs/data/daily.json\` en \`docs/data/weekly.json\`

\`\`\`json
{
  "schema_version": 1,
  "generated_at": "2026-10-28T08:00:00+01:00",
  "stores": {
    "lidl": {"checked_at": "2026-10-28", "offers": [], "recipes": []},
    "jumbo": {"checked_at": "2026-10-28", "offers": [], "recipes": []},
    "ah": {"checked_at": "2026-10-28", "offers": [], "recipes": []}
  }
}
\`\`\`

Beide bestanden bevatten **altijd alle drie de supermarktkeys**, ook als voor één winkel data ontbreekt. Voeg expliciet een status of toelichting toe bij ontbrekende controle. Nooit ontbrekende velden als bevestiging interpreteren.

**Offer-model:**

\`\`\`json
{"id":"lidl-voorbeeld","name":"Groente 500 g","category":"vega","price":0.99,"regular_price":1.39,"pack_label":"500 g","unit_price":1.98,"unit":"kg","start_date":"2026-10-26","end_date":"2026-11-01","verified":true,"member_required":false,"source":{"label":"Officiële folder","url":"https://www.lidl.nl/"},"cheapest_alternative":{"name":"Goedkoopste passende reguliere variant","price":1.09}}
\`\`\`

Dit is **alleen een schema-voorbeeld, geen actuele deal**. \`verified:true\` betekent dat prijs en actieperiode controleerbaar zijn, niet dat voorraad of filiaalkassa zijn gegarandeerd. Als producten een ander gewicht hebben, vergelijk eerst de prijs per kg/liter en het eetbare of uitlekgewicht. \`cheapest_alternative\` alleen invullen als producten daadwerkelijk vergelijkbaar zijn.

**Recipe-model:**

\`\`\`json
{"id":"ah-2026-10-28-1","title":"Groentrijke kiproerbak","category":"kip","cuisine":"Aziatisch","servings":4,"minutes":25,"ingredients":[{"name":"Kipfilet","quantity":800,"unit":"g","department":"Eiwitbronnen","pack_price":7.99},{"name":"Wokgroenten","quantity":1200,"unit":"g","department":"Groente & fruit","pack_price":3.99}],"instructions":["Snij en bereid de ingrediënten.","Bak en serveer."],"cost":{"basket_total":11.98,"estimated":false},"macros":{"kcal":410,"protein_g":48,"carbs_g":18,"fat_g":16},"macro_status":"estimated"}
\`\`\`

Ook dit is een **schema-voorbeeld, geen geverifieerd gerecht**. Gebruik uitsluitend echte prijzen voor \`basket_total\`. Dat is de **kassaprijs voor alle volledige benodigde verpakkingen**, niet alleen de kosten van gebruikte grammen. Macro's moeten per portie voor vier porties zijn en als schatting worden gelabeld tenzij werkelijk berekend met bekende productsamenstelling. Richtcriteria: minimaal 300 g groente en 150 tot 200 g kip/vlees/vis per portie, of passende plantaardige eiwitten; streef naar ≤ € 10 kassabedrag per vier porties. Toon budgetoverschrijdingen eerlijk.

**Aandachtspunt:** als één supermarkt slechts gedeeltelijk geverifieerde producten heeft, mag dat niet als een volledig geprijsd menu worden gepresenteerd. Vergelijk actieprijzen met goedkoopste passende reguliere alternatieven.

## Bestanden

- \`docs/index.html\`, \`docs/style.css\`, \`docs/app.js\`: volledige statische applicatie.
- \`docs/data/daily.json\`: dagelijkse brongecontroleerde aanbiedingen en bijbehorende recepten.
- \`docs/data/weekly.json\`: wekelijkse nieuwe budgetrecepten per winkel.
- \`docs/data/library.json\`: 40 bestaande algemene recepten uit de oude repository, **zonder actuele prijsclaims**.
- \`scripts/validate.mjs\`: controle van de JSON-contracten.
- \`.github/workflows/validate.yml\`: valideert publicatie bij wijzigingen.

## Lokale controle

\`\`\`sh
node scripts/validate.mjs
python -m http.server 8000 --directory docs
\`\`\`

Ga naar http://localhost:8000. GitHub Pages moet op branch \`main\` met bron \`/docs\` ingesteld staan; de bestaande repository gebruikte \`/docs\`. Bij het opnieuw koppelen van Pages de bron eventueel controleren.


## Actiekoppeling, sorteren en groeiend archief

Recepten worden per supermarkt afzonderlijk getoond, inclusief **minimaal tien bestaande inspiratievarianten in elk van de categorieën kip, vlees (rund/varken), vis en vega**. Dat betekent **niet** dat er tien actuele geverifieerde actiegebonden recepten per categorie zijn; daarvoor zijn actuele relevante aanbiedingen en volledige productprijzen vereist.

Drie labels zijn essentieel:
- **Actie in prijs verwerkt**: recept bevat een \`offer_links\`-relatie naar een op die datum geldige, geverifieerde aanbieding, met \`offer_id\`, \`ingredient_name\`, \`match_type:"exact"\`; het bijbehorende ingrediënt heeft \`price_status:"folder_current"\`. Iedere koppeling moet ook qua verpakking, hoeveelheden en voorwaarden werkelijk passen. De prijs hoeft nog niet volledig op dezelfde dag gecontroleerd te zijn: dat blijft een aparte waarschuwing.
- **Past bij aanbieding**: een productnaam/ingrediënt lijkt compatibel met een actuele aanbieding, maar de prijs is nog niet opnieuw berekend en de vervangbaarheid moet gecontroleerd worden. Een match is géén bewijs voor besparing.
- **Geen actie gekoppeld**: het gerecht is niet aantoonbaar actiegebonden.

Sorteren is mogelijk op aantal gekoppelde acties, laagste **werkelijk bekende** kassaprijs (onbekend komt achteraan), eiwit en bereidingstijd. Actiefilter: alle / actieprijs verwerkt / mogelijke matches. Een actiekorting wordt alleen getoond zolang de aanbieding geldig is.

Archiveer toekomstige dagelijkse of wekelijkse unieke recepten in **docs/data/archive.json** onder \`stores.lidl\`, \`stores.jumbo\`, \`stores.ah\`, met \`id\` als unieke sleutel, \`first_seen_at\` en \`last_seen_at\`. Archiveer alleen recepten die echt volledig genoeg zijn, niet alleen titels. Vermijd duplicaten; dezelfde naam met een andere winkel blijft een eigen record. De site toont archiefrecepten **zonder oude prijzen als actuele prijzen**. Bewaar bron-URL, prijspeildatum, en markeer oude aanbiedingen als verlopen.

De complete actuele prijs- en actierapportage blijft in \`docs/data/daily.json\`; de wekelijkse nieuwe recepten in \`docs/data/weekly.json\`. Werk na een succesvolle run eventueel het archief bij in een tweede GitHub-commit; schrijf nooit fictieve prijzen om een doelstelling te halen. De productdekking kan incompleet blijven bij Lidl, Jumbo en AH. Onderbouw alleen prijsverschillen wanneer exact vergelijkbare alternatieven en verpakkingsprijzen geverifieerd zijn.

### Extra filters voor vlees en vis

Met de vleeschip kies je **rund** of **varken**; met de vischip kies je **vette (omega-3-rijke) vis** of **magere vis**. Deze groepen worden uit de expliciete ingrediënt- of productnaam afgeleid, zonder ongespecificeerd gehakt zomaar als rund/varken aan te merken. Bij sommige recepten kan de precieze vissoort nog onbekend zijn. Visadvies: https://www.voedingscentrum.nl/encyclopedie/vis .


## Brede actiecatalogus en receptenmotor

\`scripts/sync_aanbiedingen.py\` gebruikt dagelijks het publieke PrijsProfeet-endpoint \`/products/promotional/all\` voor Lidl, Jumbo en Albert Heijn; de resultaten komen in \`docs/data/offers-catalog.json\`. De GitHub-workflow \`actiecatalogus.yml\` draait om 07.35 Nederlandse tijd (onder voorbehoud van een geslaagde run). De bronvermelding PrijsProfeet is vereist. Een prijs uit deze feed is niet zelfstandig geverifieerd en bevat geen volledig regulier assortiment.

\`docs/recipe-engine.js\` genereert per supermarkt uiteenlopende wereldkeuken-ideeën rond actieve aanbiedingen voor eiwitbronnen, met minimaal 1200 g voorgestelde groenten per vier porties. Deze ideeën krijgen het label **Actie als basis**. Hun volledige kassaprijs en macro's blijven onbekend totdat alle ingrediënten en verpakkingen geprijsd en berekend zijn. Alleen handmatig/aantoonbaar verbonden en al verwerkte acties krijgen het label **Actieprijs verwerkt**. De permanente bibliotheek van veertig recepten blijft aanwezig als gezonde, mogelijk budgetvriendelijke inspiratie, zonder ongefundeerde 'altijd goedkoop'-garantie.


### Budgetbasis zonder aanbiedingen

De startpagina toont afzonderlijk recepten die zonder verwerkt actieproduct onder €10 uitkwamen in een eerder berekende prijswaarneming. De kaart vermeldt expliciet dat het om een **tijdgebonden prijsindicatie** gaat, niet om een gegarandeerde 'altijd goedkoop'-prijs. Bij nieuwe actuele reguliere schapprijzen kunnen deze gerechten opnieuw beoordeeld worden en in rangorde stijgen.

## Specifieke foutcorrectie van 28 oktober 2026

De eerdere synthetische receptenmotor is uit de app uitgeschakeld omdat hij herhaaldelijk ongerelateerde productnamen kon koppelen (zoals kipkruiden als kip of plantaardige zalm als gezonde vis). Alleen de dagelijkse geprijsde recepten, geverifieerde folderrecepten met exacte hoofdproductregels, het wekelijkse repertoire en algemene originele bibliotheekrecepten worden nu getoond. Prijzen blijven null zolang de volledige kassamand niet betrouwbaar kan worden berekend. De foldervoorbeelden in docs/data/spotlight.json hebben een bron-URL en zijn aflopend; het bestand is voor 28 oktober t/m 3 november 2026 en moet daarna vervangen worden.

De vers-vs-diepvriesvergelijking voor Jumbo sperziebonen wordt uitsluitend op gelijke gewichtseenheden gemaakt: 400g vers €1,99 (€4,98/kg) versus 1kg diepvries €2,07 (€2,07/kg), op basis van de waarnemingen op 28 oktober 2026. De klant moet beschikbaarheid controleren.

Thematische inspiratie voor enkele nieuwe recepten komt uit de aan de gebruiker gekoppelde Google Drive-kookboeken Recepten uit Zuid-oost-Azië en Sandhia's Surinaamse Recepten. We hebben hieruit nieuwe eigen varianten uitgewerkt, geen letterlijke overnames.


## Extra internationale recepten (28 oktober)
De bibliotheek bevat acht nieuwe originele recepten (twee kip, twee vlees, twee vis, twee vegetarisch), gebaseerd op de algemene culinaire en gezonde kookprincipes van het Voedingscentrum en Allerhande. De bron-URL staat bij ieder nieuw recept. Elk gerecht is voor vier personen met minstens 300 gram groente per portie. Kassaprijzen en macro's zijn bewust onbekend zolang de benodigde product- en verpakkingsgegevens niet voor een specifieke winkel zijn gecontroleerd. Dit zijn geen bewezen 'altijd goedkoop'-recepten of geverifieerde aanbiedingen.


## Prijsbetrouwbaarheid (bronstatus, geen absolute garanties)

De UI zegt bij een aanbieding uitsluitend **Officiële actiebron** als de bron-URL daadwerkelijk de website van dezelfde retailer is (Jumbo, AH of Lidl), de actie nog binnen haar geldigheidsperiode valt en de gegevens als geverifieerd zijn gemarkeerd. PrijsProfeet, folderaggregatoren en andere vergelijkers krijgen in plaats daarvan een duidelijk **Externe prijswaarneming** of **Folder- of vergelijkingsbron**-label. Een officieel bronlabel is nog steeds geen filiaalvoorraad- of kassagarantie.

Het 'Voor mij'-blok met duidelijke prijsverschillen toont voortaan alleen actieprijzen met de officiële winkel als bron en een bekende oude prijs. De prijsverschillen in de recepten zijn niet per definitie werkelijke besparingen ten opzichte van huismerken, diepvries of een ander assortiment. Zolang een volledige, vergelijkbare mand ontbreekt, wordt de totale besparing niet als bevestigd weergegeven. Een product zonder bekend alternatief mag nooit als 'goedkoopste van alle winkels' worden aangeduid.

### AH week 44 en overzicht (28 oktober)
Nieuwe AH-spotlight: 11 recepten die werkelijk matchen met AH Varkensgehakt, Terra plantaardige kipstukjes, scharrelkipfilethaasjes, spruitjes, bloemkool of flespompoen. Geen macrowaarden en geen volledige kassaprijzen zonder voldoende gegevens. De startpagina toont nu uitgelichte actierecepten en actuele relevante producten voor álle drie winkels. De categorie Productfavorieten heeft een eigen ingang in het linkermenu. Een lage reguliere prijs (zoals AH cottage cheese €0,74) is niet automatisch een actie en verschijnt alleen als reguliere prijswaarneming in het persoonlijke prijsoverzicht. De filter Actie als hoofdingrediënt behandelt alle expliciet gekoppelde actierecepten, ook wanneer alleen de groenten in actie zijn; de begeleidende tekst licht dit toe.

## Bronverificatie (28 oktober 2026)

De controle in docs/data/verification.json registreert elf onderzochte winkels en prijsplatforms, 22 productcontroles en zes aanvullende AH-campagnes. De site toont bij de aanbieding wanneer twee bronnen overeenkomen, een bundel is omgerekend, of de bronnen elkaar tegenspreken. Na de controledag verdwijnt het recente controlelabel.

Let op: AH varkensgehakt 300g is €1,49 in de AH-folder/PrijsProfeet/MijnMandje en €1,50 in Allesupers. Jumbo boerenkool 300g kost los €1,99 en bij 1+1 twee gelijke pakken samen €1,99. Jumbo Zespri SunGold 750g voor €4,99 is €6,65/kg. Jumbo Dreft Platinum Plus Bries 25 capsules kost normaal €18,99 per pak: bij vijf identieke pakken en 2+3 gratis betaal je €37,98 voor 125 capsules (€0,304 per capsule). Andere Dreft-varianten hebben andere bundelbedragen. Referentieprijzen van pompoenen kunnen per soort verschillen.

Aanbiedingsprijzen uit aggregators zijn niet onafhankelijk gecontroleerde filiaalkassaprijzen. Checkjebon noemt in zijn README geen Lidl; Superscraper zegt Lidl-data via Checkjebon te gebruiken, wat onvoldoende onderbouwd is. Eenheidsprijzen van bepaalde Jumbo-productpagina's tonen de oude prijs ondanks de actie: bereken de actuele eenheidsprijs uit prijs en gewicht. Actie- en product-verificatie verlopen automatisch als een nieuwe datum begint, totdat de dagelijkse taak nieuwe controles schrijft.

## Receptkwaliteit en volledige aanbiedingimport (28 oktober 2026)
De oorspronkelijke 40 recepten hebben afzonderlijke brontitels maar geen gecontroleerde bronpagina's of proefgekookte bereidingen. Ze staan daarom als concepten gemarkeerd. Acht aanvullende wereldkeukenrecepten zijn originele, niet proefgekookte bewerkingen die op de algemene inspiratie van Voedingscentrum of Allerhande zijn gebaseerd; geen enkele bron heeft deze specifieke samenstelling getest. De 40 concepten zijn standaard verborgen via het kwaliteitsfilter, maar blijven beschikbaar. Ingrediëntcategorieën zijn gecorrigeerd en alle 48 zijn voor de groente-eis opnieuw getoetst. De app toont nu herkomst en kwaliteit per recept.

De Python-import sorteert niet meer op slechts vijf gezonde receptcategorieën; bier, huishouden, frisdrank, fruit, zuivel, voorraadproducten, snacks, brood/granen en overige productgroepen worden voortaan ook geïmporteerd. Actuele PrijsProfeet-dekking is niet synoniem aan volledige winkelvoorraad. De GitHub CI controleert syntaxis en categorisering inclusief bier; de nieuwe categorieën zijn pas volledig zichtbaar nadat de volgende importsynchronisatie slaagt. De app heeft categorieknoppen en een keuzelijst bij Alle aanbiedingen, met pagina's van maximaal 24 kaarten per winkel. Bier is een gebruikersinteresse en productfavoriet, geen automatisch receptingrediënt. Lidl wordt bij ontoereikende feed expliciet naar de officiële folder verwezen.

### Persoonlijke boodschappeninteresses en verificatie (28 oktober 2026)
Volle melk (vers 1 liter), Texels Skuumkoppe, soto-boemboe, kippenpoten/-bouten en sereh/citroengras zijn als actieve gebruikersinteresses toegevoegd in `watchlist.json`. Het gedeelte 'Voor mij' toont ook reguliere prijswaarnemingen, als acties ontbreken. Exacte favorietenhartjes slaan varianten alleen lokaal op in de browser; GitHub kan bestaande persoonlijke browserfavorieten niet stilzwijgend wijzigen. Filters bij Alle aanbiedingen: keten, productcategorie, zoektekst, sortering en broncontrole. Een officiële aanbieding met prijsconflict is niet 'officieel zonder prijsconflict'. Lidl zalm met huid is niet dezelfde variant als 'wilde zalm zonder huid'; de nieuwe ovenzalm gebruikt de juiste foldervariant, kost meer dan €10 voor 4 porties en claimt geen bevestigde kassaprijs door conflict €7,49 vs €7,99 bij Lidl. Skuumkoppe is per verpakking geprijsd met Jumbo prijsconflict bij 6x300ml.

## Strikte productidentiteit en extra Lidl-acties (28 oktober 2026)

`docs/product-matcher.js` is één gedeelde productmatcher voor alle recepten en alle drie winkels. Een exacte winkel-ID/EAN is de beste match. Zonder product-ID controleert hij herkenbare productfamilies, het verschil tussen huid/geen huid, wild/kweek, vers/diepvries, gerookt/niet-gerookt, bot/mager, dierlijk/plantaardig, alcoholvrij/alcoholhoudend, winkelmerk, melksoort en vleessoort. Een ontbrekend of afwijkend essentieel kenmerk geeft **mogelijk** of **niet dezelfde variant**, nooit een bevestigd actiebedrag. Een actiekorting in het recept telt alleen als de exacte verpakking(en) voldoende zijn en de prijs in de ingrediëntregels overeenkomt met de officiële, niet-tegenstrijdige prijs. Zonder betrouwbare identiteit geen automatische koppeling; overige vergelijkbare aanbiedingen verschijnen alleen als suggestie.

PrijsProfeet meldde 28 oktober 2026 geen Lidl-bieraanbiedingen. Andere bronnen (Biernet, AlleFolders, Lidl assortimentspagina) tonen wel producten. Daarom laadt de site `docs/data/supplemental-offers.json` naast `offers-catalog.json`. De eerste gecontroleerde externe aanbiedingen zijn Perlenbacher Strong 50cl voor €1,12 en Affligem Blond 0.0 6×30cl voor €3,99, geldig 26 oktober–1 november. De laatstgenoemde prijs is bij de vergelijkingsbron waarneembaar; de algemene Lidl-folder noemt vanaf €2,99 zonder hetzelfde zespack te bewijzen. Geen van beide prijzen is zelfstandig aan de Lidl-kassa bevestigd. `scripts/sync_lidl_supplemental.py` leest productdetailbronnen uit het uitbreidbare `docs/data/lidl-source-registry.json` en haalt prijs, periode en oorspronkelijke prijs **dagelijks opnieuw** op. De site toont brongegevens alleen bij een broncontrole met datum vandaag en als de aanbieding niet verlopen is. Een mislukte extra scan wordt als onvolledig gelabeld; prijzen worden niet stilzwijgend als vandaag bevestigd. De workflow voert de aanvullende Lidl-bronnen ook uit bij een PrijsProfeet-fout. Dit is een aanvullende bronreeks, geen claim dat het volledige Lidl-bierassortiment nu wordt afgedekt.

## Automatische controle van alle *ontvangen* aanbiedingen (28 oktober 2026)

De dagelijks geplande GitHub Action `Synchroniseer brede actiecatalogus` leest de PrijsProfeet-lijstfeed voor **Lidl, Jumbo en Albert Heijn** en de afzonderlijke, uitbreidbare Lidl-bronnen. Daarna voert `node scripts/offer-audit.cjs` een audit uit op iedere ontvangen aanbodregel. Het rapport `docs/data/offer-audit.json` bevat per supermarkt het aantal verwerkte aanbiedingen, bronherkomst, datum/geldigheid, ontbrekende of onduidelijke verpakking, bundelprijsvoorwaarden, prijsconflicten, bronovereenkomsten en aandachtspunten. De website toont dagtellers en een status bij elke kaart. Oude of ontbrekende audits mogen niet als controle van vandaag getoond worden.

**Twee niveaus mogen niet worden verward:** (1) de automatisch gevalideerde record (datums, verpakking, eenheden, bron, formule), (2) onafhankelijk bevestigde actuele productprijs en kassavoorwaarden. Niveau 1 geldt voor alle records die de integratie daadwerkelijk heeft ontvangen. Niveau 2 is slechts mogelijk wanneer een identieke productvariant met exacte verpakking en een recent onafhankelijk detailbedrag beschikbaar is. Meerdere websites kunnen dezelfde winkel- of folderbron kopiëren; twee gelijke bedragen zijn dus niet noodzakelijk onafhankelijk bewijs. Een winkel-URL betekent evenmin dat de prijs uit de productdetailpagina is uitgelezen of de kassa is geverifieerd.

De bronstatus `retailer_page_reported` betekent **retailer-URL in het aangeleverde record**, niet dat de daadwerkelijke pagina opnieuw per product is opgehaald. `external_feed_reported` is een externe prijsopgave; `needs_review` vereist aandacht. `cross_source_matching_records` toont strikte matching op EAN+verpakking of volledige naam+verpakking, nooit een garantiebewijs van winkelprijs. Problemen worden niet door 'verified=true' of door de scandatum opgelost. Verlopen aanbiedingen worden door de app niet als actueel getoond. De "bekende pakkosten" van een recept zijn expliciet geen volledige kassamand, en prijsverschillen met opgegeven oude productprijzen zijn niet automatisch besparingen ten opzichte van huismerken of andere verpakkingen.

**Beperking van de bronnen:** de gratis PrijsProfeet-endpoints bevatten promoties, niet de volledige reguliere schapprijzen. De API-voorwaarden (https://www.prijsprofeet.nl/api-voorwaarden) staan bulk-sync van lopende aanbiedingen toe, maar verbieden de volledige catalogus systematisch langs losse productdetail- of EAN-endpoints af te lopen. Voor de betaalde `/shelf-prices` en `/match/*` is afzonderlijke contracttoegang nodig. Checkjebon en andere vergelijkers hebben wisselende categorie- en winkeldekking; Lidl is bijzonder onvolledig. De workflow kan dus niet waarheidsgetrouw claimen **iedere werkelijk bestaande aanbieding bij iedere winkel** onafhankelijk te hebben bevestigd. De ontbrekende dekking wordt expliciet gemeld.

## Weergave-correcties 29 oktober 2026

- De pagina onderscheidt **actie op het hoofdingrediënt** van **een extra groente-/bijgerechtingrediënt in de aanbieding**. Een goedkope broccoli maakt dure zalm of kip niet automatisch een voordelige maaltijd.
- Bij een oudere receptvariant zoals wilde zalm zonder huid verschijnt een expliciete waarschuwing als de folder een andere variant (zalm op huid) aanbiedt. Het oude recept wordt niet herprijsd door de actie.
- De persoonlijke prijsvergelijking zegt niet meer dat een product niet in de aanbieding is als er enkel géén bronvermelding is gevonden; ontbrekende normale prijzen blijven onbekend.
- `docs/source-freshness.js` voorkomt dat duizenden nog steeds geldig verklaarde acties plots verdwijnen wanneer de externe scan één dag vertraagd is. Een aanbieding die gisteren voor een periode geldig werd gepubliceerd, mag nog één kalenderdag zichtbaar blijven **met 'prijs vandaag niet opnieuw gecontroleerd'**. Oudere scans, verlopen acties en falende bronstatussen worden uitgesloten. `tests/source-freshness.cjs` toetst deze grensgevallen automatisch.
- Aanbiedingsaantallen op de startpagina zijn aantallen **ontvangen actiemeldingen**, geen volledige winkeldekking en geen onafhankelijk geverifieerde kassaprijzen. De website toont enkel vandaag onderbouwde complete recepten wanneer elke prijs voldoet aan `docs/price-integrity.js`.
