# Duurzame receptenvoorziening — Allerhande en HelloFresh

**Status 1 november 2026.** Boodschappenmaatje gebruikt twee gescheiden lagen:
(1) een uitbreidbare index met echte links naar recepten van uitgevers;
(2) eigen, volledig uitgewerkte recepten die in de app zelf geopend en gepland kunnen worden.

## Waarom deze architectuur?

Allerhande geeft aan zijn recepten culinair te testen. HelloFresh publiceert een omvangrijke Nederlandstalige receptencatalogus. Beide leveren sterkere inspiratie en kooktechniek dan het steeds handmatig verzinnen van nieuwe titelkaarten.

De uitwerking, volledige ingrediëntenlijsten, foto's, allergenen en voedingswaarden van deze uitgevers blijven op hun **eigen websites**. Een GitHub-crawler of publiek leesbare JSON van derden geeft geen licentie om de hele receptenbank te herpubliceren. Pas met gedocumenteerde toestemming/licentie kunnen we de volledige externe stappen en hoeveelheden in Boodschappenmaatje zelf tonen en bij boodschappen optellen.

## Dagelijkse ervaring

- De eerste sectie van **Recepten** toont standaard acht uitgeverskaarten en biedt **Toon acht extra recepten**, verdeeld tussen **Allerhande** en **HelloFresh**, en gekoppeld aan passende actuele productsoorten. Er staat duidelijk wanneer de selectie niet op een bevestigde aanbieding berust.
- Daaronder komen drie zorgvuldig uitgewerkte **tweedaagse gerechten** voor twee personen, met hachee als vaste klassieke keuze. De lange verzameling overige zelfgemaakte actie-ideeën is bereikbaar via een aparte knop, maar verdringt echte uitgeversrecepten niet meer.
- Zoeken op **riblappen** toont echte uitgeversrecepten zoals hachee en rendang met bronlink; de app bewaart geen onjuiste claims dat snel bereide voorgesneden/voorgegaarde producten uitwisselbaar zijn met rauwe riblappen.
- Het filter **Kook voor 2 dagen** toont uitsluitend volledige eigen recepten met `batch_cook.days=2`, `people_per_day=2` en `total_portions=4`. Een willekeurig twee- of vierpersoonsrecept van een uitgever is **niet automatisch** geschikt voor twee dagen.

## Automatische bronindex

| Bron | Ontdekking | Status en foutafhandeling |
| --- | --- | --- |
| Allerhande | `scripts/refresh_publisher_recipes.py` leest de officiële recepten-sitemap, bezoekt beperkt een aantal publieke receptpagina's en selecteert feitelijke titel-/ingrediëntfamilie-metadata | Bestaande 102 bronverwijzingen als uitgangspunt, inclusief oudere bronnen; titel-only sitemaprecords worden niet als volledig gecontroleerde recepten gepresenteerd |
| HelloFresh NL | `scripts/refresh_hellofresh_recipes.py` leest alleen publieke categoriepagina's en hoogstens 12 nieuwe individuele pagina's per week | Exacte HTTPS-hostcheck, robots.txt, wachttijd tussen requests, directe stop op 401/403/429, geen mutatie bij netwerk-/robotsfout |
| Allebei | `.github/workflows/recipe-discovery.yml` iedere woensdag | Commit alleen relevante nieuwe bronmetadata, met statische tests vooraf |

De HelloFresh-index start met zes direct gecontroleerde Nederlandse receptpagina's. Nieuwe recepten worden **alleen** toegevoegd als de individuele originele pagina bereikbaar is. Een bron die niet toegankelijk is, blokkeert de bestaande collectie niet; er worden geen zoekresultaten omgezet in fictieve recepten.

### Toegestane opslag

`docs/data/publisher-recipes.json` bevat alleen: titel, canonieke URL, bron, indicatieve ingrediëntfamilies, eventuele tijd, kooktype, beperkte bronstatus en controledatum. Geen foto's, stappen, ingrediëntenlijsten of gekopieerde receptomschrijvingen.

`publisher_page_title_verified` betekent: individuele uitgeverspagina toegankelijk, titel gecontroleerd, families afgeleid uit korte publieke titelinformatie. **Het betekent niet dat voedingswaarde, verpakkingshoeveelheden of een volledig hoofdgerecht op voedselveiligheid zijn gecontroleerd.**

Een match met een supermarktactie is altijd een **ingrediëntsoort-match**, totdat ook de exacte productvariant en de geldende prijs op winkel- en verpakkingsniveau bewezen zijn. Een externe receptenkaart heeft daarom geen berekende boodschappenlijst of prijs.

### Regressies

- `python -m unittest discover -s tests -p 'test_hellofresh_recipes.py' -v` controleert hostallowlist, robots, paginabereikbaarheid, dubbele links, mislukte synchronisatie en het niet opslaan van receptenstappen.
- `node tests/publisher-recipe-index.cjs` controleert echte bronhosts en niet-gekopieerde metadata.
- `node tests/browser-journey.cjs` controleert of beide uitgevers zichtbaar zijn, het tweedaagse hacheerecept geopend kan worden en de vier porties niet dubbel worden ingekocht.

## Belangrijke verdere mogelijkheid

Wil je bij álle Allerhande- en HelloFresh-recepten de complete ingrediënten, stappen, hoeveelheden voor twee dagen en automatisch berekende winkelmandjes *binnen* de app? Dan is een expliciete data-/hergebruiklicentie nodig of moeten de gebruiker en uitgever een toegestane persoonlijke importworkflow ondersteunen. Dit is bewust niet geclaimd als al gereed.

## Kwaliteits- en interfacecontrole (1 november 2026)

De standaardvolgorde is nu: **(1) echte Allerhande/HelloFresh-recepten**, (2) **volledige gerechten voor twee dagen, inclusief hachee**, (3) overige eigen recepten na een expliciete klik. De selectie gebruikt `docs/publisher-selection.js` voor afwisseling naar uitgever en kookfamilie, het filteren op zoektekst en alleen passende productsoorten uit actuele supermarktacties. Een uitgeversrecept kan géén exact berekende kassaprijs tonen, tenzij de volledige ingrediënten en het relevante verkooppakket onafhankelijk en rechtmatig beschikbaar zijn.

Vier afzonderlijke originele Allerhande-hacheerecepten zijn als gecontroleerde bronlinks opgenomen; `hachee` wordt hiermee direct door de uitgeverszoekfunctie herkend. De pagina toont niet langer tientallen vermoedelijke weekactierecepten voordat je bij klassiekers komt. De wekelijkse bronindex blijft dezelfde en groeit onafhankelijk van de manier waarop de kaarten worden gepresenteerd.

## HelloFresh.nl/recipes als primaire bron (1 november 2026)

De standaard receptenervaring selecteert **alleen actuele, individueel gecontroleerde HelloFresh.nl-receptpagina's** die rechtstreeks via `https://www.hellofresh.nl/recipes` en de openbare categorieën bereikbaar zijn. De knop `Allerhande` is optioneel. `Beide bronnen` toont expliciet de gemengde selectie; de standaardweergave wisselt niet stilzwijgend tussen uitgevers.

De zelfstandige adapter `scripts/refresh_hellofresh_recipes.py` begint bij de **echte HelloFresh-receptenhub**, volgt uitsluitend de gevonden eigen recept-URL's, kent voorrang toe aan volledige avondmaaltijden (o.a. stoof, curry, lasagne, dahl, vis en rijstgerechten) boven hamburgersnacks en verhoogt de wekelijkse beperkte controle van 12 naar maximaal 36 individuele pagina's. De veiligheidsgrens is maximaal 350 geïndexeerde HelloFresh-links. Een bron wordt niet toegevoegd als de individuele pagina niet bereikbaar is of de titel onvoldoende identificeerbaar is. Robots.txt, bronweigeringen, limieten en rechten blijven leidend.

`docs/publisher-selection.js` kiest per oproep alleen de gevraagde uitgever. `tests/publisher-first-selection.cjs` en de echte Chromium-browsertest verifiëren dat de opening uitsluitend rechtstreekse HelloFresh.nl/recipes-links toont en dat Allerhande alleen via de expliciete bronkeuze verschijnt.

HelloFresh is de receptenbron, niet de bron van de supermarktprijs: koppelingen met Lidl, Jumbo en Albert Heijn blijven aparte, conservatieve productsoortmatches. Volledige externe receptteksten, foto's en uitgeversspecifieke boodschappenlijsten worden zonder gebruiksrecht niet hergepubliceerd.
