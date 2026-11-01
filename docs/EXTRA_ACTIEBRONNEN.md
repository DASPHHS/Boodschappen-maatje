# Aanvullende actiebronnen — onderzoek 1 november 2026

Dit document vult `docs/API_RESEARCH.md` aan. **'Pagina gevonden' betekent niet 'betrouwbare productimport operationeel'.** De applicatie behandelt folderperiodes, acties en reguliere schapprijzen als drie verschillende gegevenssoorten.

| Bron | Verificatie 1-11-2026 | Bruikbare integratie | Beslissing |
| --- | --- | --- | --- |
| [PrijsProfeet promoties](https://www.prijsprofeet.nl/api/v1/products/promotional/all) | API-/OpenAPI-route gepubliceerd; bestaande Python-adapter en GitHub-workflow reeds aanwezig | Huidige promoties per retailer, met herleidbare prijs en geldigheidsperiode | **Bestaand.** Geen tweede adapter maken. Controleer per run of data actueel zijn. |
| [PrijsProfeet wijzigingen](https://github.com/PrijsProfeet/supermarkt-api/blob/main/openapi.json) | Changefeed gedocumenteerd; lokale `scripts/promotion_changefeed.py` gebruikt cursor en 410-herbootstrap | Efficiënte upsert/delete per keten | **Bestaand.** Cursor pas na volledige publicatie bewaren. |
| [Folderwijzer API](https://folderwijzer.nl/folder-api/) | Gepubliceerde read-only endpoints voor folders, geldigheid, deeplinks en RSS/JSON/ICS; alleen voor alcohol productlabels | Controleren welke folder per keten loopt, eventueel folderlink en nieuwe-folder-signaal | **Geschikt voor folderstatus, niet voor algemene boodschappenprijzen.** Niet als productfeed opnemen. |
| [Folderz](https://www.folderz.nl/) | Bestaande beperkte Lidl-detailadapter; eerdere GitHub-run leverde geen bruikbare detail-links | Onafhankelijke melding alleen bij expliciete prijs, keten, productlink en datums | **Bestaand maar niet bewezen robuust.** Uitval zichtbaar houden; geen fictieve korting. |
| [AlleFolders](https://www.allefolders.nl/) | Folderwebsite; geen gecontroleerd publiek product-API-contract | Eventueel aanvullende foldernavigatie | Geen automatische productimport zonder rechten en test. |
| [Action weekactie](https://www.action.com/nl-nl/weekactie/) | Actuele weekactiepagina toegankelijk; categorie- en productvermeldingen in de publieke HTML | Afzonderlijke non-food/huishouddealcatalogus met weekvaliditeit | **Niet mengen met maaltijdprijzen.** Product- en regiobeschikbaarheid apart markeren. |
| [Zeeman weekaanbiedingen](https://www.zeeman.com/nl-nl/weekaanbiedingen) | Webcontrole gaf 403; bron-URL alleen bekend | Eventueel winkels/online modescheiding | Geen werkende adapter claimen. |
| [Xenos folder](https://www.xenos.nl/folder) | Folderpagina publiek toegankelijk; niet bewezen dat alle prijzen machineleesbaar zijn | Externe folderlink | Geen productprijs uit PDF/folderafbeelding raden. |
| [Praxis folder](https://www.praxis.nl/acties/folder) | Bron-URL bekend; niet als productfeed getest | Afzonderlijke bouwmarktdeal-bron | Niet mengen met Lidl/Jumbo/AH. |
| [Intratuin folder](https://www.intratuin.nl/folderoverzicht) | Bron-URL bekend; niet als productfeed getest | Afzonderlijke tuin-/seizoensdeals | Laat voorraad en looptijd onbeslist zonder productbewijs. |
| [Kruidvat](https://www.kruidvat.nl/) | Startpagina alleen, geen specifieke gespecificeerde productfeed | Drogisterijdeals na aparte rechten-/feedtest | Eerst gedateerde productbron aantonen. |
| [Picnic onofficiële API](https://github.com/MRVDH/picnic-api) | Accountgebonden bibliotheek genoemd; niet gekoppeld | Alleen met expliciete opt-in en toegestane toegang | Geen account, token of persoonlijke prijs in publieke GitHub-data. |
| [Bol](https://www.bol.com/nl/nl/) | Webshop, geen algemene aanbiedingsfeed in deze inventarisatie | Afzonderlijke webshopsvergelijking met leverings-/verzendingskosten | Geen retailerdata uit listing- of zoekresultaat als volwaardige productfeed behandelen. |

## Direct bruikbare Folderwijzer-routes

De gepubliceerde documentatie noemt:
- `GET https://folderwijzer.nl/api/v1/folders.json`: actuele folderindex
- `GET https://folderwijzer.nl/api/v1/folders/albert-heijn.json`: ketenfolders en beschikbare labels
- `GET https://folderwijzer.nl/api/v1/feeds/albert-heijn.json`: nieuwe-folder-feed
- `GET https://folderwijzer.nl/api/v1/ical/albert-heijn.ics`: folderperiodes voor agenda

**Beperking volgens de bron:** voor niet-alcoholcategorieën levert Folderwijzer *folderniveau en deeplink*, geen volledige productlijst met berekende actieprijzen. Het veld `price` kan letterlijk tekst als '25% korting' zijn. Het mag dus niet rechtstreeks naar `offer.price` worden gemapt.

## Kritische rechtenkwestie bij PrijsProfeet

De actuele [API-voorwaarden](https://www.prijsprofeet.nl/api-voorwaarden) staan periodieke synchronisatie van lopende acties voor een eigen applicatie toe, maar verbieden ruwe doorlevering als eigen feed/API of reconstructie van de achterliggende database. De bestaande publicatie van uitgebreide `docs/data/offers-catalog.json` in een publieke GitHub-repository en GitHub Pages is daarom **een open risico dat niet met alleen bronvermelding is opgelost**. Zie ook `docs/API_RESEARCH.md`.

**Vervolg dat voor productie nodig is:** verifieer hergebruikcontract/expliciete toestemming en verplaats ruwe sync-staat zo nodig naar een private backend met minimaal noodzakelijke applicatierespons. Controleer daarbij ook het bestaande Git-verleden en de direct toegankelijke JSON-bestanden. Deze wijziging voegt **geen nieuwe openbare PrijsProfeet-export** toe.

## Publicatievoorwaarden voor nieuwe winkelbronnen

1. Zet elke bron eerst op `discovered`; ga pas naar `working` na een reproduceerbare run vanuit de echte GitHub Actions-omgeving.
2. Bewaar bron, unieke identiteit, prijs, valuta, productvariant, verpakking, winkel, `observed_at` en expliciete geldigheidsdatums.
3. Gebruik per bron een adapter; geen aangepaste prijs of kortingspercentage bedenken bij ontbrekende waarden.
4. Houd verlopen, toekomstige, onzekere en locatieafhankelijke aanbiedingen apart van actueel bevestigde winkelacties.
5. Laat uitval van een extra bron nooit ten koste gaan van bestaande bruikbare brondata, maar toon waarschuwingsstatus.
6. Gebruik non-foodbronnen voor **aparte winkelcategorieën**, niet als onzichtbare bijmenging in receptsuggesties.
7. Publiceer uitsluitend data met passend gebruiksrecht; geen ruwe accountgegevens in een publieke repository.

Praktisch eerstvolgende productverbetering: het rechtenrisico van de bestaande PrijsProfeet-JSON oplossen en daarna de folderstatus van Folderwijzer als **aparte provenance-/dekkingcontrole** toevoegen, niet als een fictieve aanvullende prijsbron.
