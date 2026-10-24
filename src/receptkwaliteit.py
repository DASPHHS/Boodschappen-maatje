"""Controle van gerechtidentiteit, benoemde ongeprijsde smaakmakers en bereidingswijzen.

De prijsmotor rekent uitsluitend ingrediënten uit het geprijsde recept. Deze
smaakmakers staan apart, zonder inventarisatie van wat iemand in huis heeft.
"""
import re
from receptenradar_catalog import ING

BASIS = ("olijfolie (circa 1 eetlepel)", "zout naar smaak", "zwarte peper naar smaak")
BROTH = "groentebouillon (circa 600 ml, bereid met water en bouillonblokje)"

def pantry_for_recipe(title, ingredients, instructions=""):
    """Concreet vermelde smaakmakers, bewust niet meegerekend in de winkelprijs."""
    name = title.casefold()
    keys = {key for key, _, _ in ingredients}
    if name.startswith("ontbijt:"):
        if any(x in name for x in ("ei-", "eiwrap", "omelet", "muffin")):
            return list(BASIS)
        return ["kaneel (optioneel)"] if any(x in name for x in ("havermout", "oats")) else []
    if any(x in name for x in ("risotto",)):
        return list(BASIS) + [BROTH, "knoflook (1 teen)", "gedroogde tijm (1 theelepel)"]
    pantry = list(BASIS)
    if any(x in name for x in ("teriyaki", "koreaans", "koreaanse", "japans", "japanse", "gember", "soja", "sticky")):
        pantry += ["sojasaus (2 eetlepels)", "gemberpoeder (1 theelepel)", "knoflook (1 teen)"]
    elif any(x in name for x in ("mexicaans", "mexicaanse", "fajita", "burrito", "chipotle", "gallo pinto", "bonensalsa")):
        pantry += ["gemalen komijn (1 theelepel)", "paprikapoeder (1 theelepel)", "chilipoeder naar smaak"]
    elif any(x in name for x in ("curry", "kokos", "thaise", "indonesisch", "indonesische")):
        pantry += ["currypoeder (2 theelepels)", "knoflook (1 teen)"]
    elif any(x in name for x in ("italiaans", "italiaanse", "bolognese", "lasagne", "mediterraan", "mediterrane", "pasta", "tomatensaus")):
        pantry += ["gedroogde oregano (1 theelepel)", "knoflook (1 teen)"]
    elif any(x in name for x in ("shoarma", "harissa")):
        pantry += ["knoflookpoeder (1 theelepel)", "paprikapoeder (1 theelepel)"]
    elif "tonijn" in name or "zalm" in name:
        pantry += ["gedroogde dille (1 theelepel)"]
    elif any(x in name for x in ("champignon", "varkenshaas", "oven", "geroosterd", "traybake", "krieltjes")):
        pantry += ["gedroogde tijm (1 theelepel)", "paprikapoeder (1 theelepel)"]
    elif any(x in name for x in ("wok", "tofu", "aziatisch", "aziatische")):
        pantry += ["sojasaus (2 eetlepels)", "knoflook (1 teen)"]
    else:
        pantry += ["paprikapoeder (1 theelepel)"]
    if "yoghurt" in keys or "kwark" in keys:
        if any(x in name for x in ("wrap", "saus", "salade", "fris", "bowl", "dressing")):
            pantry += ["citroensap (1 eetlepel)", "knoflookpoeder (naar smaak)"]
    if "teriyaki" in name or "zoetzur" in name:
        pantry += ["honing (1 eetlepel)"]
    if "zoetzur" in name:
        pantry += ["azijn (1 eetlepel)"]
    if "harissa" in name:
        pantry += ["harissakruiden (1 theelepel)"]
    # De specifieke bereidingswijze kan extra, niet geprijsde smaakmakers noemen.
    # Maak die zichtbaar in plaats van ze in de instructie te verstoppen.
    mentioned = (name + " " + instructions.casefold())
    extras = (
        ("knoflook", "knoflook (1 teen)"),
        ("citroen", "citroensap (1 eetlepel)"),
        ("sojasaus", "sojasaus (2 eetlepels)"),
        ("gember", "gemberpoeder (1 theelepel)"),
        ("komijn", "gemalen komijn (1 theelepel)"),
        ("paprikapoeder", "paprikapoeder (1 theelepel)"),
        ("tijm", "gedroogde tijm (1 theelepel)"),
        ("dille", "gedroogde dille (1 theelepel)"),
        ("currypoeder", "currypoeder (2 theelepels)"),
        ("honing", "honing (1 eetlepel)"),
    )
    for term, label in extras:
        if term in mentioned and not any(term in item for item in pantry):
            pantry.append(label)
    return list(dict.fromkeys(pantry))

UNSUPPORTED_DISH_WORDS = re.compile(
    r"\b(garnalen|bulgur|orzo|paksoi|spekjes|pompoen|aubergine|tempeh|noedels|"
    r"spitskool|kalfsburger|biefstuk|conchiglie|tahin|falafel)\b", re.I
)

def dish_quality_issues(title, category, ingredients):
    """Voorkom dat gerechtstitels ingrediënten beloven die het recept niet bevat."""
    name = title.casefold()
    keys = {key for key, _, _ in ingredients}
    issues = []
    if UNSUPPORTED_DISH_WORDS.search(name):
        issues.append("Niet-ondersteunde gerechtnaam (ingrediënt ontbreekt): " + title)
    if "kip" in name and not keys.intersection({"kipfilet", "kipdij", "kipgehakt", "shoarma"}):
        issues.append("Kip wordt genoemd, maar ontbreekt")
    if "zalm" in name and not keys.intersection({"zalm", "gerookte_zalm"}):
        issues.append("Zalm wordt genoemd, maar ontbreekt")
    if re.search(r"\brisotto\b", name) and "risottorijst" not in keys:
        issues.append("Risotto zonder echte risottorijst")
    if "rijst" in name and not keys.intersection({"rijst", "risottorijst"}):
        issues.append("Rijst in titel ontbreekt")
    if "pasta" in name and "pasta" not in keys:
        issues.append("Pasta in titel ontbreekt")
    if category == "Vegetarisch" and keys.intersection({
        "kipfilet","kipdij","kipgehakt","shoarma","gehakt","varkenshaas",
        "zalm","gerookte_zalm","tonijn","rookworst"
    }):
        issues.append("Vlees of vis onder vegetarisch recept")
    return issues

def cooking_instructions(title, ingredients, curated=""):
    """Een volledige uitvoerbare basisbereiding; bekende specifieke methode gaat voor."""
    if curated:
        return curated
    name = title.casefold()
    keys = {key for key, _, _ in ingredients}
    def has(*names): return bool(keys.intersection(names))
    if name.startswith("ontbijt:"):
        if "overnight" in name:
            return ("Meng havermout, kwark of skyr en eventuele melk. Verdeel over vier afsluitbare bakjes. "
                    "Laat ten minste 4 uur of een nacht afgedekt in de koelkast staan. "
                    "Voeg fruit en eventuele noten vlak voor het eten toe.")
        if "muffin" in name:
            return ("Verwarm de oven voor op 180 °C. Klop de eieren los, snijd paprika en spinazie fijn "
                    "en verdeel met een deel van de kwark over ingevette muffinvormpjes. "
                    "Bak circa 18-22 minuten totdat het ei volledig gestold is. "
                    "Serveer de rest van de kwark ernaast.")
        if "omelet" in name or "eiwrap" in name:
            return ("Verwarm een koekenpan met wat olijfolie. Bak de gesneden groenten kort, voeg de "
                    "losgeklopte eieren toe en laat volledig stollen. Verwarm eventuele wraps volgens "
                    "de verpakking en serveer de kwark of skyr apart.")
        if "warme havermout" in name:
            return ("Verwarm de havermout met melk en wat water op laag vuur tot een romige pap. "
                    "Neem de pan van het vuur, verdeel over vier kommen en voeg kwark en gesneden banaan toe.")
        return ("Verdeel de kwark of skyr over vier kommen. Was en snijd het fruit; voeg havermout "
                "en eventuele ongezouten noten toe. Serveer direct.")
    if "teriyaki" in name and not curated:
        return ("Kook de zilvervliesrijst volgens de verpakking. Snijd de kip en groenten. "
                "Bak de kip in olijfolie volledig gaar en roerbak de groenten beetgaar. "
                "Roer sojasaus, honing, gember en knoflook met een paar eetlepels water "
                "door elkaar, voeg toe en schep om tot het alles licht bedekt. "
                "Serveer met de rijst.")
    if "zoetzur" in name:
        return ("Kook de zilvervliesrijst volgens de verpakking. Snijd de kip in stukjes en "
                "bak deze in olijfolie volledig gaar. Bak de gesneden paprika kort mee. "
                "Voeg de tomatenblokjes, honing en azijn toe en laat circa 8 minuten zachtjes "
                "inkoken tot een zoetzure saus. Serveer met de rijst.")
    if "gehaktballetjes" in name or "köfte" in name:
        return ("Kneed het gehakt met de genoemde kruiden tot kleine balletjes en bak ze in "
                "olijfolie rondom bruin en volledig gaar. Kook de aanwezige pasta volgens "
                "de verpakking. Voeg gesneden groenten en eventuele tomatenblokjes of "
                "kokosmelk toe aan de pan en laat zachtjes garen. "
                "Roer eventuele spinazie pas als laatste erdoor en serveer met de pasta "
                "of met de overige groenten.")
    if "stamppot" in name:
        meat = ("Verwarm de rookworst volgens de verpakking en snijd in porties. "
                if "rookworst" in keys else
                "Bak de kip volledig gaar en breng op smaak met de genoemde kruiden. "
                if has("kipfilet","kipdij") else
                "Bak het gehakt gaar met de fijngesneden ui. " if "gehakt" in keys else "")
        return ("Schil de aardappelen en kook ze met de boerenkool in circa 20 minuten gaar "
                "(volg bij diepvriesgroente de verpakkingsinstructie). "
                + meat + "Giet af en stamp aardappelen en boerenkool met een scheut kookvocht. "
                "Serveer met de bereide eiwitbron.")
    if "gevulde paprika" in name:
        return ("Verwarm de oven voor op 190 °C. Kook de rijst volgens de verpakking. "
                "Halveer de paprika's en verwijder de zaadlijsten. Bak het rundergehakt "
                "volledig gaar met de kruiden; roer tomatenblokjes en rijst erdoor. "
                "Vul de paprikahelften en bak ze circa 20-25 minuten in de oven tot ze zacht zijn.")
    if "gevulde zoete aardappel" in name:
        return ("Prik de zoete aardappelen rondom in en gaar ze circa 10-15 minuten in de "
                "magnetron, afhankelijk van hun grootte. Verwarm de bonen met de kruiden. "
                "Snijd de gare aardappelen open en vul met bonen en gesneden tomaat. "
                "Schep er yoghurt over en serveer direct.")
    if "lasagne" in name:
        return ("Verwarm de oven voor op 200 °C. Snijd de courgette in dunne plakken. "
                "Verwarm de uitgelekte linzen met tomatenblokjes en de genoemde kruiden. "
                "Maak in een ovenschaal afwisselend laagjes courgette en linzensaus, "
                "eindig met geraspte kaas en bak circa 25-30 minuten tot de courgette zacht is.")
    if "visstoof" in name:
        return ("Kook de aardappelen in circa 15-20 minuten gaar. Snijd de wortel in kleine "
                "stukken en laat met 150 ml water, olie en kruiden afgedekt zacht worden. "
                "Voeg de zalm in stukken toe en gaar rustig in de stoof, zonder hard koken. "
                "Neem de pan van het vuur en roer de yoghurt erdoor; serveer met de krieltjes.")
    if "frittata" in name or "omelet" in name or "shakshuka" in name:
        if "shakshuka" in name:
            return ("Fruit de gesneden groenten en specerijen in wat olijfolie. Voeg de uitgelekte "
                    "bonen en tomatenblokjes toe en laat 8-10 minuten zachtjes pruttelen. "
                    "Maak kuiltjes, breek de eieren erin, dek af en gaar tot het eiwit volledig gestold is.")
        return ("Verwarm de oven voor op 180 °C. Bak eventuele rauwe kip eerst volledig gaar "
                "in een ovenbestendige pan met olijfolie. Voeg de gesneden groenten toe en "
                "bak kort. Klop de eieren los en schenk over de pan. Voeg eventuele kaas of "
                "gerookte zalm toe. Gaar 12-18 minuten tot het ei volledig gestold is.")
    if "risotto" in name:
        raise ValueError("Risotto vereist een specifieke, gecontroleerde bereidingswijze")
    steps = ["Was en snijd de groenten. Giet bonen, linzen of kikkererwten uit blik af als deze worden gebruikt."]
    if "rijst" in keys:
        steps.append("Kook de zilvervliesrijst volgens de verpakking; gebruik een apart pannetje.")
    if "pasta" in keys:
        steps.append("Kook de volkoren pasta volgens de verpakking en bewaar eventueel een scheut kookwater.")
    if "couscous" in keys:
        steps.append("Bereid de volkoren couscous met heet water volgens de verpakking en roer los.")
    if "naan" in keys:
        steps.append("Verwarm het naanbrood volgens de verpakking.")
    if "aardappel" in keys or "zoete_aardappel" in keys:
        if "oven" in name or "gerooster" in name or "traybake" in name or "plaat" in name:
            steps.append("Verwarm de oven voor op 200 °C en rooster de gesneden (zoete) aardappelen "
                         "met een beetje olijfolie circa 25-35 minuten tot ze gaar zijn.")
        else:
            steps.append("Snijd de (zoete) aardappelen in kleine stukken en kook ze in circa 15-20 minuten gaar, "
                         "of bak de stukjes met wat olijfolie in een afgedekte pan tot ze zacht zijn.")
    if has("kipfilet","kipdij","kipgehakt","shoarma"):
        steps.append("Bak de kip of het kipgehakt met de genoemde kruiden in een beetje olijfolie; "
                     "zorg dat alle stukken volledig gaar zijn.")
    elif "gehakt" in keys:
        steps.append("Bak het rundergehakt rul en volledig gaar in olijfolie en breng op smaak met de genoemde kruiden.")
    elif "varkenshaas" in keys:
        steps.append("Bak de varkenshaas rondom bruin in olijfolie, laat op matig vuur garen en kort rusten.")
    elif "rookworst" in keys:
        steps.append("Verwarm de rookworst volgens de bereidingsinstructies op de verpakking.")
    elif "zalm" in keys:
        steps.append("Bak de zalm rustig in wat olijfolie tot deze gaar is; bij diepvrieszalm volg je "
                     "de instructies voor ontdooien en bereiden op de verpakking.")
    elif "gerookte_zalm" in keys:
        steps.append("Houd de gerookte zalm gekoeld en voeg deze pas bij het serveren toe.")
    elif "tofu" in keys:
        steps.append("Dep de tofu droog, snijd in blokjes en bak in een beetje olijfolie rondom goudbruin.")
    elif "tonijn" in keys:
        steps.append("Laat de tonijn uit blik goed uitlekken; deze hoeft niet opnieuw gaar gebakken te worden.")
    elif "eieren" in keys:
        steps.append("Kook de eieren hard in circa 9 minuten, of bak ze in olijfolie tot het eiwit gestold is.")
    if "curry" in name or "stoof" in name or "bolognese" in name or "tomatensaus" in name:
        steps.append("Fruit de specerijen kort en voeg de aanwezige tomatenblokjes en/of kokosmelk toe. "
                     "Voeg stevige groenten en peulvruchten toe; laat zachtjes pruttelen totdat ze gaar zijn. "
                     "Voeg spinazie pas aan het einde toe.")
    elif any(x in name for x in ("oven", "gerooster", "traybake", "plaat", "schotel", "lasagne")):
        steps.append("Bereid de overige groenten gaar in de oven of een pan. "
                     "Verdeel bij een ovenschotel de bereide onderdelen over een ovenschaal, "
                     "strooi eventuele kaas erover en bak tot de kaas gesmolten is.")
    else:
        steps.append("Roerbak stevige groenten zoals broccoli, paprika, champignons of wortel in olijfolie "
                     "tot ze beetgaar zijn. Verwarm eventuele peulvruchten mee; voeg spinazie "
                     "alleen kort toe als deze warm geserveerd wordt.")
    if "wrap" in name or "tortilla" in name or "fajita" in name:
        steps.append("Warm de wraps volgens de verpakking. Vul met de bereide ingrediënten; "
                     "voeg sla, komkommer en tomaat vers toe. Meng eventuele yoghurt of kwark met "
                     "de genoemde smaakmakers tot een dressing en serveer erbij.")
    elif any(x in name for x in ("salade", "bowl", "poké")):
        steps.append("Verdeel de bereide onderdelen over vier kommen of bakjes. Voeg sla, komkommer, "
                     "tomaat en avocado, voor zover aanwezig, vers toe. "
                     "Gebruik eventuele yoghurt of kwark als frisse dressing.")
    else:
        steps.append("Meng of serveer de onderdelen samen. Voeg eventuele yoghurt of kwark pas op "
                     "het einde buiten het vuur toe en maak af met de genoemde smaakmakers.")
    return " ".join(steps)
