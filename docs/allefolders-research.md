# AlleFolders technical investigation (23 October 2026)

## Verified web structure

AlleFolders has public store landing pages:

- Lidl: https://www.allefolders.nl/lidl/folder-aanbiedingen
- Albert Heijn: https://www.allefolders.nl/nl/albert-heijn/folder-aanbiedingen
- Jumbo: https://www.allefolders.nl/jumbo/folder-aanbiedingen
- Kruidvat: https://www.allefolders.nl/kruidvat/folder-aanbiedingen

A folder detail page has this shape:

`https://www.allefolders.nl/{store}-aanbiedingen/{folder-uuid}/{page-index}`

A concrete AH example inspected on the public web:

`https://www.allefolders.nl/albert-heijn-aanbiedingen/084ea755-c0a1-42b5-850a-9341c3504198/0`

Page images use a separate CDN:

`https://cdn.jafolders.com/pages/{page-uuid}/small.webp?v={version}`

Example observed:

`https://cdn.jafolders.com/pages/776776ce-7242-477d-955b-a5867ebd59dd/small.webp?v=63886795942`

A Jumbo offer URL was observed:

`https://www.allefolders.nl/jumbo-aanbiedingen/fa23cd05-6e77-4336-88a2-5f35f970f408/36?offer=7c862c59-82e5-456a-bb0b-ff28db949208`

This shows separate identifiers for folder, page and offer. It does NOT establish an undocumented API or that the originating PDF can be downloaded.

## Exploratory script

`python src/allefolders_discovery.py --store jumbo`

Or inspect a specific detail page:

`python src/allefolders_discovery.py --store albert-heijn --folder-url 'https://www.allefolders.nl/albert-heijn-aanbiedingen/084ea755-c0a1-42b5-850a-9341c3504198/0'`

The script only attempts to discover page-image URLs and linked folder pages. It intentionally performs no bulk image download, OCR, scraping of offer prices, or purchases. It has **not been verified in the GitHub Actions environment**. In the current sandbox, direct requests to AlleFolders were blocked, so its runtime behavior remains untested.

## Next production milestones

1. Verify permitted access/robots.txt, response structure and dynamic loading in GitHub Actions.
2. Collect current and forthcoming folder URLs, store validity intervals and page image references.
3. Extract individual offer names, quantities, unit prices and discounts from accessible data or images; annotate source page and detection confidence.
4. Cross-check prices with primary stores and existing PrijsProfeet integration.
5. Build deals-based recipes from verified offers; retain regular-price ingredient lines and do not announce a total unless every ingredient is priced.

Do not switch the existing production PrijsProfeet scanner off until these stages work and have tests.
