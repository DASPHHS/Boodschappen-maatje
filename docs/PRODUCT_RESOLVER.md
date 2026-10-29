# Duurzame product- en prijsresolutie

## Productprofiel: wat wil de gebruiker echt?

Een interesse in `docs/data/watchlist.json` mag een declaratief `match` bevatten:

```json
{
  "key": "volle_melk",
  "title": "Houdbare volle melk voor cappuccino",
  "match": {
    "all": ["volle", "melk"],
    "any": ["houdbare", "houdbaar", "uht", "langlekker"],
    "none": ["verse", "halfvolle", "magere", "plantaardig", "koffiemelk"],
    "traits": {"shelf_life": "houdbaar", "fat": "vol"},
    "pack": {"unit": "L", "amount": 1}
  }
}
```

De centrale `docs/product-resolver.js` levert `match`, `partial` of `reject`. Variant, EAN of verpakking die ontbreken worden nooit stilzwijgend ingevuld. Voor nieuwe producten hoeft geen productspecifieke `if` in de UI.

## Bewijs- en gegevensketen

1. Officiële detailpagina's die bekend zijn, worden gecontroleerd door `scripts/sync_regular_prices.py`; niet-verifieerbare prijzen behouden hun oorspronkelijke datum.
2. Reguliere waarnemingen, acties en de externe promotiefeed blijven apart herkenbaar.
3. `docs/price-observations.js` beoordeelt actualiteit, prijs, verpakking, bron, beschikbaarheid en prijsconflicten.
4. `scripts/build_product_resolution.cjs` schrijft elke dag `docs/data/product-resolution.json`: per gevolgde interesse × winkel één van `price_observed`, `stale_or_unavailable`, `needs_variant_evidence` of `needs_source`.
5. GitHub Actions publiceert de bronstatus. Een ontbrekende bron wordt bij de volgende scan opnieuw bekeken. Een nieuwe bekende detailpagina krijgt een eigen hercontrole en prijsgeschiedenis.
6. Tests controleren zowel keten en databronnen als het niet verwisselen van pakgroottes of houdbare/verse melk.

## Onvermijdelijke beperkingen en escalatie

De gratis promotie-API bevat geen volledige schapprijsinventaris. De resolver kan bronnen combineren en verzoeken registreren, maar kan geen niet-publieke kassaprijs vaststellen. `needs_source` is daarom een correcte uitkomst. Om de dekking structureel uit te breiden zijn additionele, toegestane winkel-specifieke bronadapters of een gelicentieerde schapprijsfeed nodig.

Op de statische GitHub Pages-site blijven eigen productwensen en favorieten alleen in `localStorage`. Zij worden direct vergeleken met de aanwezige feeds; de dagelijkse centrale workflow ziet ze niet automatisch. Via het zichtbare GitHub-issueverzoek kan een gebruiker een nog ontbrekend product expliciet aanmelden voor centrale opvolging. Vermijd geheime API-sleutels in browsercode.

## Inspiratie

- [KortingKlok](https://github.com/RashadAnsari/KortingKlok): bron-snapshots, verschilcontrole en geschiedenis (archiefproject).
- [SupermarktConnector](https://github.com/bartmachielsen/SupermarktConnector): afzonderlijke AH- en Jumbo-dataverzamelaars; onofficiële API's zijn onderhoudsgevoelig.
- [AH sorteren op eenheid](https://github.com/HansKDev/ah-sorteren-op-eenheid): vergelijk prijs per liter/kilo/stuk, niet alleen verpakkingsprijs.
- Reddit-discussies over winkelprijsvergelijking: onbetrouwbare productmatches en oude prijzen zijn belangrijker dan een ogenschijnlijk groot aantal treffers.

Deze concepten zijn opnieuw geïmplementeerd in deze codebasis; er is geen code uit deze projecten overgenomen.
