# Koopkracht 1.0: aanbiedingen via PrijsProfeet

**Actieve productiescan:** `src/prijsprofeet_v1.py`. De dagelijkse GitHub Actions-workflow gebruikt nu de openbare PrijsProfeet-API in plaats van de niet-functionerende AlleFolders-afbeeldingenscan.

- **Gratis basis:** aanbiedingen van Albert Heijn, Jumbo, Lidl, Aldi, Dirk en andere ondersteunde ketens.
- **Geen sleutel vereist:** publieke endpoints, optioneel `PRIJS_PROFEET_KEY` als GitHub Actions-secret voor hogere limieten.
- **Uitvoer:** een vernieuwd dashboard met acties, kortingspercentages en geldigheidsdatums waar beschikbaar.
- **Geen volledige mandprijs:** normale schapprijzen, uitgebreide matching en historische prijsreeksen vallen buiten de gratis laag.
- **Bron:** [PrijsProfeet](https://www.prijsprofeet.nl). Gebruik van de API is onderworpen aan de [voorwaarden](https://www.prijsprofeet.nl/api-voorwaarden); gebruik de data niet om een concurrerende ruwe kopiedatabase op te bouwen.
- **Test:** Actions → Dagelijkse Koopkracht Scan → Run workflow. De eerste live API-run moet aantonen dat alle drie prioriteitsketens data leveren. Bij onvoldoende data wordt de workflow rood in plaats van een leeg succes te melden.

De oude AlleFolders-parser blijft als experimentele module in de repository maar maakt geen deel meer uit van de dagelijkse productiescan.

---

# Koopkracht: dagelijkse folders, aanbiedingen en recepten

Open-source koopjesradar voor Nederlandse reclamefolders. Gebruikt een automatische GitHub Actions-scan en publiceert een statisch doorzoekbaar dashboard.

## Starten
1. Ga naar **Actions** > **Dagelijkse Koopkracht Scan** > **Run workflow**. GitHub Actions moet voor de repository ingeschakeld zijn.
2. De workflow vindt winkels, folders en aanbiedingen; het dashboard wordt in `docs/index.html` gebouwd.
3. Om het dashboard openbaar bereikbaar te maken: **Settings > Pages > Deploy from a branch > main /docs**.
4. Voor e-mail: zet repository Actions-secrets `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO`. Zonder deze gegevens wordt geen e-mail verstuurd.

**Belangrijk:** dit project is een complete technische basis, maar niet een garantie dat iedere folder en ieder product beschikbaar is. De website kan veranderen of downloads blokkeren. De extractiekwaliteit van OCR varieert. In de dashboardstatus staat welke bronvelden daadwerkelijk zijn verkregen.

## Wat zit erin?
- Dynamische ontdekking van winkel- en folderlinks vanaf AlleFolders (zonder vaste lijst als voorwaarde).
- Paginaverwijzingen naar folderafbeeldingen en herkenning van tekstuele aanbiedingen.
- Optionele OCR van folderafbeeldingen in dagelijkse batches met gratis Tesseract. OCR-resultaten staan als **onbevestigd**, nooit als gecontroleerde winkelprijs.
- Deduplicatie, dagstempels, oude en toekomstige folderverwijzingen.
- Doorzoekbaar HTML-dashboard en JSON-data; prijsvergelijking alleen bij vergelijkbare geregistreerde prijzen.
- Basisrecepten die echte geïndexeerde aanbiedingen als inspiratie gebruiken. Receptprijzen worden niet verzonnen.
- Dagelijks scannen; optionele SMTP-mail op zaterdag, maandag en woensdag.

## Beperkingen
Een volledige, gecontroleerde prijsvergelijking vereist betrouwbare artikelidentificatie, verpakkingshoeveelheden, actievoorwaarden en reguliere prijzen. **OCR is geen garantie op correcte prijsextractie.** Zonder account- of API-toegang zijn Picnic en persoonlijke prijzen niet volledig beschikbaar. Coupons worden niet automatisch geverifieerd. Er is bewust geen fictieve prijsinformatie.

## Lokaal uitvoeren
```bash
pip install -r requirements.txt
python src/koopkracht.py --max-stores 50 --max-folders 150 --ocr-pages 10
python -m unittest discover -s tests
```

Variabelen: `MAX_STORES`, `MAX_FOLDERS`, `OCR_PAGES`, `SCAN_TIMEOUT`, `REQUEST_DELAY`. Bij een eerste test zijn lage maxima verstandig om bronservers niet te overbelasten.

## Privacy en stabiliteit
De repository is openbaar. Zet nooit e-mailwachtwoorden, API-sleutels of privégegevens in code of data; gebruik GitHub Actions Secrets. De scanner gebruikt begrensde verzoeken, tijdslimieten en backoff bij fouten. Respecteer robots.txt en gebruiksvoorwaarden. Er kan aanvullende toestemming nodig zijn voor grootschalige reproductie van folderinhoud.
