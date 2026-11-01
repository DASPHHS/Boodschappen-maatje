# API- en brononderzoek — 1 november 2026

Doel: Nederlandse Lidl-, Jumbo- en AH-aanbiedingen duurzaam bijwerken, zonder een
onbekende verpakking, oude prijs of toekomstige actie als actuele kassaprijs te presenteren.
Alle onderstaande documentatie en relevante broncode zijn gelezen; een README-belofte
is afzonderlijk gehouden van een werkende live proef.

| Project / bron | Vastgesteld | Keuze |
| --- | --- | --- |
| [PrijsProfeet README](https://github.com/PrijsProfeet/supermarkt-api/blob/main/README.en.md), [OpenAPI](https://github.com/PrijsProfeet/supermarkt-api/blob/main/openapi.json), [dekking](https://www.prijsprofeet.nl/supermarkt-aanbiedingen-api/) | Publieke REST-aanbiedingen en wijzigingsfeed. Schapprijzen vereisen Pro/trial; de specificatie sluit Lidl-schapprijzen expliciet uit. Lidl heeft volgens de gepubliceerde meting geen EAN-dekking. | Bestaande aanbiedingenadapter uitgebreid met cursor-sync; geen betaald abonnement afgesloten. Geen fuzzy zoekresultaat als productidentiteit gebruiken. |
| [FriendlyUser/flipp_flyer_parser](https://github.com/FriendlyUser/flipp_flyer_parser) | Code richt zich op Canadese Save-On, Walmart, Superstore en Loblaws. Werkt met winkelcodes, folder/product-ID's, datums en browserinteractie; geen aangetoonde Nederlandse Lidl-bron. | Principes bron-/winkelidentiteit en foldergeldigheid bruikbaar. Geen Canadese prijsbron of browserpakket geïntegreerd. Ontbrekende inhoud blijft onbekend, niet standaard 1. |
| [Samvox1/nl-supermarkt-mcp](https://github.com/Samvox1/nl-supermarkt-mcp) | Prijzen komen uit Checkjebon, dus geen nieuwe onafhankelijke catalogus. Aanbiedingen komen uit Folderz. De parser vult een ontbrekende looptijd met 7 dagen aan en kan een oude prijs uit een percentage terugrekenen. | Onafhankelijke Folderz-adapter toegevoegd, maar met JSON-LD-detaildata en expliciete datums. Die aannames uit de originele parser niet overgenomen. |
| [bartmachielsen/SupermarktConnector](https://github.com/bartmachielsen/SupermarktConnector) | AH/Jumbo-connector; geen Lidl. Voorbeeld scheidt SKU, centbedragen, verpakking en eenheidsprijs. De Jumbo v17-search-route uit de code gaf in onze live proef HTTP 404. | Schema-/eenheidsprincipes bruikbaar. De verouderde route niet als werkende bron aangesloten. |
| [t0ffifee/discount-scraper](https://github.com/t0ffifee/discount-scraper) | Lidl-code leest `data-grid-data` uit HTML, met een oudere lijstvorm (`parsed_record[0]`). | Ondersteunt onze keuze voor gestructureerde openbare griddata. Onze huidige parser controleert daarnaast regio, datums, winkelverkoop en Lidl Plus. Dit lost de 503 vanuit GitHub niet op. |
| [tonsmets/SupermarketScraper](https://github.com/tonsmets/SupermarketScraper) | Laatste push volgens GitHub: 2015; README vinkt Lidl niet aan. Beschrijft bronmodules, cron, controles voor de run en logging van de scrape-run. | Die architectuurprincipes toegepast; geen oude scraper als actuele API gepresenteerd. |
| [GitHub topic grocery-api](https://github.com/topics/grocery-api) | Tijdens het onderzoek drie projecten voor Coles, Woolworths en Aldi; nadruk op Australische winkels. | Geen aangetoonde extra NL-bron. |

## Live proeven

- PrijsProfeet `/api/v1/products/changes?retailer=lidl`: geldige cursor-respons.
- Volledige Lidl-bootstrap via `/api/v1/products`: 85 actuele/aankomende catalogusrijen.
  Daarna één delta-aanvraag, zonder volledige herhaling; 37 rijen passeerden de
  bestaande filter voor lopende winkelacties. Dit is geen compleet Lidl-assortiment.
- Folderz Lidl-overzicht en 12 daar daadwerkelijk gelinkte detailpagina's bereikbaar;
  11 expliciet gedateerde meldingen geaccepteerd. Selectie beperkt tot één lijstpagina.
- Jumbo `mobileapi.jumbo.com/v17/search`: HTTP 404; niet aangesloten.

## Toegepaste principes

### Transacties en wijzigingen

`scripts/promotion_changefeed.py` vraagt eerst een startcursor, leest vervolgens alle
productpagina's en bewaart een snapshot per winkel. Bij volgende runs worden `upsert`
en `delete` in volgorde toegepast. Een verlopen cursor (410) start een nieuwe volledige
sync. Afgebroken pagina's, ongeldige winkel-ID's, dubbele bootstrap-ID's en een niet
voortschrijdende cursor stoppen de transactie zonder de oude cursor te wijzigen.
Aankomende producten blijven in de interne snapshot; de publieke app toont alleen de
rijen die de bestaande datum-/statuscontrole passeren.

De interne snapshot staat buiten de publieke website in een GitHub Actions-cache.
De cache wordt pas opgeslagen nadat de bijbehorende publieke feed succesvol is
gepubliceerd. Een cache-miss is veilig: de volgende run doet opnieuw een bootstrap.
De gepubliceerde productgegevens blijven hun oorspronkelijke `extracted_at` houden.
Zonder key blijft de client onder de gedocumenteerde 30 bulkrequests/minuut.

### Onafhankelijke aanvulling zonder prijsfantasie

`scripts/sync_folderz.py` gebruikt maximaal 12 detailpagina's, volgt alleen links uit
het Lidl-overzicht en vereist EUR, een expliciete Lidl-verkoper, dezelfde detail-URL en
expliciete begin- en einddatums. Geen relatieve "nog 2 dagen", gegokte oude prijs of
gewicht uit historische paginadelen. Ontbrekende verpakking wordt letterlijk als
onbevestigd opgeslagen; deze bron kan dan geen gewichtgebaseerde receptmand bewijzen.
Lidl Plus-voorwaarden worden niet als bekend verondersteld.

Folderz wordt als externe melding getoond, met bronlink en waarschuwing. De bestaande
onafhankelijke Lidl-, Biernet- en PrijsProfeet-bronnen blijven bestaan. Uitval van de
directe Lidl-bron blijft zichtbaar als `partial`. De import als geheel mag slagen als
een daadwerkelijk verse, gedateerde Folderz-aanvulling of een geslaagde actuele
PrijsProfeet API-import beschikbaar is; dit maakt de
directe Lidl-bron niet ineens groen. Als beide ontbreken, blijft de controle falen.

## Wat hiermee niet is opgelost

Er is geen gratis, volledige, gegarandeerd actuele Lidl-schapprijs-API aangetoond.
Een betaald PrijsProfeet-abonnement levert volgens de gelezen specificatie evenmin
Lidl-schapprijzen. Onbekende verpakkingsgewichten en onzekere productvarianten blijven
ontbrekende gegevens; zij worden niet door een schatting vervangen.


## Aanvullende controle vanuit GitHub Actions

De eerste product-bootstrap vanuit GitHub is geslaagd: 85 Lidl-, 2.938 Jumbo- en
5.836 AH-rijen, waarvan respectievelijk 37, 1.537 en 3.396 de filter voor lopende
winkelacties passeerden. De interne cursorcache is daadwerkelijk opgeslagen.

De rechtstreekse Lidl-pagina's gaven vanuit die runner HTTP 503. Folderz leverde
daar geen bruikbare detail-links, ondanks de geslaagde lokale proef met 11 meldingen.
Die adapter is dus geen bewezen betrouwbare automatische oplossing op GitHub.
De import bewaart de oorspronkelijke datums, toont bronuitval en blijft de werkende
API-feed gebruiken. Aanvullende bronuitval is een waarschuwing; als ook de API-import
geen actuele bron oplevert, blijft de beschikbaarheidscontrole falen. Paginatitels
worden bij ontbrekende links als beperkte diagnose bijgehouden, zonder blokkades te
omzeilen of een andere browseridentiteit aan te nemen.

## Aanvullende broncontrole — 1 november 2026

- De huidige echte broncode van **PrijsProfeet** is niet publiek (de repo is documentatie en OpenAPI). Het enige direct aanspreekbare gratis aanbod is de actuele promotiefeed, géén volledig winkelassortiment. Het gepubliceerde JSON-schema beschrijft `seq` voor wijzigingen als een oplopende positie, maar `cursor` uitdrukkelijk als **opaak**. Onze sync controleert nu de volgorde/identiteit van wijzigingen zonder rekenkundige aannames over de cursor en slaat een partiële update niet op.
- Voor een aanbieding met `valid_until_estimated` toont de website nu zichtbaar dat de einddatum geschat is. Ongeldige of niet-dalende referentieprijzen, onmogelijke ledenprijzen en niet-eindige bedragen worden niet als korting getoond. Een externe actie blijft een externe waarneming, geen winkelbevestiging.
- **PrijsProfeet API-voorwaarden art. 6–7:** het volledig synchroniseren van lopende aanbiedingen voor eigen applicatiegebruik mag, maar een opgehaalde reeks publiceren als downloadbaar bestand, in een publieke repository of als eigen feed/API is uitgesloten. De bestaande publicatie van `docs/data/offers-catalog.json` in GitHub Pages/repository vormt daarom een **nog openstaand hergebruik-/licentierisico**. De HTML bevat al een bronlink; dat neemt het afzonderlijke doorleveringsverbod niet weg. Bouw geen extra publieke ruwe feed zonder toestemming. Voor duurzame productie moet de architectuur verschuiven naar beperkte applicatiegerichte rendering via een toegestane backend of naar afzonderlijk gelicentieerde data. Eerdere publieke Git-commits vergen daarbij aparte aandacht. Dit is niet opgelost door alleen een andere bestandsnaam, selectie of CORS-truc.
- De `grocery-api` GitHub-topiclijst bestaat per 1 november uit vijf voornamelijk internationale scraperprojecten (Coles, Woolworths, Aldi Australië, Harris Farm en Tesco/UK/Walmart). Geen daarvan levert een actuele, specifiek voor Nederlandse Lidl/Jumbo/AH aangetoonde prijscatalogus.
- **Geen extra scraper aangeschakeld:** het oude Jumbo v17-endpoint van SupermarktConnector, de Canadese Flipp-retailercodes en de historische SupermarketScraper van 2015 zijn geen bewezen werkende Nederlandse bron. TheMealDB uit nl-supermarkt-mcp levert bovendien geen zelfstandige zekerheid over Nederlandse ingrediënten, toestemming voor herpublicatie of kassaprijzen.

Voorwaarden: https://www.prijsprofeet.nl/api-voorwaarden (secties 6–7); API-schema: https://github.com/PrijsProfeet/supermarkt-api/blob/main/openapi.json; GitHub topic: https://github.com/topics/grocery-api.
