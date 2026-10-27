"""Brede, volledig gespecificeerde EIGEN maaltijdvarianten voor de prijsengine.

Geen kopieën van titel-only bronarchieven. Iedere variant heeft vierpersoons-
hoeveelheden en alleen bestaande ingrediëntenidentiteiten. De actuele
winkelprijs, korting en volledigheid bepaalt receptenradar_v2, niet dit bestand.
"""
from receptenradar_catalog import ING

# Keuken, titel, eiwitcategorie, tijd in minuten, ingrediënten per vier personen.
# Gebruik alleen culinaire combinaties; portiegrootte circa 150-200 g vlees/vis
# of een passende plantaardige combinatie per persoon.
DISHES=[
 ("Surinaams","Surinaamse kipmasala met sperziebonen en rijst","Kip",35,[("kipdij",700,"g"),("sperziebonen",800,"g"),("rijst",300,"g"),("ui",200,"g"),("tomatenblokjes",400,"g")]),
 ("Surinaams","Surinaamse bruine-bonenschotel met paprika en rijst","Vegetarisch",30,[("bruine_bonen",800,"g"),("paprika",3,"st"),("rijst",300,"g"),("ui",200,"g"),("tomatenblokjes",400,"g")]),
 ("Surinaams","Surinaamse kip met kousenband-alternatief sperziebonen en aardappel","Kip",35,[("kipfilet",700,"g"),("sperziebonen",900,"g"),("aardappel",800,"g"),("ui",200,"g")]),
 ("Surinaams","Surinaamse tofu met bruine bonen en rijst","Vegetarisch",30,[("tofu",700,"g"),("bruine_bonen",650,"g"),("rijst",280,"g"),("paprika",3,"st")]),
 ("Indonesisch","Indonesische kip-ketjap met wokgroenten en rijst","Kip",30,[("kipdij",700,"g"),("wok",1100,"g"),("rijst",300,"g"),("ui",150,"g")]),
 ("Indonesisch","Indonesische tempeh met paksoi en rijst","Vegetarisch",30,[("tempeh",700,"g"),("paksoi",1100,"g"),("rijst",300,"g"),("wortel",300,"g")]),
 ("Indonesisch","Indonesische garnalen met groenten en noedels","Vis",25,[("garnalen",700,"g"),("wok",1100,"g"),("noedels",320,"g"),("ui",150,"g")]),
 ("Thais","Thaise kipcurry met bloemkool en rijst","Kip",35,[("kipfilet",700,"g"),("bloemkool",1,"st"),("spinazie",450,"g"),("rijst",300,"g"),("kokosmelk",400,"ml")]),
 ("Thais","Thaise tofu met broccoli en noedels","Vegetarisch",25,[("tofu",700,"g"),("broccoli",900,"g"),("noedels",320,"g"),("paprika",3,"st")]),
 ("Thais","Thaise garnalencurry met courgette en rijst","Vis",30,[("garnalen",700,"g"),("courgette",3,"st"),("rijst",300,"g"),("kokosmelk",400,"ml"),("wortel",350,"g")]),
 ("Indiaas","Indiase kipmadras met bloemkool en rijst","Kip",35,[("kipdij",700,"g"),("bloemkool",1,"st"),("rijst",300,"g"),("tomatenblokjes",400,"g"),("ui",200,"g")]),
 ("Indiaas","Indiase kikkererwtencurry met spinazie en naan","Vegetarisch",30,[("kikkererwten",850,"g"),("spinazie",850,"g"),("tomatenblokjes",400,"g"),("naan",4,"st")]),
 ("Indiaas","Indiase linzencurry met broccoli en rijst","Vegetarisch",30,[("linzen",900,"g"),("broccoli",900,"g"),("rijst",300,"g"),("tomatenblokjes",400,"g")]),
 ("Vietnamees","Vietnamese kip met paksoi en noedels","Kip",25,[("kipfilet",700,"g"),("paksoi",900,"g"),("noedels",320,"g"),("wortel",350,"g")]),
 ("Vietnamees","Vietnamese tofu met wokgroenten en rijst","Vegetarisch",25,[("tofu",750,"g"),("wok",1100,"g"),("rijst",300,"g")]),
 ("Chinees","Chinese kiproerbak met broccoli en rijst","Kip",25,[("kipfilet",750,"g"),("broccoli",900,"g"),("paprika",3,"st"),("rijst",300,"g")]),
 ("Chinees","Chinese garnalen met paksoi en noedels","Vis",25,[("garnalen",700,"g"),("paksoi",1000,"g"),("noedels",320,"g"),("champignons",350,"g")]),
 ("Japans","Japanse zalm met broccoli en rijst","Vis",30,[("zalm",700,"g"),("broccoli",1100,"g"),("rijst",300,"g")]),
 ("Japans","Japanse tofu met champignons en noedels","Vegetarisch",25,[("tofu",750,"g"),("champignons",800,"g"),("noedels",320,"g"),("spinazie",400,"g")]),
 ("Koreaans","Koreaanse kip met wortel en rijst","Kip",30,[("kipdij",700,"g"),("wortel",750,"g"),("spinazie",450,"g"),("rijst",300,"g")]),
 ("Koreaans","Koreaanse tofu met paksoi en noedels","Vegetarisch",25,[("tofu",700,"g"),("paksoi",1000,"g"),("noedels",320,"g"),("champignons",300,"g")]),
 ("Marokkaans","Marokkaanse kip met courgette en couscous","Kip",35,[("kipdij",700,"g"),("courgette",3,"st"),("wortel",600,"g"),("couscous",320,"g")]),
 ("Marokkaans","Marokkaanse kikkererwtenstoof met wortel en couscous","Vegetarisch",35,[("kikkererwten",900,"g"),("wortel",900,"g"),("tomatenblokjes",400,"g"),("couscous",320,"g")]),
 ("Libanees","Libanese kip met paprika en bulgur","Kip",30,[("kipfilet",700,"g"),("paprika",4,"st"),("bulgur",320,"g"),("komkommer",2,"st")]),
 ("Libanees","Libanese kikkererwtensalade met bulgur en komkommer","Vegetarisch",25,[("kikkererwten",900,"g"),("bulgur",320,"g"),("komkommer",2,"st"),("tomaten",550,"g")]),
 ("Grieks","Griekse kip met courgette en krieltjes","Kip",35,[("kipfilet",750,"g"),("courgette",3,"st"),("aardappel",850,"g"),("yoghurt",300,"g")]),
 ("Grieks","Griekse zalm met groenten en aardappeltjes","Vis",35,[("zalm",700,"g"),("paprika",4,"st"),("aardappel",850,"g"),("tomaten",450,"g")]),
 ("Italiaans","Italiaanse varkenshaas met champignons en krieltjes","Vlees",35,[("varkenshaas",750,"g"),("champignons",800,"g"),("aardappel",800,"g"),("spinazie",400,"g")]),
 ("Italiaans","Italiaanse volkorenpasta met tonijn en courgette","Vis",30,[("tonijn",600,"g"),("courgette",3,"st"),("pasta",320,"g"),("tomatenblokjes",400,"g")]),
 ("Italiaans","Italiaanse groentepasta met mozzarella","Vegetarisch",30,[("mozzarella",500,"g"),("pasta",320,"g"),("spinazie",650,"g"),("tomaten",600,"g")]),
 ("Mexicaans","Mexicaanse kipwraps met paprika en bonen","Kip",30,[("kipfilet",700,"g"),("paprika",4,"st"),("bonen",650,"g"),("wraps",8,"st")]),
 ("Mexicaans","Mexicaanse bonenschotel met rijst en mais","Vegetarisch",30,[("kidneybonen",900,"g"),("mais",400,"g"),("paprika",4,"st"),("rijst",320,"g")]),
 ("Turks","Turkse kip met aubergine en bulgur","Kip",35,[("kipdij",750,"g"),("aubergine",800,"g"),("bulgur",320,"g"),("tomatenblokjes",400,"g")]),
 ("Turks","Turkse linzen met paprika en rijst","Vegetarisch",30,[("linzen",900,"g"),("paprika",4,"st"),("rijst",300,"g"),("tomatenblokjes",400,"g")]),
 ("Spaans","Spaanse kip met paprika en aardappeltjes","Kip",35,[("kipfilet",750,"g"),("paprika",4,"st"),("aardappel",850,"g"),("ui",200,"g")]),
 ("Spaans","Spaanse garnalen met tomaat en rijst","Vis",30,[("garnalen",700,"g"),("tomaten",800,"g"),("rijst",300,"g"),("spinazie",350,"g")]),
 ("Nederlands","Nederlandse varkenshaas met spruiten en krieltjes","Vlees",35,[("varkenshaas",750,"g"),("spruiten",1100,"g"),("aardappel",850,"g")]),
 ("Nederlands","Nederlandse kip met sperziebonen en aardappeltjes","Kip",35,[("kipfilet",700,"g"),("sperziebonen",1100,"g"),("aardappel",850,"g")]),
 ("Frans","Franse varkenshaas met champignons en aardappeltjes","Vlees",35,[("varkenshaas",750,"g"),("champignons",700,"g"),("aardappel",850,"g"),("wortel",500,"g")]),
 ("Frans","Franse zalm met sperziebonen en krieltjes","Vis",35,[("zalm",700,"g"),("sperziebonen",1100,"g"),("aardappel",850,"g")]),
 ("Mediterraan","Mediterrane tofu met aubergine en couscous","Vegetarisch",35,[("tofu",750,"g"),("aubergine",850,"g"),("couscous",320,"g"),("tomaten",450,"g")]),
 ("Mediterraan","Mediterrane kip met paprika en parelcouscous","Kip",35,[("kipdij",750,"g"),("paprika",4,"st"),("parelcouscous",320,"g"),("courgette",2,"st")]),
]

def expanded_variants():
    result=[]
    used=set()
    for cuisine,title,category,minutes,ingredients in DISHES:
        if title in used:raise ValueError("Dubbele maaltijdvariant: "+title)
        used.add(title)
        if not (0<minutes<=60) or len(ingredients)<3:raise ValueError("Onvolledig recept: "+title)
        if any(key not in ING or quantity<=0 or unit not in ("g","ml","st")
               for key,quantity,unit in ingredients):
            raise ValueError("Ongeldige ingrediënten: "+title)
        result.append((title,category,minutes,ingredients))
    return result

def cooking_steps(title,ingredients):
    keys={key for key,_,_ in ingredients}
    instructions=["Bereid alle ingrediënten volgens de vermelde hoeveelheden voor vier personen."]
    if "rijst" in keys:instructions.append("Kook de rijst volgens de verpakking.")
    if "pasta" in keys:instructions.append("Kook de pasta volgens de verpakking.")
    if "noedels" in keys:instructions.append("Kook de noedels volgens de verpakking.")
    if "bulgur" in keys or "couscous" in keys or "parelcouscous" in keys:
        instructions.append("Bereid de bulgur of couscous volgens de verpakking.")
    if "aardappel" in keys:instructions.append("Kook, bak of rooster de aardappeltjes tot ze gaar zijn.")
    if any(k in keys for k in ("kipfilet","kipdij","varkenshaas","gehakt","kipgehakt")):
        instructions.append("Bak het vlees volledig gaar en controleer de kerntemperatuur waar nodig.")
    if any(k in keys for k in ("zalm","garnalen","tonijn")):
        instructions.append("Bereid de vis of garnalen volledig en volgens de verpakkingsinstructie.")
    if any(k in keys for k in ("tofu","tempeh")):
        instructions.append("Bak de tofu of tempeh goudbruin.")
    instructions.append("Bereid de groenten beetgaar; voeg passende kruiden naar smaak toe. Serveer alles samen.")
    return " ".join(instructions)
