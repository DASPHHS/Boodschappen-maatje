"""Eenduidige keukenindeling en verantwoorde Nederlandse recepttitels.

Een recept krijgt geen nationaliteit op basis van alleen kip, rijst, curry,
spaghetti of een woord als 'fusion'. Bij onbekende herkomst tonen we
'Internationaal', geen verzonnen land.

Vertalingen zijn handmatig gecontroleerde voorbeelden of conservatieve,
volledig gedekte patronen. Originele titels worden ALTIJD behouden.
"""
import re
import unicodedata

SPECIFIC_CUISINES=(
 "Surinaams","Indonesisch","Indiaas","Thais","Vietnamees","Koreaans",
 "Japans","Chinees","Turks","Marokkaans","Libanees","Grieks",
 "Italiaans","Mexicaans","Spaans","Nederlands","Frans",
 "Caribisch","Ethiopisch","Peruaans","Braziliaans","Amerikaans",
 "Costa Ricaans","West-Afrikaans","Midden-Oosters","Mediterraan"
)
GENERAL={"","overig","overig / wereldwijd","overig/onbekend",
         "internationaal","wereldkeukens","onbekend","aziatisch",
         "latijns-amerikaans","zuid-amerikaans","overig / wereldwijd"}
ALIASES={
 "indisch":"Indonesisch","surinaamse":"Surinaams","surinamese":"Surinaams",
 "hollands":"Nederlands","nederlands":"Nederlands",
 "mediterrane":"Mediterraan","mediterraan":"Mediterraan",
 "mexican":"Mexicaans","italian":"Italiaans","greek":"Grieks",
 "american":"Amerikaans","korean":"Koreaans","thai":"Thais",
 "japanese":"Japans","vietnamese":"Vietnamees","moroccan":"Marokkaans",
 "caribbean":"Caribisch","middle eastern":"Midden-Oosters"
}

def normalized(s):
    s=unicodedata.normalize("NFKD",str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))

# Alleen voldoende kenmerkende gerechtbenamingen of expliciete landnamen.
CUES=[
 ("Surinaams",r"\b(surinaam\w*|surinam\w*|sranang|saoto|moksi\w*|moksie\w*|"
              r"bakkeljauw|masoesa|pomtayer|heri heri|pepre watra|bara met)\b"),
 ("Indonesisch",r"\b(indonesi\w*|rendang|gado.gado|soto ayam|"
                r"nasi goreng|mie goreng|gado gado|sambal goreng)\b"),
 ("Indiaas",r"\b(india\w*|indian|tandoori|vindaloo|biryani|"
            r"chana masala|paneer tikka|palak paneer|dal makhani)\b"),
 ("Thais",r"\b(thaise?|thai|pad thai|pad krapow|tom yum|tom kha|massaman)\b"),
 ("Vietnamees",r"\b(vietnam\w*|pho bo|pho ga|banh mi|bun cha)\b"),
 ("Koreaans",r"\b(korea\w*|bibimbap|bulgogi|kimchi|gochujang|japchae)\b"),
 ("Japans",r"\b(japan\w*|ramen|miso soup|yakitori|okonomiyaki|"
            r"teriyaki|sushi|donburi|udon)\b"),
 ("Chinees",r"\b(chinese?|chinees|chinees\w*|szechuan|sichuan|"
             r"kung pao|mapo tofu|char siu|dim sum)\b"),
 ("Turks",r"\b(turk\w*|lahmacun|menemen|iskender|imam bayildi)\b"),
 ("Marokkaans",r"\b(marokka\w*|morocc\w*|harira|tagine|tajine)\b"),
 ("Libanees",r"\b(libane\w*|leban\w*|fattoush|tabbouleh|kibbeh)\b"),
 ("Grieks",r"\b(griek\w*|greek|souvlaki|moussaka|spanakopita)\b"),
 ("Italiaans",r"\b(italia\w*|italian|risotto|lasagne|gnocchi|"
              r"parmigiana|cacio e pepe|puttanesca|carbonara|amatriciana)\b"),
 ("Mexicaans",r"\b(mexic\w*|mexica\w*|enchilada|quesadilla|"
               r"burrito|fajita|taco|pozole|chilaquiles)\b"),
 ("Spaans",r"\b(spanj\w*|spanish|paella|gazpacho|patatas bravas|"
            r"tortilla espanola)\b"),
 ("Nederlands",r"\b(nederland\w*|holland\w*|stamppot|hutspot|"
                r"erwtensoep|snert)\b"),
 ("Frans",r"\b(franse?|french|ratatouille|coq au vin|"
           r"boeuf bourguignon|cassoulet)\b"),
 ("Caribisch",r"\b(caribbean|caribisch|jerk chicken|"
                r"rice and peas|callaloo)\b"),
 ("Ethiopisch",r"\b(ethiop\w*|doro wat|injera|misir wat)\b"),
 ("Peruaans",r"\b(peru\w*|lomo saltado|aji de gallina|causa limena)\b"),
 ("Braziliaans",r"\b(brazil\w*|brazili\w*|feijoada|moqueca)\b"),
 ("Costa Ricaans",r"\b(costa rica\w*|gallo pinto)\b"),
 ("West-Afrikaans",r"\b(west.afrika\w*|jollof|egusi|fufu)\b"),
 ("Midden-Oosters",r"\b(midden.oost\w*|middle.eastern|shakshuka|"
                  r"muhammara|maqluba|shawarma)\b"),
 ("Mediterraan",r"\b(mediterr\w*|mediterrane\w*)\b"),
 ("Amerikaans",r"\b(american|amerikaans|tex.mex|"
                r"mac and cheese|new orleans|cajun)\b"),
]
PATTERNS=[(c,re.compile(p,re.I)) for c,p in CUES]

def infer_cuisine(title,declared=None):
    original=normalized(declared).strip()
    if original in GENERAL:
        original=""
    elif original in ALIASES:
        return ALIASES[original]
    else:
        for known in SPECIFIC_CUISINES:
            if original==normalized(known):
                return known
        # Titelinhoud helpt de regio bepalen, maar onbekende tags doen dat niet.
    name=normalized(title)
    for cuisine,pattern in PATTERNS:
        if pattern.search(name):
            return cuisine
    return "Internationaal"

# Betekenis behouden, geen automatische overname van ingrediënten die niet in
# de brontitel worden genoemd. Dit zijn geverifieerde formuleringen van titels.
EXACT_TRANSLATIONS={
 "chicken bowls with rice and lentils":"Kipbowls met rijst en linzen",
 "chicken soup with rice and potatoes":"Kippensoep met rijst en aardappelen",
 "chicken with orange, spinach and cherry tomatoes":
     "Kip met sinaasappel, spinazie en cherrytomaten",
 "chili garlic chicken with rice and beans":
     "Chili-knoflookkip met rijst en bonen",
 "chicken bacon broccoli alfredo spaghetti":
     "Spaghetti Alfredo met kip, spek en broccoli",
 "lentil, potato, and tomato curry":"Curry met linzen, aardappel en tomaat",
 "spinach mushroom pesto spaghetti":
     "Spaghetti met spinazie, champignons en pesto",
 "chicken and broccoli stir fry":"Roerbakgerecht met kip en broccoli",
 "chicken with broccoli and rice":"Kip met broccoli en rijst",
 "chicken and vegetable curry":"Kipcurry met groenten",
 "rice and beans":"Rijst met bonen",
}
# Toepassen als vrijwel alles met zekerheid vertaald kan worden.
PHRASES=(
 ("sweet potatoes","zoete aardappelen"),
 ("sweet potato","zoete aardappel"),
 ("cherry tomatoes","cherrytomaten"),
 ("green beans","sperziebonen"),
 ("black beans","zwarte bonen"),
 ("kidney beans","kidneybonen"),
 ("ground beef","rundergehakt"),
 ("minced beef","rundergehakt"),
 ("chicken breasts","kipfilets"),
 ("chicken breast","kipfilet"),
 ("chicken thighs","kippendijen"),
 ("chicken thigh","kippendij"),
 ("red onion","rode ui"),
 ("spring onions","bosuien"),
 ("bell peppers","paprika's"),
 ("bell pepper","paprika"),
 ("stir fry","roerbakgerecht"),
 ("meal prep","mealprep"),
 ("with","met"),("and","en"),("rice","rijst"),
 ("chicken","kip"),("beef","rundvlees"),("turkey","kalkoen"),
 ("salmon","zalm"),("tuna","tonijn"),("shrimp","garnalen"),
 ("prawns","garnalen"),("lentils","linzen"),("lentil","linzen"),
 ("potatoes","aardappelen"),("potato","aardappel"),
 ("tomatoes","tomaten"),("tomato","tomaat"),
 ("spinach","spinazie"),("mushrooms","champignons"),
 ("mushroom","champignon"),("broccoli","broccoli"),
 ("carrots","wortelen"),("carrot","wortel"),
 ("zucchini","courgette"),("eggplant","aubergine"),
 ("onions","uien"),("onion","ui"),("garlic","knoflook"),
 ("orange","sinaasappel"),("lemon","citroen"),
 ("beans","bonen"),("chickpeas","kikkererwten"),
 ("vegetables","groenten"),("vegetable","groente"),
 ("chili","chili"),("curry","curry"),("ginger","gember"),
 ("salad","salade"),("soup","soep"),("stew","stoofpot"),
 ("bowl","bowl"),("bowls","bowls"),("noodles","noedels"),
 ("chili","chili"),("pesto","pesto"),("spaghetti","spaghetti"),
 ("pasta","pasta"),("tofu","tofu"),("avocado","avocado"),
 ("eggs","eieren"),("egg","ei"),("oats","havermout"),
 ("oatmeal","havermout"),("quinoa","quinoa"),("sauce","saus"),
 ("coconut","kokos"),("milk","melk"),("yogurt","yoghurt"),
 ("yoghurt","yoghurt"),("peas","erwten"),("pepper","peper"),
 ("roasted","geroosterd"),("baked","gebakken"),("spicy","pittig"),
 ("fresh","vers"),("green","groen"),("red","rood"),
 ("italian","Italiaans"),("thai","Thais"),("korean","Koreaans"),
 ("mexican","Mexicaans"),("moroccan","Marokkaans"),
 ("indian","Indiaas"),("japanese","Japans"),
 ("cajun","Cajun"),("alfredo","Alfredo"),("teriyaki","teriyaki"),
 ("miso","miso"),("risotto","risotto"),("lasagna","lasagne"),
 ("orzo","orzo"),("wraps","wraps"),("wrap","wrap"),
)
TRANSLATION_RULES=[(re.compile(r"(?<![A-Za-z])"+re.escape(src)+r"(?![A-Za-z])",re.I),dst)
                   for src,dst in sorted(PHRASES,key=lambda pair:-len(pair[0]))]

def dutch_title(title):
    """Return (Dutch display title, translated). Never disguise English as Dutch.

    We translate only if every word in the title was recognized; unknown words
    result in the original English source title (with UI language badge).
    """
    original=str(title or "").strip()
    key=normalized(original).strip()
    if key in EXACT_TRANSLATIONS:return EXACT_TRANSLATIONS[key],True
    # Already Dutch, leave intact (multilingual food terms are common).
    if not re.search(r"\b(with|and|chicken|potatoes|rice|lentils|soup|"
                     r"mushroom|baked|roasted|beans|shrimp|beef|salad)\b",key):
        return original,False
    changed=original
    spans=[]
    # Replace placeholders so 'and' etc do not alter replacements.
    for index,(pattern,dutch) in enumerate(TRANSLATION_RULES):
        token=f"ZZTRANSLATE{index}ZZ"
        if pattern.search(changed):
            changed=pattern.sub(token,changed)
            spans.append((token,dutch))
    # If unknown original English words remain: keep unchanged, mark English.
    residue=changed
    residue=re.sub(r"ZZTRANSLATE\d+ZZ","",residue)
    residue=re.sub(r"[\s,;:()\-–/&.!?]+","",residue)
    if residue:return original,False
    for token,dutch in spans:
        changed=changed.replace(token,dutch)
    changed=re.sub(r"\s+,",",",changed)
    changed=re.sub(r",\s*en\s+", " en ", changed)
    # This conservative fallback is for simple constructions ("X with Y").
    if changed!=original:
        return changed[0].upper()+changed[1:].lower(),True
    return original,False
