# Acceptatiecontrole Supermarkt scan — 3 november 2026

Deze controle legt aantoonbare werking vast. Testsucces is geen 100%-garantie voor externe prijzen, lokale winkelvoorraad, alle productnamen of gegevens op een individuele telefoon.

| Wens | Bevinding en controle |
|---|---|
| Minimaal twee actieproducten per gerecht bij dezelfde winkel | Gemeenschappelijke selector toetst datum, productvariant en verschillende ingrediënten; geldt ook voor ontbijt en lunch. Regressietests en echte gegevens gecontroleerd. |
| Eiwitbron leidend | Vaste rangschikkingsvoorrang; ook getest met extreem hoge bijproductkortingen. |
| Werkelijk voordeel | Hele verpakkingen en verplichte bundels; vergelijking met passende recente prijsopties. Onbekende prijsvoordelen blijven onbekend, oude catalogusprijzen vormen geen actueel bewijs. Externe prijsdekking blijft onvolledig. |
| HelloFresh en Allerhande als bronbasis | Gecontroleerde metadata en originele receptlinks; geen gefingeerde bereidingsinstructies of volledige maaltijdprijzen. |
| Meer variatie | Categorieën, bereidingswijzen, bronselectie en een uitgebreide geïndexeerde bronreceptenbank met bruikbare actiekoppelingen. Beschikbaarheid wisselt met acties. |
| Broodbeleg nooit als rauwe kip | Gemeenschappelijke herkenning in vergelijking, productcodes, receptkoppelingen, winkelopties en bewaarde ingrediënten. Lunch kan expliciet broodbeleg gebruiken zonder de rauwe-kipregel te omzeilen. |
| Ontbijt en lunch | Waren nog niet geïmplementeerd. Nu maaltijdknoppen, acht gecontroleerde Allerhande-bronnen, vier eigen uitgewerkte ontbijt-/lunchgerechten met planning en boodschappenlijst, passende ontbijtproductfamilies en lunchcontext. Op de gecontroleerde actiecatalogus voldoen vier ontbijt- en één lunchrecept aan de actieondergrens. |
| Houdbare volle melk voor cappuccino | Bestaande variant- en verpakkingscontrole, inclusief uitsluiting van verse en lactosevrije vervangingen; browsertest. |
| Zoeken en filters | Unieke zoekveld-ID's, focusbehoud, aantallen, niet-selecteerbare lege exacte-koppelingen en herstelknoppen. |
| Mobiel | Onderscheid Recepten/Bewaard; browserroute test maaltijdknoppen en twee-actiesregel. |
| Favorieten en eigen bewaarde recepten | Behoud en heropenen van snapshots, toevoegen aan planning en browserpersistentieregressies. Dit verifieert geen specifieke lokale iPhone-opslag op afstand. |
| Boodschappenlijst | Vier porties, samengevoegde hoeveelheden, hele verpakkingen en onbekende prijsdelen blijven apart. |
| Koken voor twee dagen | Eigen recepten behouden 2 personen × 2 dagen, vier porties en bewaar-/opwarminstructies. Externe langzaam-koken-recepten worden niet automatisch als bewaarbaar verklaard. |
| Duurzame actualisering | Bestaande actie- en bronworkflows; nieuwe maaltijdbronnen worden mee ververst. Weigeringen en ontbrekende brondata leiden niet tot verzonnen prijzen. |

## Grenzen die open blijven

De reguliere prijscatalogus is afhankelijk van de publicatiefrequentie van een externe leverancier. Een oude catalogus wordt behouden als historische informatie, niet als verse winkelcontrole. Actiemeldingen bewijzen geen filiaalvoorraad of universeel laagste kassaprijs. Veel recepten hebben daarom terecht geen aangetoond prijsvoordeel. Uitgeversrecepten blijven externe links; volledige kookstappen en het plannen van een complete ingrediëntenlijst zijn alleen beschikbaar bij de eigen uitgewerkte recepten.

## Verificatie

Onder meer `recipe-basis.cjs`, `meal-types.cjs`, `recipe-action-ui.cjs`, `recipe-price-ui.cjs`, de bestaande product-, portie- en boodschappenlijstsuites, Python bronparsertests en de Chromium-route voor desktop en mobiel. De publicatie wordt gecontroleerd tegen de werkelijk geserveerde bestanden. Bevindingen van een onafhankelijke actualiteitscontrole blijven zichtbaar wanneer de leverancier geen nieuwe prijzen heeft gepubliceerd.
