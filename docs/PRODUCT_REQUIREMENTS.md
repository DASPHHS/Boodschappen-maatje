# Boodschappenmaatje: functionele acceptatiecriteria

Status: specificatie, geen claim van implementatie.

## Aanbiedingen eerst
- Dagelijks per AH/Jumbo/Lidl producten tonen onder vlees, vis, groente, aardappelen, pasta, zuivel, vega en overig.
- Elk product: bron-URL, peildatum, geldigheid, actieprijs, reguliere prijs indien bekend, verpakkingsinhoud, eenheidsprijs en prijsvergelijkingsstatus.
- Geen aanbieding tonen als actueel zonder gecontroleerde geldigheid. Niet-geverifieerde prijzen expliciet als onbekend.
- Per product passende alternatieven vergelijken, inclusief huismerk, diepvries, vers, bulk, uitlekgewicht, eetbaar gewicht, bereiding en portiekosten.
- Selecteer de goedkoopste geschikte optie, ook als die niet in de aanbieding is. Vergelijk zowel verbruikskosten als kassabedrag.

## Recepten
- Drive-map 1aYFkOeVn1zdjTBhFAaU11ZfFbAKDlOhn inventariseren en per bestand de verwerkingsstatus vastleggen; grote ZIP en scans niet als verwerkt markeren zonder extractie/controle.
- 20 unieke avondrecepten per supermarkt, met 4 royale porties per bereiding voor 2 personen en 2 dagen; per portie eiwit, groente, koolhydraten, prijs en bereidingstijd.
- Richtwaarden avondeten: 150-250 g vlees/vis waar passend, circa 300 g groente per persoon, eiwitrijk, koolhydraatbewust. Vega krijgt een volwaardige eiwitbron.
- 10 snel te bereiden, draagbare mealprep-lunches; 10 ontbijten; eiwitrijke snacks inclusief kwarkproducten met minstens 20 g eiwit per verpakking.
- Acties en normale producten samen optimaliseren; ingredienten van recepten op dezelfde dag opnieuw prijzen en alternatieven evalueren.
- Verschillende supermarktassortimenten moeten verschillende rangschikkingen en zo nodig verschillende recepten opleveren.

## Betrouwbaarheid
- Bronadapters met expliciete fouten, versheidscontrole en gedateerde snapshots; geen stilzwijgende terugval op fictieve prijzen.
- Dagelijkse GitHub Actions job moet echte gegevens ophalen, bouwen, valideren en publiceren; een geslaagde test alleen geldt niet als succesvolle prijsupdate.
- Rapporteer per winkel dekking, ontbrekende prijzen, laatst geslaagde scan en laatst gepubliceerde snapshot.
- Test onder meer: diepvries goedkoper dan verse actie, afwijkende verpakkingsgroottes, verlopen folder, niet-vergelijkbare visvorm, multi-buy, ontbrekende prijs en 4-portiecalculatie.
