# Productprijzen en automatisch uitgekozen kookrecepten

Onderzocht op 1 november 2026.

## Checkjebon (https://github.com/supermarkt/checkjebon)

De bron is **al aangesloten** sinds eerdere versies: `scripts/sync_retailer_catalog.py` importeert de openbare `data/supermarkets.json` op een specifieke commit en controleert bronleeftijd, recordaantal, product-URL, verpakking, prijs en bron-identiteit. `docs/catalog-search.js` houdt AH/Jumbo/Lidl-verpakkingsregels bij, `docs/recipe-shop-options.js` berekent het aantal hele verpakkingen en toont onvolledige dekkingscijfers.

Checkjebon en de bijbehorende `supermarkt/checkjebon-js` zijn **MIT-gelicentieerd** en ondersteunen hergebruik van broncode mits copyright- en licentienotities behouden blijven. De Checkjebon-dataset is openbaar te hergebruiken. De huidige kopie van onze geoptimaliseerde, genormaliseerde productprijsfeed is gebaseerd op die bron. Checkjebon vermeldt expliciet **geen volledige online Lidl-assortimentsbron**. Daarom blijven Lidl-prijswaarnemingen afzonderlijk en conservatief, nooit automatisch gelijk aan AH/Jumbo.

De checkjebon-js-bibliotheek kiest als algemene fallback soms een *fuzzy best match* en schat een ontbrekende prijs via een gemiddelde van andere supermarkten. Dat gedrag nemen we **niet** over: het kan een biologische, houdbare, lactosevrije, gladde of crunchy variant verwisselen. Onze code bevat inmiddels geschiktheidsgates, productvariantclassificaties, werkelijke verpakkingsinhoud en onbekend/oud-status. Deze mechanismen zijn nauwkeuriger voor de gebruiker dan het klakkeloos kopiëren van de upstream winkelwagenplanner.

Bronnen: https://github.com/supermarkt/checkjebon/blob/main/README.md en https://github.com/supermarkt/checkjebon-js/blob/main/checkjebon.js. Licentie: https://github.com/supermarkt/checkjebon-js/blob/main/LICENSE.txt (Copyright (c) 2022 supermarkt).

## Directe recepten in plaats van zoekmachinezoekacties

De publicatie `docs/data/publisher-recipes.json` bevat eerst ruim dertig **door ons geselecteerde originele recepten** van Allerhande en Jumbo met directe URL, titel, relevante ingrediëntfamilies en, waar bekend, minuten en porties. De app sorteert per actieproduct op:

- bewezen culinaire ingrediëntfamilie, inclusief bereidingstijd van langzaam gaar te maken vleessoorten;
- hoofdgerecht, vier porties, passende bereidingswijze, groenten en peulvruchten;
- variatie in productfamilies en gerechten zodat een winkel niet twaalf keer dezelfde curry krijgt;
- herkomst bij de oorspronkelijke uitgever; geen overname van auteursrechtelijk beschermd bereidingsverhaal, foto's of andere lange tekst.

Automatische aanvulling is geïntroduceerd in `scripts/refresh_publisher_recipes.py` en `.github/workflows/recipe-discovery.yml`. We volgen het **sitemap-principe** van https://github.com/nwesthoff/allerhande-recipe (oud voorbeeld), en verifiëren een beperkt aantal originele receptpagina's per week via Recipe-JSON-LD. Alleen feitelijke link-/titel-/categorie-/tijd-/ingrediëntfamilie-metadata wordt bewaard. Recepten zonder geschikte groente of peulvrucht, met baby's/verspakketten of onbruikbare bron gaan niet automatisch de index in. **AH geeft bij automatische verzoeken om receptpagina's HTTP 403:** dan is een pagina niet inhoudelijk geverifieerd. De officiële sitemap kan wel een aanvullende directe receptlink leveren, uitsluitend als de titel duidelijk op meerdere ingrediënten en een gerecht wijst. Zulke suggesties krijgen verplicht de lagere status `publisher_sitemap_title_only`, zonder verzonnen bereidingsminuten, porties of gezondheidsclaims, en staan na de inhoudelijk gecontroleerde receptverwijzingen. Een mislukte sitemapimport bewaart de bestaande index.

### Andere projecten

- https://github.com/moshetrenk/hellofresh-database: goede inspiratie voor ingrediëntenindex, tags, porties, allergenen en filters. De gepubliceerde REST API is alleen voor geregistreerde gebruikers en de HelloFresh-productiecontent heeft eigen rechten; die database is geen vrij te kopiëren receptendump.
- https://github.com/PaulVerhoeven1/grocy-dutch-supermarket: EAN-/barcodepricipe via oude SupermarktConnector. Verbindingslogica en endpoints zijn niet bewezen actueel; niet gebruikt voor receptkwaliteit.
- https://github.com/peternijssen/python-jumbo-api: in 2023 gearchiveerde API-client voor bestellingen en winkelwagen; geen actuele vrij toegankelijke recepten-API.
- https://bitmash.nl/portfolio/mealpreprecepten: commerciële productbeschrijving van headless CMS, maaltijdtags en API-productmatching. Geen gepubliceerde open receptenbron of automatisch herbruikbare receptlicentie.
- https://github.com/basetenlabs/ml-cookbook: machine-learningtrainingsrecepten, géén kookreceptendatabase. Niet relevant voor de consumentenfunctie.

Er wordt **geen** publicatie gedaan alsof een automatisch gesuggereerd gerecht proefgekookt, nutritioneel gevalideerd of volledig aan de kassa geprijsd is. Het bronrecept open je rechtstreeks; de app zoekt de geschikte opties voor je.
