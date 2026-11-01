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
een daadwerkelijk verse, gedateerde Folderz-aanvulling beschikbaar is; dit maakt de
directe Lidl-bron niet ineens groen. Als beide ontbreken, blijft de controle falen.

## Wat hiermee niet is opgelost

Er is geen gratis, volledige, gegarandeerd actuele Lidl-schapprijs-API aangetoond.
Een betaald PrijsProfeet-abonnement levert volgens de gelezen specificatie evenmin
Lidl-schapprijzen. Onbekende verpakkingsgewichten en onzekere productvarianten blijven
ontbrekende gegevens; zij worden niet door een schatting vervangen.
