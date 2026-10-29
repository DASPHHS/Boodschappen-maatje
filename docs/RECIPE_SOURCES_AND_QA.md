# Receptbronnen en doorlopende publicatie

Controle van 29 oktober 2026. Het doel is bruikbare, veilige receptinspiratie gekoppeld aan actuele boodschappen, zonder een onbewezen kassaprijs of andermans recepttekst als eigen uitgave te presenteren.

## Onderzochte praktische oplossingen

- **Mealie** (https://github.com/mealie-recipes/mealie): gescheiden import, bronomschrijving, receptenbibliotheek en boodschappenlijst. Import kan stuklopen wanneer schema.org/Recipe ontbreekt of sites hun markup wijzigen. Daarom nooit automatisch publiceren enkel omdat een HTML-parser tekst vond.
- **recipe-scrapers** (https://github.com/hhursev/recipe-scrapers en https://github.com/recipe-scrapers/recipe-scrapers): JSON-LD/schema.org Recipe en site-specifieke extractors. Bruikbaar voor METADATA en controle, maar geen toestemming om auteursrechtelijk beschermde instructies/foto's opnieuw te publiceren.
- **CookDex** (Reddit, r/Mealie, 21 oktober 2026, https://www.reddit.com/r/Mealie/comments/1xbsrqj/): duplicates/non-recipe-detectie, metadata-opruiming, bronkeuze, preview en backup vóór wijzigingen. Overgenomen principe: controle vóór publicatie en regressietests.
- **Checkjebon** (https://github.com/supermarkt/checkjebon): herbruikbare reguliere productwaarnemingen; GitHub issues melden soms vastgelopen updates. Daarom peildatum en productidentiteit checken, geen historisch bedrag stilzwijgend als actuele prijs.
- **PrijsProfeet** (https://github.com/PrijsProfeet/supermarkt-api): gratis API bevat acties, niet het complete winkelassortiment. Geen volledige receptmand uit deze feed afleiden.

## Rechten en receptbronselectie

De bronnen in `docs/data/recipe-sources.json` zijn links naar originele uitgevers: Allerhande, Jumbo, Voedingscentrum, 24Kitchen, Lidl. In de interface worden geen volledige externe instructies, foto's of lange teksten gekopieerd. Het Voedingscentrum noemt voor de algemene website expliciete beperkingen en voorafgaande toestemming, zie https://www.voedingscentrum.nl/nl/service/over-ons/privacy/over-de-site.aspx. Linken naar het origineel is daarom de standaard. Zelfs gestructureerde JSON-LD is geen gebruikslicentie.

## Beveiligde toekomstige import (nog geen automatische overname)

Als er een toegestane feed, partnerlicentie of eigen originele recepten zijn:
1. Selecteer toegestane herkomst en exacte canonieke HTTPS-URL.
2. Lees alleen toegestane metadata: titel, bron, tijd, ingrediëntnamen en porties; bewaar bron- en scanmoment. Nooit blind tekst publiceren.
3. Valideer ingrediënten, hoeveelheden, bereidingsstappen, allergenen, voedselveiligheid, uniek ID, porties en eventuele rechten. Plaats onvolledige records in een reviewwachtrij, niet live.
4. Laat originele recepten of uitdrukkelijk gelicentieerde inhoud pas na review door naar `daily.json` / `weekly.json`. Vertaal of herschrijf een beschermde recepttekst niet louter om die te kopiëren.
5. Koppel aanbodprijzen uitsluitend op winkel, artikelidentiteit, variant, inhoud, geldigheidsdatum en bron. Bij onzekerheid geen prijsclaim.
6. Behoud oude recepten voor de gebruiker na een verversing, maar nooit met een oude actie- of prijsgarantie.

De bestaande 40 oudere bibliotheekconcepten en automatisch gegenereerde actie-ideeën zijn NIET proefgekookt. Externe koppelingen zijn gecontroleerde UITGAANDE BRONLINKS, geen gekopieerde recepten en geen impliciete voedingswaarde- of prijsverificatie.

## Live kwaliteitscontrole

- `tests/browser-journey.cjs`: echte Chromium desktop+mobiel, vijf pagina's, producttoevoeging, reload, favorieten, recepten bewaren, plannen en boodschappenlijst.
- `tests/recipe-source-integrity.cjs`: toegestane links/domeinen, geen instructies/foto's uit derdenarchief en geen vaste weekcampagne op homepage.
- `tests/live-data-freshness.cjs`: nieuw aanbod en productcatalogus, per winkel scanstatus, peildatum, productdekking. Faalt bij structurele terugval en verouderde data.
- `.github/workflows/live-site-check.yml`: twee keer per dag de publieke GitHub Pages-site nalopen. Een mislukking verschijnt zichtbaar als GitHub Actions-fout; nog GEEN e-mail-/pushmelding ingericht.

Beperking: een test op een publieke site toont dat de app technisch werkt, maar kan nooit alle filiaalkassaprijzen onafhankelijk bevestigen of een gerecht proefkoken.
