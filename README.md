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
