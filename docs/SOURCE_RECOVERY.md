# Werkende bronroutes en resterende toegang

Onderzoek en liveproeven van 3 november 2026. Dit document beschrijft concrete brondekking; het claimt geen compleet assortiment of filiaalvoorraad.

## Geraadpleegd

- [KortingKlok](https://github.com/RashadAnsari/KortingKlok), inclusief de Jumbo-, AH- en Lidl-adapters en de MIT-licentie. Bruikbare principes: een adapter per winkel, exacte artikelcodes, gestructureerde paginadata en meetmomenten. De repository is gearchiveerd; de huidige publieke winkelpagina's zijn daarom afzonderlijk getest.
- [SupermarktConnector](https://github.com/bartmachielsen/SupermarktConnector): voorbeeld van artikeldetails en barcodezoeken. Een oude endpointnaam is geen bewijs dat een route vandaag zonder aanvullende toegang werkt.
- [PrijsProfeet API-documentatie](https://github.com/PrijsProfeet/supermarkt-api/blob/main/README.md): gratis promoties en betaalde schapprijzen zijn verschillende datasets. Actie-, toekomstige, historische en gewone prijzen moeten onderscheiden blijven.
- [Reddit-discussie over Lijssie](https://www.reddit.com/r/Netherlands/comments/1jmlgjw/i_built_a_free_app_where_you_can_compare/): praktijkervaringen, eenheidsprijzen, verplichte aantallen en verwijzing naar Checkjebon. Gebruikt als onderzoeksingang; de technische implementatie is gebaseerd op primaire broncode en live winkeldata.

## Doorgevoerd

De metadata-adapter leest nu Jumbo's openbare Nuxt-productobject op exacte SKU en canonieke URL. AH-productcategorieën kunnen uit het afgebakende kruimelpad worden aangevuld, nadat de JSON-LD-artikelcode is gecontroleerd. Een inhoud die expliciet in de officiële producttitel staat kan een ontbrekende ondertitel aanvullen; onbekende gewichten worden niet geschat. Liter en gram voluit worden herkend.

Een nieuwe controle vergelijkt geïmporteerde Jumbo-acties met de productprijs, actiedata, verpakking en voorwaarden van de winkel. Ondersteund zijn eenduidige vaste prijzen, percentages met expliciete productprijs, aantallen voor een totaalbedrag en koop-plus-gratisacties. Een bezorgbeloning is geen korting op het product. Een omgerekende bundelprijs is geen prijs voor één los product. De verplichte afname en het totaal worden bewaard en zichtbaar getoond.

Bewijs wordt blijvend opgeslagen, hergebruikt na een nieuwe import en ongeldig bij gewijzigde product-, prijs-, datum- of actievoorwaarden. De bronverificatie heeft een verzoek- en tijdslimiet, verdeelt werk over volgende runs en stopt bij toegangs- of snelheidsweigering.

De productmonitor haalt ontbrekende gegevens nu actief op, zes keer per dag. Hij publiceert opgehaalde informatie en verrijkte catalogus samen. Gelijklopende prijsjobs voegen informatie op controledatum samen, zodat een latere publicatie geen nieuwer winkelbewijs terugdraait.

In de eerste twee metadata-runs steeg het aantal productrecords met gecontroleerde winkelidentiteit van 122 naar 168. Dat is niet hetzelfde als 168 bevestigde actuele aanbiedingen. Live actieproeven en de volledige testsets worden afzonderlijk gecontroleerd.

## Wat niet door broncode alleen oplosbaar is

De geteste Jumbo GraphQL-route gaf zonder extra toegang HTTP 401. De publieke productpagina's werkten wel. De volledige PrijsProfeet-schapprijsroute vereist volgens de aanbieder een betaald account met API-sleutel; die toegang is niet beschikbaar gemaakt voor dit project. De bestaande openbare catalogus blijft een aanvullende prijsbron. Een live workflow liep tegen de gedeelde GitHub-limiet voor anonieme API-aanvragen aan; de catalogusimport gebruikt daarvoor nu de eigen GitHub Actions-token, uitsluitend op api.github.com. Dit vraagt geen nieuw persoonlijk account of token van de gebruiker.

Een ontbrekend assortimentartikel, een winkelafhankelijke voorraad en een niet-gespecificeerde productvoorkeur zijn verschillende problemen. Geen van de onderzochte projecten biedt bewijs dat werkelijk elk product, elke filiaalprijs en elke actievoorwaarde altijd compleet beschikbaar is. Het onderzoek rechtvaardigt daarom meer automatische bronophaling en betere dekking, geen garantie van nul ontbrekende gegevens.

## Controle van de zomerstamppot

De kaart voor Allerhandes zomerstamppot met prei en masala-tofu werd op 3 november gekoppeld aan Jumbo's stevige tofu (2 × 280 g voor €2,19) en kruimige aardappelen (2 × 600 g voor €1,39). Dit zijn twee verschillende passende actieproducten, inclusief de vegetarische eiwitbasis. De bedragen dekken de benodigde tofu en aardappelen voor vier porties; niet de overige ingrediënten.

De productparser miste het meervoud “preien”. Die is hersteld en veertien betrokken Allerhande-recepten zijn opnieuw bij de uitgever gecontroleerd. Een kaart vermeldt nu waarom zij bij een winkel is gekozen. Een seizoen in de oorspronkelijke titel wordt onderscheiden van de selectie op acties; de titel van de maker wordt behouden. Een bronmelding voor prei zonder voldoende verpakkingsbewijs is geen bewezen hoeveelheidsprijs.

Bij het vervolgonderzoek zijn ook expliciete stuksaantallen en “gr” als gram verwerkt. Maximale actieaantallen uit de winkelbron worden bewaard; een berekening voor meer verpakkingen dan die grens geeft geen bevestigd actietotaal.
