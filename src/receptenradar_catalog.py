"""Recepten en ingrediëntdefinities. Hoeveelheden gelden voor vier porties.

'Simpel' receptbestand: uitsluitend echt geprijsde kerningrediënten tellen voor de prijs.
Kruiden, olie en peper/zout gelden als optionele voorraad en staan apart op de site.
"""
import re

# Naam, zoekpatroon, uitgesloten woorden: conservatief, niet generiek fuzzy koppelen.
ING = {
 "havermout": ("havermout", r"(havermout|rolled oats)", r"reep|koek|drank|pap kant|ontbijtkoek|muesli"),
 "banaan": ("bananen", r"(bananen|banaan)", r"chips|smoothie|drank|smaak|puree|brood|melk|gedroog|toetje"),
 "blauwe_bessen": ("blauwe bessen", r"(blauwe bessen|blauwebessen|bosbessen)", r"jam|yoghurt|sap|smaak|muffin|muesli|drank|reep"),
 "aardbeien": ("aardbeien", r"(aardbeien|aardbei)", r"jam|yoghurt|sap|smaak|muffin|drank|reep"),
 "noten": ("ongezouten noten", r"(ongezouten noten|ongezouten amandelen|ongezouten walnoten)", r"pasta|reep|koek|chocolade|smaak"),
 "melk": ("halfvolle melk", r"(halfvolle melk|melk halfvol)", r"chocolade|drank smaak|poeder|lactosevrij"),
 "hummus": ("hummus naturel", r"(hummus|humus)", r"chips|wrap|salade|broodje|maaltijd|dipmix|kruiden"),
 "rookworst": ("rookworst", r"\brookworst\b", r"vegetar|vegan|plantaardig|soep|saus|chips|smaak|kruiden|broodbeleg|maaltijd|stamppot"),
 "varkenshaas": ("varkenshaas", r"varkenshaas", r"rollade|broodbeleg|gevuld|saus|maaltijd|reepjes|medaillon|vleeswaren|salade"),
 "kipfilet": ("kipfilet", r"\bkipfilet\b", r"vegetar|vegan|plantaardig|wortel|erwt|maaltijd|mix|salade|broodbeleg|soep|smaak|pizza|spread|pepersaus|roomsaus|saus|ragout|gepocheerd|gebakken"),
 "kipdij": ("kipdijfilet", r"kipdij(filet)?", r"vegetar|vegan|salade|broodbeleg|soep|smaak"),
 "kipgehakt": ("kipgehakt", r"\bkipgehakt\b", r"vegetar|vegan|gebraden|gekookt|beleg|worst|plantaardig"),
 "gehakt": ("rundergehakt", r"(rundergehakt|mager gehakt|half.om.half gehakt)", r"vegetar|vegan|kruiden|vervanger|gehaktbal"),
 "shoarma": ("kipshoarma", r"(kipshoarma|shoarmareepjes kip)", r"vegetar|vegan|saus|kruiden|pizza"),
 "zalm": ("zalmfilet", r"(verse zalmfilet|zalmfilet|diepvries zalmfilet)", r"gerookt|salade|broodbeleg|spread|hond|kat|saus"),
 "tonijn": ("tonijn in blik", r"(?:\btonijn(?:stukken|filets?|mootjes)?\b.{0,45}\b(?:blik|water|eigen nat|olijfolie|zonnebloemolie|olie|naturel)\b|\btonijnstukken\b)", r"salade|pizza|broodje|hond|kat|twist|diner|maaltijd|saus|spread|sushi|hamburger|kruidenmix"),
 "eieren": ("eieren", r"(vrije uitloop eieren|scharreleieren|scharrel eieren|biologische eieren|eieren maat|eieren [0-9])", r"chocolade|salade|koek"),
 "tofu": ("tofu", r"\btofu\b", r"saus|kruiden|soep"),
 "kikkererwten": ("kikkererwten", r"kikkererwten", r"chips|crackers|soep|falafel|saus|gedroog|droge|linzen|mix"),
 "linzen": ("linzen", r"\blinzen\b", r"chips|soep|gedroog|droge|kikkererwten|mix|noedel"),
 "bonen": ("zwarte bonen", r"(zwarte bonen|kidneybonen)", r"saus|soep|burgers|gedroog"),
 "rijst": ("zilvervliesrijst", r"(zilvervliesrijst|bruine rijst|volkorenrijst)", r"wafels|melk|drank|pudding|cracker|saus"),
 "risottorijst": ("risottorijst (Arborio of Carnaroli)", r"(risottorijst|risotto rijst|arborio|carnaroli|vialone nano|risotto rice|riso per risotti)", r"kant.en.klaar|maaltijd|saus|soep|risottomix|risotto mix|met kip|met champignons|mix voor"),
 "pasta": ("volkoren pasta", r"(volkoren (penne|pasta|spaghetti|fusilli|macaroni)|spaghetti volkoren|penne volkoren)", r"saus|maaltijd|kant.en.klaar"),
 "couscous": ("volkoren couscous", r"(volkoren couscous|couscous volkoren)", r"salade|maaltijd"),
 "wraps": ("volkoren wraps", r"(volkoren wraps|wraps volkoren|volkoren tortilla)", r"chips|kant.en.klaar|vulling"),
 "aardappel": ("aardappelen", r"(vastkokende aardapp|kruimige aardapp|aardappelen|krieltjes)", r"friet|chips|puree|salade|saus|gratin"),
 "zoete_aardappel": ("zoete aardappel", r"(zoete aardappel|bataat)", r"friet|chips|soep|puree|gratin|schotel|maaltijd"),
 "wok": ("wokgroenten", r"(wokgroenten|roerbakgroenten|wok groente)", r"maaltijd|saus|soep"),
 "boerenkool": ("boerenkool", r"\bboerenkool\b", r"soep|chips|quiche|stamppot|maaltijd|saus"),
 "spruiten": ("spruitjes", r"(spruitjes|spruiten)", r"saus|soep|stamppot|maaltijd|mix"),
 "gerookte_zalm": ("gerookte zalm", r"gerookte zalm", r"salade|saus|wraps|broodjes|spreads|rolletje|roomkaas|hapje|sushi|mousse"),
 "spinazie": ("spinazie", r"\bspinazie\b", r"pizza|saus|pasta|maaltijd|soep|smoothie|quiche|a la creme|a la cr.me|roomspinazie"),
 "broccoli": ("broccoli", r"\bbroccoli\b", r"soep|saus|maaltijd|mix|pizza|a la creme|a la cr.me|room|roomspinazie"),
 "bloemkool": ("bloemkool", r"\bbloemkool\b", r"soep|saus|rijst|pizza|mix|maaltijd"),
 "paprika": ("paprika", r"\bpaprika('s)?\b", r"poeder|chips|saus|soep|maaltijd|smaak|pasta|kruiden|tortilla|wrap|crackers|snack|salsa"),
 "courgette": ("courgette", r"\bcourgette\b", r"soep|saus|maaltijd|mix"),
 "champignons": ("champignons", r"(kastanjechampignons|champignons)", r"soep|saus|maaltijd|mix|wok|roerbakgroente|roerbakmix"),
 "tomaten": ("tomaten", r"(trostomaten|cherrytomaten|romatomaten|tomaten)", r"puree|saus|blokjes|blik|soep|ketchup|pasta|sap|zongedroogd|gepeld|gezeefd|passata|bonen|tomatens|tomatensap|pulp|polpa|ciliegini|conserven"),
 "olijven": ("zwarte olijven zonder pit", r"(zwarte olijven|olijven zwart|zwarte olijf|olijven zonder pit)", r"tapenade|olie|dip|saus|brood|pizza|mix"),
 "kappertjes": ("kappertjes", r"\\bkappertjes\\b", r"saus|dressing|tapenade|chips"),
 "tomatenblokjes": ("tomatenblokjes", r"(tomatenblokjes|tomaten in blokjes|tomaten pulp|tomatenpulp)", r"soep|saus|maaltijd"),
 "ui": ("uien", r"(gele uien|uien|rode uien|sjalotten)", r"saus|soep|kruiden|gebakken|poeder|snippers"),
 "komkommer": ("komkommer", r"\bkomkommer\b", r"zuur|saus|soep|salade|plakjes"),
 "wortel": ("wortelen", r"(winterpeen|bospeen|wortelen|worteltjes|waspeen)", r"soep|sap|salade|maaltijd"),
 "sla": ("slamelange", r"(slamelange|gemengde sla|ijsbergsla|veldsla|rucola)", r"maaltijd|saus|soep"),
 "avocado": ("avocado", r"\bavocado('s)?\b", r"olie|guacamole|saus|spread|maaltijd"),
 "mais": ("maïs", r"(mais|maïs)", r"chips|wafels|popcorn|meel|zetmeel|kippen|tortilla|soep"),
 "yoghurt": ("magere yoghurt", r"(magere yoghurt|griekse yoghurt|yoghurt griekse stijl|yoghurt mager|skyr yoghurt)", r"drank|saus|knijp|dessert|vla|pudding|10% vet|volle"),
 "kwark": ("magere kwark", r"(magere(?:\s+milde)?\s+kwark|kwark naturel|skyr(?:\s|$)|high protein kwark|proteinekwark|proteïnekwark)", r"drink|knijp|toetje|dessert|vla|pudding|cheesecake|mousse|roomkwark"),
 "kaas": ("geraspte kaas", r"(geraspte (oude|belegen|jong|kaas)|kaas geraspt)", r"pizza|maaltijd|saus"),
 "kokosmelk": ("kokosmelk", r"kokosmelk", r"drank|shampoo|haar|dessert|rijst"),
 "naan": ("naanbrood", r"(naanbrood|naan brood|naan)", r"pizza|maaltijd"),
}

# (titel, categorie, minuten, [(ingrediëntsleutel, hoeveelheid, eenheid), ...])
# Kernrecepten; kruiden, olie, zout en peper naar smaak uit eigen voorraad.
RECIPES = [
 ("Kip teriyaki met wokgroenten","Kip",25,[("kipfilet",600,"g"),("wok",800,"g"),("rijst",320,"g"),("ui",150,"g")]),
 ("Romige kip-spinaziepasta","Kip",30,[("kipfilet",600,"g"),("spinazie",500,"g"),("pasta",350,"g"),("yoghurt",250,"g")]),
 ("Kip-curry met bloemkool","Kip",35,[("kipfilet",600,"g"),("bloemkool",1,"st"),("kokosmelk",400,"ml"),("rijst",300,"g")]),
 ("Kip-avocadowraps","Kip",25,[("kipfilet",600,"g"),("wraps",8,"st"),("avocado",2,"st"),("sla",150,"g")]),
 ("Geroosterde kip met broccoli en krieltjes","Kip",40,[("kipdij",650,"g"),("broccoli",700,"g"),("aardappel",800,"g"),("yoghurt",200,"g")]),
 ("Kipshoarmabowl met frisse saus","Kip",25,[("shoarma",600,"g"),("rijst",320,"g"),("komkommer",1,"st"),("yoghurt",250,"g"),("sla",150,"g")]),
 ("Zoetzure kip met paprika en rijst","Kip",30,[("kipfilet",650,"g"),("paprika",3,"st"),("rijst",320,"g"),("tomatenblokjes",400,"g")]),
 ("Kip-kikkererwtencurry","Kip",30,[("kipdij",550,"g"),("kikkererwten",400,"g"),("spinazie",400,"g"),("kokosmelk",400,"ml")]),
 ("Kip-couscous met courgette","Kip",25,[("kipfilet",600,"g"),("couscous",300,"g"),("courgette",2,"st"),("tomaten",400,"g")]),
 ("Kipwraps met bonensalsa","Kip",25,[("kipgehakt",600,"g"),("wraps",8,"st"),("bonen",400,"g"),("tomaten",350,"g")]),
 ("Kipfrittata met spinazie","Kip",35,[("kipfilet",400,"g"),("eieren",8,"st"),("spinazie",450,"g"),("tomaten",300,"g")]),
 ("Kipgehaktballetjes met tomatensaus","Kip",35,[("kipgehakt",600,"g"),("tomatenblokjes",800,"g"),("pasta",320,"g"),("champignons",400,"g")]),
 ("Mediterrane kip-traybake","Kip",40,[("kipdij",650,"g"),("courgette",2,"st"),("paprika",3,"st"),("aardappel",800,"g")]),
 ("Mexicaanse rijstpan met kip","Kip",30,[("kipfilet",600,"g"),("bonen",400,"g"),("mais",250,"g"),("rijst",300,"g"),("tomatenblokjes",400,"g")]),
 ("Kip in romige champignonsaus","Kip",30,[("kipfilet",650,"g"),("champignons",500,"g"),("aardappel",900,"g"),("yoghurt",250,"g")]),
 ("Zalm met broccoli en krieltjes","Vis",35,[("zalm",600,"g"),("broccoli",700,"g"),("aardappel",800,"g"),("yoghurt",200,"g")]),
 ("Zalm-spinaziepasta","Vis",25,[("zalm",500,"g"),("spinazie",450,"g"),("pasta",320,"g"),("yoghurt",250,"g")]),
 ("Zalmrijstbowl met komkommer","Vis",25,[("zalm",600,"g"),("rijst",320,"g"),("komkommer",1,"st"),("avocado",2,"st")]),
 ("Zalm uit de oven met bloemkool","Vis",35,[("zalm",600,"g"),("bloemkool",1,"st"),("zoete_aardappel",750,"g"),("yoghurt",200,"g")]),
 ("Tonijn-wraps met bonen","Vis",20,[("tonijn",320,"g"),("bonen",400,"g"),("wraps",8,"st"),("sla",200,"g")]),
 ("Tonijnpastasalade","Vis",20,[("tonijn",320,"g"),("pasta",320,"g"),("komkommer",1,"st"),("tomaten",400,"g"),("yoghurt",250,"g")]),
 ("Mediterrane tonijnrijst","Vis",25,[("tonijn",320,"g"),("rijst",320,"g"),("paprika",2,"st"),("tomaten",400,"g")]),
 ("Tonijn-zoeteaardappelschotel","Vis",40,[("tonijn",320,"g"),("zoete_aardappel",850,"g"),("spinazie",450,"g"),("kaas",150,"g")]),
 # Vierpersoonsvariant gebaseerd op een daadwerkelijk bestaand Allerhande-recept.
 # Volkoren pasta, tonijngewicht en tomatenblokjes zijn bewust gekozen
 # varianten; originele bron blijft zichtbaar op de receptenkaart.
 ("Volkoren tonijnpasta met zwarte olijven en kappertjes","Vis",25,[
   ("tonijn",480,"g"),("pasta",320,"g"),("courgette",2,"st"),
   ("tomatenblokjes",400,"g"),("ui",150,"g"),("olijven",100,"g"),("kappertjes",35,"g")]),
 # Nieuwe gevarieerde tonijnrecepten; alle vier porties, prijzen pas na exacte productmatch.
 ("Tonijn-broccolipasta met tomatensaus","Vis",25,[("tonijn",500,"g"),("broccoli",700,"g"),("pasta",320,"g"),("tomatenblokjes",800,"g")]),
 ("Tonijn-paprikafrittata met spinazie","Vis",30,[("tonijn",450,"g"),("eieren",8,"st"),("paprika",3,"st"),("spinazie",500,"g")]),
 ("Mexicaans geïnspireerde tonijn-bonenbowl","Vis",25,[("tonijn",450,"g"),("bonen",550,"g"),("mais",250,"g"),("tomaten",400,"g"),("rijst",260,"g")]),
 ("Tonijn-kikkererwtensalade met komkommer","Vis",15,[("tonijn",500,"g"),("kikkererwten",600,"g"),("komkommer",2,"st"),("tomaten",400,"g")]),
 ("Tonijn-courgette-ovenschotel","Vis",35,[("tonijn",500,"g"),("courgette",3,"st"),("tomatenblokjes",800,"g"),("kaas",180,"g")]),
 ("Tonijnrijstschotel met broccoli","Vis",30,[("tonijn",500,"g"),("rijst",300,"g"),("broccoli",700,"g"),("tomatenblokjes",400,"g")]),
 ("Tonijn-avocadosalade met eieren","Vis",20,[("tonijn",450,"g"),("avocado",2,"st"),("eieren",8,"st"),("sla",250,"g"),("komkommer",1,"st")]),
 ("Pittige tonijnwraps met mais en paprika","Vis",20,[("tonijn",500,"g"),("wraps",8,"st"),("mais",250,"g"),("paprika",2,"st"),("sla",200,"g")]),
 ("Tonijn-aardappelsalade met yoghurtdressing","Vis",30,[("tonijn",500,"g"),("aardappel",750,"g"),("yoghurt",300,"g"),("komkommer",2,"st"),("sla",200,"g")]),
 ("Mediterrane tonijn-kikkererwtenbowl","Vis",20,[("tonijn",500,"g"),("kikkererwten",600,"g"),("tomaten",450,"g"),("komkommer",1,"st"),("spinazie",350,"g")]),
 ("Tonijncouscous met gegrilde courgette","Vis",25,[("tonijn",500,"g"),("couscous",320,"g"),("courgette",2,"st"),("paprika",2,"st")]),
 ("Tonijn-tomatenstoof met bonen","Vis",25,[("tonijn",500,"g"),("tomatenblokjes",800,"g"),("bonen",600,"g"),("spinazie",500,"g")]),
 ("Tonijn-spinaziepasta met frisse yoghurtsaus","Vis",25,[("tonijn",500,"g"),("spinazie",500,"g"),("pasta",320,"g"),("yoghurt",250,"g")]),
 ("Tonijn-broccoli-aardappelovenschotel","Vis",40,[("tonijn",500,"g"),("broccoli",700,"g"),("aardappel",850,"g"),("yoghurt",250,"g")]),
 ("Gevulde paprika met tonijn, rijst en bonen","Vis",35,[("tonijn",500,"g"),("paprika",4,"st"),("rijst",280,"g"),("bonen",450,"g"),("tomatenblokjes",400,"g")]),
 ("Tonijn-bonensalade met spinazie en tomaat","Vis",15,[("tonijn",500,"g"),("bonen",600,"g"),("spinazie",350,"g"),("tomaten",450,"g")]),
 ("Gehaktballetjes met volkorenpasta","Vlees",35,[("gehakt",600,"g"),("pasta",320,"g"),("tomatenblokjes",800,"g"),("courgette",2,"st")]),
 ("Mexicaanse gehaktbowl","Vlees",30,[("gehakt",600,"g"),("rijst",320,"g"),("bonen",400,"g"),("mais",250,"g"),("sla",150,"g")]),
 ("Gevulde paprika met gehakt","Vlees",40,[("gehakt",600,"g"),("paprika",4,"st"),("rijst",250,"g"),("tomatenblokjes",400,"g")]),
 ("Gehakt-zoeteaardappelschotel","Vlees",40,[("gehakt",600,"g"),("zoete_aardappel",800,"g"),("broccoli",600,"g"),("kaas",150,"g")]),
 ("Italiaanse gehakt-wokpan","Vlees",30,[("gehakt",600,"g"),("wok",750,"g"),("tomatenblokjes",400,"g"),("pasta",320,"g")]),
 ("Gehaktwraps met avocado","Vlees",25,[("gehakt",600,"g"),("wraps",8,"st"),("avocado",2,"st"),("tomaten",400,"g")]),
 ("Gehaktstoof met kikkererwten","Vlees",35,[("gehakt",500,"g"),("kikkererwten",400,"g"),("tomatenblokjes",800,"g"),("spinazie",400,"g")]),
 ("Ovenschotel met gehakt en bloemkool","Vlees",40,[("gehakt",600,"g"),("bloemkool",1,"st"),("aardappel",750,"g"),("kaas",150,"g")]),
 ("Kikkererwtencurry met spinazie","Vegetarisch",30,[("kikkererwten",650,"g"),("spinazie",500,"g"),("kokosmelk",400,"ml"),("rijst",300,"g")]),
 ("Tofuwok met wokgroenten","Vegetarisch",25,[("tofu",600,"g"),("wok",800,"g"),("rijst",320,"g")]),
 ("Shakshuka met bonen","Vegetarisch",30,[("eieren",8,"st"),("tomatenblokjes",800,"g"),("bonen",400,"g"),("paprika",2,"st")]),
 ("Linzen-bolognese met groenten","Vegetarisch",35,[("linzen",500,"g"),("tomatenblokjes",800,"g"),("champignons",450,"g"),("pasta",320,"g")]),
 ("Vegetarische burritobowl","Vegetarisch",25,[("bonen",600,"g"),("mais",300,"g"),("rijst",320,"g"),("avocado",2,"st")]),
 ("Bloemkool-kikkererwten traybake","Vegetarisch",40,[("bloemkool",1,"st"),("kikkererwten",600,"g"),("zoete_aardappel",750,"g"),("yoghurt",250,"g")]),
 ("Groentefrittata met kaas","Vegetarisch",30,[("eieren",8,"st"),("spinazie",450,"g"),("champignons",350,"g"),("kaas",150,"g")]),
 ("Couscoussalade met kikkererwten","Vegetarisch",25,[("couscous",300,"g"),("kikkererwten",600,"g"),("komkommer",1,"st"),("tomaten",450,"g")]),
 ("Tofu-kokoscurry","Vegetarisch",30,[("tofu",600,"g"),("kokosmelk",400,"ml"),("wok",800,"g"),("rijst",300,"g")]),
 ("Groentelasagne zonder lasagnebladen","Vegetarisch",40,[("courgette",3,"st"),("linzen",500,"g"),("tomatenblokjes",800,"g"),("kaas",200,"g")]),
 ("Wraps met ei, avocado en sla","Vegetarisch",20,[("eieren",8,"st"),("wraps",8,"st"),("avocado",2,"st"),("sla",150,"g")]),
 ("Broccoli-kikkererwtenpasta","Vegetarisch",25,[("broccoli",700,"g"),("kikkererwten",500,"g"),("pasta",320,"g"),("yoghurt",200,"g")]),
 ("Spinazie-linzenstoof","Vegetarisch",30,[("spinazie",500,"g"),("linzen",600,"g"),("tomatenblokjes",800,"g"),("naan",4,"st")]),
 ("Tortilla-avond met bonen en kaas","Vegetarisch",25,[("wraps",8,"st"),("bonen",600,"g"),("kaas",180,"g"),("tomaten",400,"g")]),
 ("Geroosterde groentebowl met kikkererwten","Vegetarisch",40,[("kikkererwten",700,"g"),("courgette",2,"st"),("paprika",3,"st"),("couscous",300,"g")]),
 ("Kipfilet met spinazie en krieltjes","Kip",30,[("kipfilet",650,"g"),("spinazie",450,"g"),("aardappel",800,"g"),("yoghurt",200,"g")]),
 ("Kruidige kip met spruitjes en aardappelen","Kip",35,[("kipfilet",650,"g"),("spruiten",750,"g"),("aardappel",800,"g")]),
 ("Zalm-spinazie wraps met yoghurtsaus","Vis",20,[("gerookte_zalm",200,"g"),("spinazie",450,"g"),("wraps",8,"st"),("yoghurt",300,"g")]),
 ("Zalmfrittata met spinazie","Vis",30,[("gerookte_zalm",200,"g"),("spinazie",450,"g"),("eieren",8,"st"),("aardappel",650,"g")]),
 ("Spruitjes-roerbak met kip en rijst","Kip",30,[("kipfilet",650,"g"),("spruiten",750,"g"),("rijst",320,"g")]),
 ("Spruitjesplaat met zalm en aardappel","Vis",40,[("zalm",600,"g"),("spruiten",750,"g"),("aardappel",750,"g")]),
 ("Spinazie-ei wraps","Vegetarisch",25,[("spinazie",450,"g"),("eieren",8,"st"),("wraps",8,"st"),("yoghurt",250,"g")]),
 ("Gevulde zoete aardappel met zwarte bonen","Vegetarisch",40,[("zoete_aardappel",900,"g"),("bonen",600,"g"),("tomaten",400,"g"),("yoghurt",250,"g")]),
 ("Boerenkoolstamppot met rundergehakt","Vlees",35,[("boerenkool",600,"g"),("aardappel",900,"g"),("gehakt",600,"g"),("ui",200,"g")]),
 ("Kruidige kip met boerenkool en zoete aardappel","Kip",35,[("boerenkool",600,"g"),("kipfilet",650,"g"),("zoete_aardappel",800,"g"),("yoghurt",200,"g")]),
 ("Boerenkool-shakshuka met eieren en bonen","Vegetarisch",30,[("boerenkool",600,"g"),("eieren",8,"st"),("bonen",400,"g"),("tomatenblokjes",800,"g")]),
 ("Boerenkool-linzencurry met kokos","Vegetarisch",30,[("boerenkool",600,"g"),("linzen",500,"g"),("kokosmelk",400,"ml"),("rijst",300,"g")]),
 ("Italiaans geïnspireerde boerenkoolpasta met kipgehakt","Kip",30,[("boerenkool",600,"g"),("kipgehakt",600,"g"),("pasta",320,"g"),("tomatenblokjes",400,"g")]),
 ("Boerenkoolfrittata met champignons","Vegetarisch",30,[("boerenkool",450,"g"),("eieren",8,"st"),("champignons",450,"g"),("kaas",150,"g")]),
 ("Koreaanse kip met broccoli en zilvervliesrijst","Kip",35,[("kipdij",650,"g"),("broccoli",700,"g"),("rijst",300,"g"),("ui",200,"g")]),
 ("Gekruid rundergehakt met wokgroenten","Vlees",25,[("gehakt",600,"g"),("wok",800,"g"),("rijst",300,"g"),("ui",200,"g")]),
 ("Vis met knoflook-kruidenyoghurt en broccoli","Vis",30,[("zalm",600,"g"),("broccoli",700,"g"),("aardappel",850,"g"),("yoghurt",200,"g")]),
 ("Kruidige harissa-kipwraps met rauwkost","Kip",25,[("kipdij",600,"g"),("wraps",8,"st"),("sla",200,"g"),("komkommer",1,"st"),("yoghurt",200,"g")]),
 ("Indonesische kipkokoscurry met groene groenten","Kip",35,[("kipdij",650,"g"),("wok",800,"g"),("kokosmelk",400,"ml"),("rijst",250,"g")]),

 ("HelloFresh-geïnspireerd: volkorenpasta met champignons","Vegetarisch",30,[("pasta",320,"g"),("champignons",500,"g"),("courgette",2,"st"),("kaas",150,"g")]),
 ("HelloFresh-geïnspireerd: groentecouscous met courgette","Vegetarisch",25,[("couscous",320,"g"),("courgette",2,"st"),("tomaten",400,"g"),("paprika",2,"st")]),
 ("HelloFresh-geïnspireerd: stamppot met wokgroenten en kaas","Vegetarisch",35,[("aardappel",1000,"g"),("wok",750,"g"),("ui",200,"g"),("kaas",150,"g")]),
 ("HelloFresh-geïnspireerd: courgette-kikkererwtenbowl met yoghurt","Vegetarisch",40,[("courgette",2,"st"),("kikkererwten",600,"g"),("couscous",320,"g"),("yoghurt",250,"g")]),
 ("HelloFresh-geïnspireerd: kikkererwtencurry met zoete aardappel","Vegetarisch",35,[("kikkererwten",600,"g"),("zoete_aardappel",800,"g"),("kokosmelk",400,"ml"),("spinazie",450,"g")]),
 ("HelloFresh-geïnspireerd: frisse kipcouscous met wortel en spinazie","Kip",30,[("kipfilet",650,"g"),("couscous",320,"g"),("wortel",450,"g"),("spinazie",250,"g")]),
 ("HelloFresh-geïnspireerd: gekruide kikkererwten met geroosterde groenten","Vegetarisch",35,[("kikkererwten",700,"g"),("courgette",2,"st"),("wortel",450,"g"),("couscous",320,"g")]),
 ("HelloFresh-geïnspireerd: rundergehakt met champignons en krieltjes","Vlees",35,[("gehakt",650,"g"),("aardappel",900,"g"),("champignons",400,"g"),("sla",150,"g")]),
 ("HelloFresh-geïnspireerd: pokébowl met tofu en avocado","Vegetarisch",25,[("tofu",600,"g"),("rijst",320,"g"),("avocado",2,"st"),("komkommer",1,"st")]),
 ("HelloFresh-geïnspireerd: kruidige gehaktreepjes met wokgroenten","Vlees",30,[("gehakt",600,"g"),("wok",800,"g"),("rijst",320,"g"),("ui",200,"g")]),
 ("HelloFresh-geïnspireerd: Koreaanse kip met broccoli","Kip",30,[("kipdij",650,"g"),("broccoli",700,"g"),("rijst",320,"g"),("wortel",300,"g")]),
 ("HelloFresh-geïnspireerd: zalm met knoflookyoghurt en wokgroenten","Vis",35,[("zalm",600,"g"),("wok",700,"g"),("aardappel",900,"g"),("yoghurt",200,"g")]),
 ("HelloFresh-geïnspireerd: rundergehakt met zoete aardappel en spruitjes","Vlees",35,[("gehakt",600,"g"),("zoete_aardappel",850,"g"),("spruiten",650,"g"),("ui",200,"g")]),
 ("HelloFresh-geïnspireerd: romige visstoof met krieltjes","Vis",35,[("zalm",600,"g"),("aardappel",900,"g"),("wortel",400,"g"),("yoghurt",250,"g")]),
 ("HelloFresh-geïnspireerd: vegetarische couscousbowl met kikkererwten","Vegetarisch",25,[("kikkererwten",650,"g"),("couscous",320,"g"),("courgette",2,"st"),("tomaten",400,"g")]),
 ("HelloFresh-geïnspireerd: champignonrisotto met kipgehakt","Kip",40,[("kipgehakt",650,"g"),("risottorijst",180,"g"),("champignons",700,"g"),("spinazie",400,"g"),("ui",150,"g"),("kaas",100,"g")]),
 ("HelloFresh-geïnspireerd: volkorenpasta-ovenschotel met geraspte kaas","Vegetarisch",35,[("pasta",350,"g"),("courgette",2,"st"),("tomatenblokjes",800,"g"),("kaas",200,"g")]),
 ("HelloFresh-geïnspireerd: köfte-gehaktballetjes in kokos-currysaus","Vlees",30,[("gehakt",650,"g"),("kokosmelk",400,"ml"),("rijst",320,"g"),("wok",700,"g")]),
 ("HelloFresh-geïnspireerd: volkorenpastaroerbak met gehakt en wokgroenten","Vlees",25,[("gehakt",650,"g"),("wok",800,"g"),("pasta",320,"g"),("paprika",2,"st")]),
 ("HelloFresh-geïnspireerd: gepofte kikkererwten en wittekaascouscous","Vegetarisch",35,[("kikkererwten",650,"g"),("couscous",320,"g"),("paprika",2,"st"),("kaas",150,"g")]),
 ("HelloFresh-geïnspireerd: rundergehakt met zwarte bonen en rijst","Vlees",25,[("gehakt",600,"g"),("bonen",500,"g"),("rijst",320,"g"),("komkommer",1,"st")]),
 ("HelloFresh-geïnspireerd: tofubowl met broccoli","Vegetarisch",30,[("tofu",650,"g"),("broccoli",700,"g"),("rijst",320,"g"),("wortel",350,"g")]),
 ("Mealprep: chipotle kipbowl met zwarte bonen","Kip",30,[("kipfilet",650,"g"),("bonen",500,"g"),("rijst",320,"g"),("paprika",3,"st")]),
 ("Mealprep: mediterrane kipwraps met yoghurt","Kip",25,[("kipfilet",600,"g"),("wraps",8,"st"),("sla",200,"g"),("komkommer",1,"st"),("yoghurt",250,"g")]),
 ("Mealprep: romige limoenstijl kipbowl","Kip",30,[("kipdij",650,"g"),("rijst",320,"g"),("yoghurt",250,"g"),("wok",800,"g")]),
 ("Mealprep: pittige gehaktroerbak met volkorenpasta","Vlees",30,[("gehakt",650,"g"),("wok",800,"g"),("pasta",320,"g"),("ui",150,"g")]),
 ("Mealprep: teriyaki kip uit de oven met groenten","Kip",40,[("kipfilet",650,"g"),("broccoli",650,"g"),("wortel",350,"g"),("rijst",300,"g")]),
 ("Mealprep: kaneelpaprika-kip met zoete aardappel","Kip",40,[("kipdij",650,"g"),("zoete_aardappel",900,"g"),("broccoli",650,"g"),("yoghurt",250,"g")]),
 ("Mealprep: geroosterde groentencouscous met kikkererwten","Vegetarisch",40,[("couscous",320,"g"),("kikkererwten",600,"g"),("courgette",2,"st"),("paprika",3,"st")]),
 ("Mealprep: tofu-kokosrijst met spinazie","Vegetarisch",30,[("tofu",600,"g"),("spinazie",450,"g"),("kokosmelk",400,"ml"),("rijst",320,"g")]),
 ("Varkenshaas met gebakken minikrieltjes en bloemkool","Vlees",35,[("varkenshaas",800,"g"),("aardappel",1100,"g"),("bloemkool",1,"st")]),
 ("Varkenshaas met wokgroenten en aardappeltjes","Vlees",35,[("varkenshaas",800,"g"),("wok",800,"g"),("aardappel",1100,"g")]),
 ("Varkenshaas met bloemkool en champignons","Vlees",35,[("varkenshaas",800,"g"),("bloemkool",1,"st"),("champignons",400,"g"),("aardappel",900,"g")]),
 ("Varkenshaas met spruitjes en krieltjes","Vlees",35,[("varkenshaas",800,"g"),("spruiten",750,"g"),("aardappel",1000,"g")]),
 ("Varkenshaas met gebakken broccoli en aardappelschijfjes","Vlees",35,[("varkenshaas",800,"g"),("broccoli",700,"g"),("aardappel",1100,"g")]),
 ("Varkenshaas met spinazie en krieltjes","Vlees",35,[("varkenshaas",800,"g"),("spinazie",750,"g"),("aardappel",1100,"g")]),
 ("Ontbijt: skyr met havermout, banaan en blauwe bessen","Vegetarisch",5,[("kwark",1400,"g"),("havermout",160,"g"),("banaan",480,"g"),("blauwe_bessen",300,"g")]),
 ("Ontbijt: overnight oats met kwark en blauwe bessen","Vegetarisch",10,[("kwark",1200,"g"),("havermout",200,"g"),("blauwe_bessen",400,"g"),("melk",250,"ml")]),
 ("Ontbijt: kwarkbowl met aardbeien, banaan en noten","Vegetarisch",5,[("kwark",1400,"g"),("aardbeien",400,"g"),("banaan",360,"g"),("noten",80,"g")]),
 ("Ontbijt: warme havermout met kwark en banaan","Vegetarisch",10,[("kwark",1400,"g"),("havermout",180,"g"),("banaan",480,"g"),("melk",250,"ml")]),
 ("Ontbijt: skyr met blauwe bessen en ongezouten noten","Vegetarisch",5,[("kwark",1400,"g"),("blauwe_bessen",480,"g"),("noten",100,"g")]),
 ("Ontbijt: ei-muffins met spinazie en kwark","Vegetarisch",20,[("eieren",10,"st"),("spinazie",500,"g"),("kwark",1000,"g"),("paprika",2,"st")]),
 ("Lunch: Aziatische kip-buddhabowl met broccoli","Kip",20,[("kipfilet",800,"g"),("broccoli",800,"g"),("wortel",300,"g"),("rijst",140,"g")]),
 ("Lunch: Koreaanse kip-slabowl met komkommer","Kip",20,[("kipfilet",800,"g"),("sla",400,"g"),("komkommer",2,"st"),("wortel",400,"g")]),
 ("Lunch: frisse Thaise kipwrap met veel groenten","Kip",20,[("kipfilet",800,"g"),("wraps",4,"st"),("wok",600,"g"),("komkommer",1,"st"),("yoghurt",300,"g")]),
 ("Lunch: Mexicaanse kip-bonenbowl","Kip",20,[("kipfilet",700,"g"),("bonen",400,"g"),("paprika",3,"st"),("tomaten",500,"g"),("sla",350,"g")]),
 ("Lunch: Costa Ricaanse gallo pinto bowl met ei","Vegetarisch",20,[("bonen",800,"g"),("rijst",160,"g"),("eieren",8,"st"),("paprika",3,"st"),("tomaten",450,"g")]),
 ("Lunch: Zuid-Amerikaanse kip-avocadobowl","Kip",20,[("kipfilet",800,"g"),("avocado",2,"st"),("sla",500,"g"),("tomaten",450,"g"),("komkommer",1,"st")]),
 ("Lunch: Japanse tofu-buddhabowl met broccoli","Vegetarisch",20,[("tofu",1000,"g"),("broccoli",800,"g"),("wortel",350,"g"),("rijst",140,"g")]),
 ("Lunch: Aziatische tofu-slabowl met paprika","Vegetarisch",15,[("tofu",1000,"g"),("sla",450,"g"),("paprika",3,"st"),("komkommer",2,"st")]),
 ("Lunch: Mediterrane kip-hummus saladebowl","Kip",15,[("kipfilet",800,"g"),("hummus",240,"g"),("sla",450,"g"),("komkommer",2,"st"),("tomaten",450,"g")]),
 ("Lunch: Mexicaanse gehakt-bonenbowl","Vlees",20,[("gehakt",650,"g"),("bonen",500,"g"),("paprika",3,"st"),("tomaten",500,"g")]),
 ("Lunch: ei- en kikkererwtensalade met frisse groenten","Vegetarisch",15,[("eieren",8,"st"),("kikkererwten",700,"g"),("sla",450,"g"),("komkommer",2,"st"),("yoghurt",300,"g")]),
 ("Lunch: volkoren kipwrap met spinazie en avocado","Kip",15,[("kipfilet",800,"g"),("wraps",4,"st"),("spinazie",400,"g"),("avocado",2,"st"),("yoghurt",250,"g")]),
 ("Lunch: buddhabowl met tofu en bonen","Vegetarisch",20,[("tofu",850,"g"),("bonen",400,"g"),("wok",800,"g"),("wortel",350,"g")]),
 ("Lunch: kip Caesar-stijl wrap met yoghurt en knapperige sla","Kip",15,[("wraps",4,"st"),("kipfilet",800,"g"),("sla",500,"g"),("komkommer",2,"st"),("yoghurt",250,"g")]),
 ("Lunch: kip-avocado wrap met tomaat en spinazie","Kip",15,[("wraps",4,"st"),("kipfilet",800,"g"),("avocado",2,"st"),("tomaten",500,"g"),("spinazie",250,"g")]),
 ("Lunch: kip-hummus wrap met wortel en komkommer","Kip",15,[("wraps",4,"st"),("kipfilet",800,"g"),("hummus",250,"g"),("wortel",400,"g"),("komkommer",2,"st")]),
 ("Lunch: kip-fajita wrap met paprika en zwarte bonen","Kip",20,[("wraps",4,"st"),("kipfilet",700,"g"),("paprika",3,"st"),("bonen",400,"g"),("sla",300,"g")]),
 ("Lunch: koude kipwrap met wokgroenten en yoghurtdressing","Kip",20,[("wraps",4,"st"),("kipfilet",800,"g"),("wok",650,"g"),("komkommer",1,"st"),("yoghurt",250,"g")]),
 ("Lunch: kipgehakt-tomatensalsa wrap met ijsbergsla","Kip",20,[("wraps",4,"st"),("kipgehakt",800,"g"),("tomaten",650,"g"),("sla",400,"g"),("yoghurt",200,"g")]),
 ("Lunch: kipshoarma wrap met frisse yoghurtsaus","Kip",15,[("wraps",4,"st"),("shoarma",800,"g"),("sla",500,"g"),("komkommer",2,"st"),("yoghurt",250,"g")]),
 ("Lunch: kipwrap met champignons, paprika en spinazie","Kip",20,[("wraps",4,"st"),("kipfilet",800,"g"),("champignons",450,"g"),("paprika",3,"st"),("spinazie",250,"g")]),
 ("Lunch: tonijnwrap met hummus, komkommer en sla","Vis",10,[("wraps",4,"st"),("tonijn",600,"g"),("hummus",220,"g"),("komkommer",2,"st"),("sla",450,"g")]),
 ("Lunch: tonijn-bonenwrap met tomaat en spinazie","Vis",10,[("wraps",4,"st"),("tonijn",500,"g"),("bonen",450,"g"),("tomaten",500,"g"),("spinazie",280,"g")]),
 ("Lunch: tonijnwrap met avocado en frisse yoghurtdressing","Vis",10,[("wraps",4,"st"),("tonijn",600,"g"),("avocado",2,"st"),("komkommer",2,"st"),("yoghurt",250,"g")]),
 ("Lunch: gerookte-zalmwrap met spinazie en frisse kwark","Vis",10,[("wraps",4,"st"),("gerookte_zalm",500,"g"),("spinazie",400,"g"),("kwark",550,"g"),("komkommer",1,"st")]),
 ("Lunch: zalmwrap met komkommer en yoghurtsaus","Vis",20,[("wraps",4,"st"),("zalm",750,"g"),("komkommer",2,"st"),("sla",450,"g"),("yoghurt",250,"g")]),
 ("Lunch: ei-hummuswrap met sla en tomaat","Vegetarisch",15,[("wraps",4,"st"),("eieren",12,"st"),("hummus",320,"g"),("sla",450,"g"),("tomaten",500,"g")]),
 ("Lunch: ei-avocadowrap met spinazie en kwark","Vegetarisch",15,[("wraps",4,"st"),("eieren",10,"st"),("avocado",2,"st"),("spinazie",450,"g"),("kwark",450,"g")]),
 ("Lunch: tofu-wrap met komkommer, wortel en pittige kruiden","Vegetarisch",20,[("wraps",4,"st"),("tofu",1000,"g"),("komkommer",2,"st"),("wortel",500,"g"),("yoghurt",250,"g")]),
 ("Lunch: tofu-avocadowrap met paprika en sla","Vegetarisch",15,[("wraps",4,"st"),("tofu",1000,"g"),("avocado",2,"st"),("paprika",3,"st"),("sla",400,"g")]),
 ("Lunch: Mexicaanse bonenwrap met ei en frisse salsa","Vegetarisch",15,[("wraps",4,"st"),("bonen",700,"g"),("eieren",8,"st"),("tomaten",550,"g"),("paprika",3,"st")]),
 ("Lunch: kikkererwten-hummuswrap met komkommer en wortel","Vegetarisch",15,[("wraps",4,"st"),("kikkererwten",700,"g"),("hummus",250,"g"),("komkommer",2,"st"),("wortel",400,"g")]),
 ("Lunch: warme tofu-champignonwrap met spinazie","Vegetarisch",20,[("wraps",4,"st"),("tofu",1000,"g"),("champignons",500,"g"),("spinazie",500,"g"),("yoghurt",250,"g")]),
 ("Lunch: Italiaanse wrap met kip, tomaat en yoghurtdressing","Kip",15,[("wraps",4,"st"),("kipfilet",800,"g"),("tomaten",650,"g"),("sla",350,"g"),("yoghurt",200,"g")]),
 ("Lunch: kruidige kipwrap met courgette en spinazie","Kip",20,[("wraps",4,"st"),("kipfilet",800,"g"),("courgette",2,"st"),("spinazie",400,"g"),("yoghurt",200,"g")]),
 ("Lunch: mediterrane wrap met tofu, hummus en tomaat","Vegetarisch",15,[("wraps",4,"st"),("tofu",1000,"g"),("hummus",280,"g"),("tomaten",600,"g"),("komkommer",1,"st")]),
 ("Lunch: rundergehaktwrap met tomaten, paprika en sla","Vlees",20,[("wraps",4,"st"),("gehakt",600,"g"),("paprika",3,"st"),("tomaten",550,"g"),("sla",350,"g")]),
 ("Lunch: zoeteaardappelwrap met bonen, spinazie en ei","Vegetarisch",20,[("wraps",4,"st"),("zoete_aardappel",400,"g"),("bonen",600,"g"),("eieren",8,"st"),("spinazie",400,"g")]),
 ("Lunch: koude kip-yoghurtwrap met wortel en paprika","Kip",15,[("wraps",4,"st"),("kipfilet",800,"g"),("wortel",550,"g"),("paprika",3,"st"),("yoghurt",320,"g")]),
 ("Lunch: gerookte-zalmwrap met avocado en komkommer","Vis",10,[("wraps",4,"st"),("gerookte_zalm",500,"g"),("avocado",2,"st"),("komkommer",2,"st"),("kwark",450,"g")]),
 ("Lunch: roereiwrap met champignons en spinazie","Vegetarisch",15,[("wraps",4,"st"),("eieren",12,"st"),("champignons",550,"g"),("spinazie",450,"g"),("kwark",350,"g")]),
 ("Lunch: kip-bonenwrap met maïs en frisse salade","Kip",20,[("wraps",4,"st"),("kipfilet",750,"g"),("bonen",400,"g"),("mais",200,"g"),("sla",450,"g")]),
 ("Lunch: tonijnwrap met rode paprika en frisse kwark","Vis",10,[("wraps",4,"st"),("tonijn",650,"g"),("paprika",3,"st"),("kwark",450,"g"),("sla",350,"g")]),
 ("Lunch: kruidige tofuwrap met kikkererwten en komkommer","Vegetarisch",20,[("wraps",4,"st"),("tofu",800,"g"),("kikkererwten",400,"g"),("komkommer",2,"st"),("tomaten",400,"g")]),
 ("Lunch: kip-zwartebonensalade om koud mee te nemen","Kip",15,[("kipfilet",800,"g"),("bonen",500,"g"),("komkommer",2,"st"),("tomaten",650,"g")]),
 ("Lunch: tonijnsalade met ei en tomaat, zonder brood","Vis",15,[("tonijn",600,"g"),("eieren",8,"st"),("tomaten",700,"g"),("sla",450,"g"),("yoghurt",250,"g")]),
 ("Lunch: tofu-roerbak met bloemkool en paprika om voor te bereiden","Vegetarisch",20,[("tofu",1000,"g"),("bloemkool",1,"st"),("paprika",3,"st"),("wortel",400,"g")]),
 ("Lunch: linzen- en eiersalade met geroosterde paprika","Vegetarisch",20,[("linzen",800,"g"),("eieren",8,"st"),("paprika",3,"st"),("tomaten",450,"g")]),
 ("Ontbijt: overnight oats met aardbeien en skyr","Vegetarisch",10,[("kwark",1400,"g"),("havermout",160,"g"),("aardbeien",450,"g"),("melk",200,"ml")]),
 ("Ontbijt: skyr met banaan, havermout en noten","Vegetarisch",5,[("kwark",1400,"g"),("havermout",150,"g"),("banaan",480,"g"),("noten",80,"g")]),
 ("Ontbijt: kwark met blauwe bessen en aardbeien","Vegetarisch",5,[("kwark",1600,"g"),("blauwe_bessen",350,"g"),("aardbeien",450,"g")]),
 ("Ontbijt: hartige eiwrap met spinazie","Vegetarisch",15,[("eieren",12,"st"),("wraps",4,"st"),("spinazie",450,"g"),("kwark",650,"g")]),
 ("Ontbijt: kwark met havermout, banaan en aardbeien","Vegetarisch",5,[("kwark",1400,"g"),("havermout",160,"g"),("banaan",360,"g"),("aardbeien",400,"g")]),
 ("Ontbijt: overnight oats met banaan en noten","Vegetarisch",10,[("kwark",1400,"g"),("havermout",160,"g"),("banaan",420,"g"),("noten",100,"g")]),
 ("Ontbijt: groenteomelet met skyr ernaast","Vegetarisch",15,[("eieren",12,"st"),("spinazie",450,"g"),("paprika",2,"st"),("kwark",1000,"g")]),
 ("Boerenkoolstamppot met rookworst (af en toe)","Vlees",35,[("boerenkool",1200,"g"),("aardappel",600,"g"),("rookworst",400,"g"),("ui",150,"g")]),
 ("Boerenkoolstamppot met kruidige kip (lichter alternatief)","Kip",35,[("boerenkool",1200,"g"),("aardappel",600,"g"),("kipfilet",750,"g"),("ui",150,"g")]),

]

# Bewaak expliciete gerechtvormen: risotto is geen zilvervliesrijstgerecht.
# Deze semantische regels worden op de hele bibliotheek én nieuwe voorstellen getest.
DISH_REQUIRED_INGREDIENTS = (
    (r"risotto", "risottorijst"),
    (r"pasta|spaghetti|penne|fusilli|macaroni", "pasta"),
    (r"wrap|tortilla|fajita", "wraps"),
    (r"couscous", "couscous"),
    (r"stamppot", "aardappel"),
)

def validate_dish_ingredients(title, ingredients):
    keys = {key for key, amount, unit in ingredients}
    issues = []
    name = title.lower()
    for pattern, required in DISH_REQUIRED_INGREDIENTS:
        if re.search(pattern, name) and required not in keys:
            issues.append(f"{title}: verplichte basis {required} ontbreekt")
    return issues

RECIPE_METHODS = {
    "Italiaans geïnspireerde boerenkoolpasta met kipgehakt": (
        "Breng water aan de kook voor de volkorenpasta. Kook de pasta volgens de verpakking en "
        "bewaar een kopje kookwater. Verwarm olijfolie in een ruime pan en bak het kipgehakt "
        "met gedroogde oregano, fijngesneden knoflook, zout en peper volledig gaar en rul. "
        "Voeg de tomatenblokjes toe en laat circa 8 minuten zachtjes pruttelen. "
        "Snijd verse boerenkool fijn en verwijder eventuele dikke nerven; gebruik bij diepvriesboerenkool "
        "de aanwijzingen op de verpakking. Voeg de boerenkool met een scheut water toe "
        "en laat onder een deksel 8-12 minuten zachtjes garen tot de kool zacht genoeg is. "
        "Schep de gekookte pasta erdoor en voeg indien nodig wat achtergehouden kookwater toe "
        "om de saus goed te laten hechten. Breng op smaak met extra peper en eventueel "
        "chilivlokken uit voorraad. Verdeel over vier porties."
    ),
    "HelloFresh-geïnspireerd: champignonrisotto met kipgehakt": (
        "Fruit ui en champignons, bak het kipgehakt goed gaar en zet apart. "
        "Rooster de droge Arborio- of Carnarolirijst kort mee met de ui. "
        "Voeg circa 500–650 ml hete bouillon in porties toe en roer regelmatig, "
        "tot de rijst gaar maar nog stevig is (volg de verpakking). "
        "Schep kipgehakt, spinazie en geraspte kaas erdoor en laat de spinazie slinken. "
        "Let op: bouillon, peper en olie moeten nog van de voorraad komen "
        "en zijn niet in de getoonde kassaprijs opgenomen."
    )
}

# Meer volwaardige tonijngerechten, zonder bestaande gerechten of prijsregels te vervangen.
# Bronvermelding, originele bronreceptuur blijft de referentie voor controle.
RECIPE_SOURCES = {
 "Volkoren tonijnpasta met zwarte olijven en kappertjes": {
   "name": "Allerhande · Pasta met mediterrane tonijnsaus",
   "url": "https://www.ah.nl/allerhande/recept/R-R369914/pasta-met-mediterrane-tonijnsaus",
   "status": "Eigen gezondere variant van bestaand recept, ingrediënten aangepast"
 }
}

from tonijn_varianten import TUNA_RECIPES, TUNA_METHODS
RECIPES.extend(TUNA_RECIPES)
RECIPE_METHODS.update(TUNA_METHODS)
RECIPE_METHODS["Volkoren tonijnpasta met zwarte olijven en kappertjes"] = (
 "Kook de volkoren penne volgens de verpakking beetgaar. Snipper de ui, "
 "snijd de courgettes in blokjes en fruit de ui kort in olijfolie. Bak de "
 "courgette ongeveer 5 minuten mee. Voeg tomatenblokjes, uitgelekte olijven "
 "en kappertjes toe en laat 7 minuten zacht pruttelen. Laat de tonijn "
 "goed uitlekken en verwarm de tonijn in de laatste 2 minuten mee, "
 "zodat hij sappig blijft. Meng met de pasta en verdeel over vier borden. "
 "Olijfolie, peper en optionele knoflook komen uit de voorraad. Dit is "
 "een aangepaste variant van een bestaand Allerhande-recept."
)

