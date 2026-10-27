# Boodschappenmaatje

**[Open de winkelhulp](https://dasphhs.github.io/Boodschappen-maatje/)**

1. Kies AH, Jumbo of Lidl.
2. Kies Kip, Vlees, Vis of Vega.
3. Open één gerecht en vink je boodschappen af.

Vier royale porties voor twee personen, twee dagen. Doel: €10 per bereiding, meestal €10–€13 voor vier porties. Eerst de volledig geprijsde recepten binnen €13, daarbinnen de meeste voordelige actieproducten en daarna de laagste portieprijs. Duurdere en onvolledige opties staan apart ingeklapt; €20 is alleen een uitzondering. Verbruik en kassabedrag voor hele verpakkingen staan apart.

De nieuwe startpagina staat in `docs/winkelhulp/`; de bronbestanden staan in `winkelhulp/`. Beide Pages-configuraties (root en `/docs`) openen de winkelhulp. Er is geen server of account nodig. Vinkjes en de laatst gekozen winkel worden alleen lokaal bewaard.

## Receptenbasis

De 40 geselecteerde gerechten zijn eigen aanpassingen van concrete recepten uit de Drive-map: HelloFresh-kaarten, het mealprep-boek en het Surinaamse receptenboek. Elk gerecht bevat de originele recepttitel, het bronbestand, de Drive-link en uitleg over de aanpassing. Het zijn 40 recepten met 120 winkelkaarten. De hoeveelheden zijn **eigen vierportiesbewerkingen**, geen letterlijk overgenomen HelloFresh-porties.

`winkelhulp/recipes.json` bevat uitsluitend receptfeiten en eigen korte bereidingen. Volledige boekteksten, scans en OCR-teksten worden niet gepubliceerd. Het bronoverzicht vermeldt alle 28 bestanden: de ZIP van 2,1 GB is niet verwerkt en OCR blijft controle vereisen. De selectie is geen claim dat elk recept uit ieder bestand is gevalideerd.

## Prijzen en acties

`python src/build_winkelhulp.py` leest de bestaande gedateerde prijssnapshot uit `recepten/winkelprijzen.json`. De dagelijkse receptenprijsscan bouwt de compacte gegevens mee. Geen aanvullende prijsfeed of verzonnen fallback.

- Exacte eenheden en volledige verpakkingen, zonder stilzwijgende portieverkleining.
- Alleen gedateerde, geldige en rekenkundig bevestigde kortingen tellen als actie.
- AH Bonus en Lidl Plus kunnen worden meegenomen; persoonlijke coupons zijn niet aangenomen.
- Een goedkoper passend regulier product wordt direct gekozen boven een duurder actieproduct. Geen extra kosten om een actieaantal op te krikken.
- Geen maaltijdtotaal bij ontbrekende prijs, onbekend uitlekgewicht of niet-bevestigde visvorm.
- De browser trekt verlopen acties in en markeert snapshots ouder dan 36 uur.
- Winkelvoorraad, persoonlijke coupons en de exacte filiaalkassa zijn niet bevestigd.

## Controleren

```sh
python src/build_winkelhulp.py
python -m unittest discover -s tests -p 'test_winkelhulp.py' -v
node tests/test_winkelhulp_engine.cjs
python -m http.server 8765 --directory docs
# Met Playwright beschikbaar:
node tests/winkelhulp_browser.cjs
```

## Prijsverwerking

De bestaande bronnenlezers (`load_shelves` en `load_deals`) worden hergebruikt. De winkelhulp gebruikt een eigen strenge productselectie en de afzonderlijke workflow **Eenvoudige winkelhulp**. Die draait om circa 08:05 Nederlandse tijd en kan ook handmatig gestart worden. Bij bronuitval blijft de vorige publicatie staan. De eerste meegeleverde gegevens zijn berekend uit de gedateerde prijssnapshot in de repository.

Lunch, ontbijt en snacks worden in deze nieuwe interface nog niet als ingevulde productselectie aangeboden. De app vermeldt dit expliciet.

## Budgetoptimalisatie

Kipgerechten bevatten nu expliciet 150 g rauwe kip per persoon en minimaal 300 g groente. Dit is zichtbaar in de boodschappen en de bronaanpassing. Groente wordt niet verkleind om het budget te halen. `winkelhulp/verified-offers.json` vult de prijsfeed aan met gedateerde, onderling gecontroleerde folderwaarnemingen. Deze vervallen automatisch na hun einddatum. De aanvullende Lidl-waarnemingen zijn foldergegevens, geen gecontroleerde filiaalkassa.
