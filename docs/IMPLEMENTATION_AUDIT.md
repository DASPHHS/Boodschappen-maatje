# Boodschappen-maatje: audit en uitvoering, 26 oktober 2026

## Gecontroleerde uitvoering

Uitgangspunt: bestaande main op `25e3c857c96eeee440dd6931fbc7093a45d6b57f`.
Implementatie gepubliceerd als `3017db82c56e339746eb8f1906f96585c13bb285`.
De daaropvolgende automatische prijsscan publiceerde `2c53f306dd01dfca4aacffb3ae4e8733d5665778`.
Dit rapport onderscheidt bevestigde uitvoering van ontbrekende productfuncties.

- 27 bestaande Python-modules geïnventariseerd, aangevuld met winkelparser en herhaalbare audit.
- Alle Python-tests uitgevoerd, na aanvullende wijzigingen 142 tests geslaagd.
- Alle 14 bestaande en nieuwe Node-regressiescripts uitgevoerd en geslaagd.
- Alle JavaScript-modules op syntaxis gecontroleerd.
- GitHub Actions Platform kwaliteit geslaagd: echte Chromium-tests op 390 en 1280 pixels, vijf productzoekopdrachten, actiecheckbox, geen horizontale overflow of runtimefouten op de koopjespagina.
- Prijswatchlist kwaliteit geslaagd in GitHub Actions.
- Volledige live receptenprijsscan lokaal én in GitHub Actions uitgevoerd. Prijsscan succesvol, geen gemelde bronfouten.
- 641 receptberekeningen op interne consistentie gecontroleerd. Geen ongeschikte ingrediënten volgens de bestaande semantische uitsluitingsregels gevonden.
- Gepubliceerde koopjeszoeker in een browser gebruikt voor vaatwastabletten; resultaten met Action en supermarkten bevestigd.

## Functionaliteit per onderdeel

| Onderdeel | Status | Bewijs en resterende grens |
|---|---|---|
| Direct producten zoeken | Werkt | Resultaten direct op dezelfde pagina, reguliere prijzen en gedateerde acties |
| Winkel, merk, categorie, korting, sorteren | Werkt | Gedeelde deterministische engine, Node-tests en browsertests |
| Eerlijke eenheidsprijzen | Gedeeltelijk | Tablet, expliciete wasbeurt, kg, liter, shampoo per 100 ml; rollen worden niet als vellen beschouwd; onbekende inhoud blijft onbekend |
| AH/Jumbo/Lidl receptenprijzen | Werkt met beperkingen | Complete én incomplete recepten zichtbaar; smaakmakers/voorraad en niet-bevestigd uitlekgewicht blijven uitgesloten |
| Jumbo-aanbiedingen en recepten | Werkt | 1.617 actuele actievermeldingen en 92 volledig geprijsde recepten in live scan |
| Lidl-aanbiedingen | Gedeeltelijk | 28 gedateerde vermeldingen, slechts één aantoonbare korting; officiële aanvulling is een gedateerde momentopname |
| Weekmandjes | Gedeeltelijk | Identieke gerechten tussen drie winkels; gedeelde actieverpakkingen hersteld. Aantal gerechten gaat nu uit van bestaande instelling 4, niet hard gecodeerd 3 |
| Gezonde receptkeuze | Gedeeltelijk | Eiwit- en groenteschattingen, filters en kwaliteitswaarschuwingen; geen universele controle van voedingswaarden per winkel-SKU |
| Bronrecepten | Gedeeltelijk | Brede titels/linkindex met keukens en beperkte Recipe JSON-LD-controle. Titels zijn geen volledig geverifieerde recepten |
| Favorieten | Werkt | Bestaande opslag behouden, extra productgroepen, gecontroleerde import/export voor handmatige overdracht |
| Automatische synchronisatie apparaten | Ontbreekt | Geen accountdienst of privébackend ingericht |
| Action-prijzen | Gedeeltelijk | 19 rechtstreeks gecontroleerde producten. GitHub-runner ontvangt HTTP 403 voor productpagina's; geen betrouwbare automatische dagelijkse verversing |
| Andere drogisten en winkels | Ontbreekt in nieuwe zoekindex | Kruidvat-landingspagina bereikbaar, geen gevalideerde feed. Etos/DA/Trekpleister/Online Drogist/Wibra/Zeeman/buitenland nog niet geïntegreerd |
| Historische bodemprijs/dealscore | Ontbreekt | Geen voldoende lange vergelijkbare prijsreeks. Geen verzonnen 'scherpe reguliere prijs'-claim |
| EAN-identiteit over winkels | Gedeeltelijk | EAN-velden in bronnen, onvoldoende dekking voor universele exacte productvergelijking |
| Zoekprestaties | Werkt voor huidige omvang | Eén index, maximaal 60 kaarten per render, meer laden; eerste download circa 4,7 MB blijft verbeterpunt |
| Instellingen | Gedeeltelijk | Bestaande configuratie en filters; geen complete persoonlijke instellingenpagina |

## Werkelijke dekking uit live scan

De aantallen hieronder horen bij de scan van 26 oktober. Een importtijd is niet hetzelfde als een nieuw geverifieerde winkelprijs. Vermeldingen zijn niet hetzelfde als unieke EAN-producten.

| Winkel | Reguliere bronprijzen | Acties met geldige datums | Wiskundig bevestigde korting | Volledig geprijsde recepten |
|---|---:|---:|---:|---:|
| Albert Heijn | 15.657 | 3.225 | 3.225 | 146 |
| Jumbo | 9.713 | 1.617 | 1.569 | 92 |
| Lidl | 5.369 | 28 | 1 | 43 |
| Action | 19 gecontroleerde productprijzen | 0 als actie geclaimd | 0 | Niet van toepassing |
| Overige winkels | 0 in nieuwe productzoekindex | 0 in nieuwe productzoekindex | 0 | Niet van toepassing |

De oudere aanbiedingen/foldermodule kan aanvullende winkels noemen; dat bewijst geen betrouwbare reguliere productdekking voor prijsvergelijking.

## Herstelde fouten

1. `export_shopping_index` verloor valid_from: doorgegeven als twaalfde promotieveld. Watchlist gebruikt uitsluitend acties met beide datums.
2. De oude mealplanner liet ongedateerde acties door: uitgesloten, datum volgens Europe/Amsterdam.
3. Weekmand splitste dezelfde bundel-SKU bij een andere effectieve gemiddelde prijs: prijsverschil is geen aparte verkoopeenheid meer als dezelfde actie geldt.
4. De dagelijkse aanbiedingenrenderer overschreef de platformstartpagina: verwijderd en met tijdelijke map getest.
5. Browsermand gebruikte aankoopverpakkingen inclusief bundeloverschot als deler voor reguliere stukprijs: gebruikt nu de werkelijk benodigde verpakkingen.
6. Browsermand kon onvolledige gratis/bundelvoorwaarden behandelen als losse korting: geblokkeerd.
7. Prijsindex werd geschreven vóór receptvalidatie: verplaatst tot na de controle.
8. Bronreceptparser herkende geen PropertyValue-ingrediënten en kon een brood als persoonsportie interpreteren: hersteld.
9. Boodschappenassistent en chatprijsvergelijker lieten actieperiodes buiten beschouwing: toekomstige, verlopen en ongedateerde acties uitgesloten.
10. Navigatie hoofdingang bood geen direct productzoeken: zes functionele ingangen en direct zoekformulier toegevoegd.

## Gewijzigde bestanden en automatisering

- `docs/koopjes/index.html`, `app.js`, `engine.js`: zelfstandige productzoeker en prijsfilters.
- `src/retailer_prices.py`, `docs/koopjes/retailer-prices.json`: begrensde officiële Product JSON-LD-parser en feitelijke prijsuitvoer.
- `.github/workflows/retailer-prices.yml`: dagelijkse poging, beperkte verzoeken, robotscontrole, bronfoutregistratie.
- `.github/workflows/quality.yml`, `tests/browser_smoke.js`: volledige Python/Node-regressie en echte mobiele/desktop Chromium-controle.
- `src/receptenradar_v2.py`, `src/weekmenu_advies.py`, `src/meal_planner.py`, `src/koopkracht.py`: datumexport, publicatievolgorde, mandberekening en stabiele startpagina.
- `src/bronrecept_controle.py`: uitgebreid gestructureerd Recipe-formaat en portiecontrole.
- `recepten/watchlist*` en `docs/recepten/watchlist*`: favorieten, datums en overdracht.
- `recepten/index.html` en `docs/recepten/index.html`: browsermandprijs hersteld.
- `src/platform_audit.py`, `docs/platform-audit.json`: herhaalbare inventaris en prijsconsistentiecontrole.
- Nieuwe regressietests voor bundelaggregatie, koopjes, officiële Product-data en behoud startpagina.

## Brononderzoek en voorwaarden

Gecontroleerd: Checkjebon open dataset, PrijsProfeet API/documentatie/voorwaarden, Schema.org Recipe en PropertyValue, officiële Action-productpagina's en robots.txt, Kruidvat-landingspagina en robots.txt. GitHub- en Reddit-zoekopdrachten gebruikt voor ontdekking; geen ongecontroleerde forumcode overgenomen. Bronvermeldingen en gebruiksvoorwaarden blijven van toepassing; geen volledige beschermde receptinstructies gekopieerd. Geen betaalde diensten aangeschaft.

## Resterende prioriteiten

1. Een toegestane stabiele Action-feed of expliciete toegang voor GitHub-runner regelen. HTTP 403 niet omzeilen. Bronuitval zichtbaar laten, verouderde Action-prijzen na 36 uur uitsluiten.
2. Drogisterijfeeds afzonderlijk valideren voordat winkeldekking wordt geclaimd. Geen abonnement zonder toestemming.
3. Netto- versus uitlekgewicht en smaakmakers per recept sluitend maken. Tot die tijd bedragen labelen als geprijsde onderdelen.
4. Winkel-SKU-voedingswaarden aanvullen; voedingsschattingen blijven schattingen.
5. Persoonlijke menu-instellingen, acht dagen/twee dagen per gerecht en categoriegestuurde afvinklijst verder uitwerken.
6. EAN, productvarianten en wettelijke/licentievoorwaarden per bron vastleggen vóór uitbreiding van prijsarchief en historische dealclaims.
7. Index opsplitsen per categorie/winkel en downloaden op behoefte. Prijsimport blijft voor huidige zoekfunctie groter dan wenselijk.
8. Automatische privésynchronisatie vereist een gekozen account/backend; huidige import/export werkt zonder persoonsgegevens naar een server te sturen.

Deze uitvoering is een gecontroleerde verbetering van het bestaande platform. De volledige masteropdracht is niet afgerond: de ontbrekende functies hierboven zijn geen bewezen werkende functionaliteit.
