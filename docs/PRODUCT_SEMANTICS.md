# Productvergelijking en doorlopende broncontrole

De zoekindex haalt kandidaten op. Een woordmatch geeft nooit toestemming om een
product als vergelijkbaar of goedkoop te presenteren. `product-semantics.js`
controleert onafhankelijk doelgroep, productfamilie, bereidingsvorm en meetbasis.
`product-resolver.js` past daarna de expliciete variant- en verpakkingseisen toe.
Dezelfde modules draaien in de browser, receptenberekening en dagelijkse audit.

## Vergelijkingsregels

- Menselijke basisvoeding, dierenvoeding, babyvoeding en huishoudartikelen zijn
  afzonderlijke domeinen. Een overeenkomende ingrediëntnaam overbrugt die grens niet.
- Bereide gerechten, gerookt broodbeleg, gemarineerd vlees en poeder zijn geen
  vervangers voor onbewerkte ingrediënten. Samengestelde woorden tellen mee.
- Onbekende beschrijvingen krijgen `partial` en geen plaats als goedkoopste keuze.
  Nieuwe, letterlijk benoemde producten kunnen ook zonder vaste productlijst
  worden verwerkt; afwijkende beschrijvingen vereisen aanvullende broninformatie.
- De vergelijking krijgt aparte rijen per familie, vorm, relevante variant en
  meeteenheid. Vissoorten en alcoholvarianten worden dus niet door prijs gesorteerd
  tot schijnbaar gelijkwaardige alternatieven. Liter wordt nooit als kilo behandeld.
- Een onbekend verpakkingsgewicht blijft onbekend. Prijs per verpakking is geen
  bewijs van prijs per kilo of van de goedkoopste volledige boodschappenmand.

Dit is een conservatief classificatiesysteem, geen garantie dat iedere nieuwe
productnaam automatisch kan worden begrepen. Foutieve goedkope treffers wegen
zwaarder dan een lege cel met onvoldoende bewijs.

## Automatische actualisatie

De winkelcatalogus wordt tweemaal dagelijks opgehaald. Broninhoud en datum komen
uit dezelfde vastgepinde Checkjebon-commit, zodat een parallelle bronupdate geen
oude inhoud een nieuwe datum kan geven. Een verouderde, incomplete of onverwacht
veel kleinere import overschrijft de bewaarde catalogus niet. `source-health.json`
krijgt een foutstatus en de workflow faalt zichtbaar na publicatie van de waarschuwing.
Een catalogusdatum is een snapshotdatum, geen bevestiging dat elk individueel
schapprijskaartje die dag is gecontroleerd.

Bij elke import/publicatie wordt `semantic-review.json` opnieuw opgebouwd uit
alle huidige gevolgde productgroepen en winkelkandidaten. Het rapport bevat
beleidsversie, uitsluitingsredenen, vergelijkingsgroepen en een controlewachtrij.
De aparte productmonitor herhaalt deze controle dagelijks; vertraagde GitHub-runs
worden niet op een exact uitvoeringsuur weggefilterd.

`sync_product_evidence.py` verwerkt maximaal 24 officiële productpagina's per run,
verdeeld over winkels en met voorrang voor nog niet/het langst niet gecontroleerde
producten. Zowel onzekere kandidaten als passende producten komen daarvoor in
aanmerking. Een HTTP 403 of 429 stopt die winkel in die run, zonder omzeiling.
Mislukte metadata-aanvragen krijgen drie dagen wachttijd.

Er wordt alleen JSON-LD Product-informatie gebruikt met een bevestigd eigen
artikelnummer/product-URL en categorie. Een hash van bronproductnaam en verpakking
maakt eerder bewijs ongeldig zodra die gegevens veranderen. Categorie-informatie
mag maximaal veertien dagen oud zijn. Een expliciete EUR-prijs uit een bevestigde
productpagina mag op de controledag of de volgende kalenderdag de snapshotprijs
vervangen; daarna valt de prijs terug op de gedateerde cataloguswaarneming. Dat is
nog steeds geen onafhankelijke kassagarantie. Recepten en vergelijking gebruiken
hiervoor dezelfde `catalog-search.observation`-functie.

Niet iedere winkel publiceert bruikbare gestructureerde metadata. Een mislukte of
onduidelijke bron blijft daarom onduidelijk; er wordt geen categorie of prijs
verzonnen om een lege cel te vullen. Bronwijzigingen kunnen onderhoud blijven vragen.

## Verificatie en uitbreiden

`tests/product-semantics.cjs` bevat de gemelde fouten én gegenereerde varianten van
doelgroep- en bereidingsconflicten, onbekende productnamen en eenheidsfouten.
`tests/test_product_evidence.py` bewaakt artikelidentiteit, categorieën en hashwijzigingen.
`tests/test_retailer_catalog.py` controleert dat een bronfout oude bytes bewaart én
als fout wordt gerapporteerd. De Chromium-test controleert de daadwerkelijke
vergelijking op verkeerde productklassen, plus navigatie en opslag op desktop/mobiel.

Voeg herbruikbare families/vormkenmerken toe aan het gedeelde beleid, met positieve
én negatieve voorbeelden. Voeg geen winkel-SKU-uitzondering toe om één screenshot
te repareren. Verhoog de beleids-/scriptversie bij wijzigingen.

## Onderzochte voorbeelden

- [Checkjebon](https://github.com/supermarkt/checkjebon): openbare prijsdata en
  expliciete beschrijving van de beperkingen van generieke/fuzzy productselectie.
  De hier gebruikte toelatingscontrole kopieert die fuzzy selectie niet.
- [Open Food Facts dataformaat](https://github.com/openfoodfacts/data-imports/blob/master/docs/data-formats.md):
  productidentificatie, categorieën en verpakking als afzonderlijke gegevens.
- [Open Food Facts gestructureerd zoeken](https://openfoodfacts.github.io/documentation/docs/Product-Opener/v2/search/get-search/):
  categorie-/merkfilters naast productidentificatie.
- Reddit-discussies over Grocery Detective en prijsvergelijkers: praktijkervaringen
  met varianten en handmatige controle. Dit is inspiratie, geen databron of bewijs
  dat een productcategorie of actuele prijs klopt.
