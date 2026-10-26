"""Semantische validatie van losse receptingrediënten tegen winkelartikelen.

Een productnaam met een ingrediëntwoord is niet genoeg: fruitspread,
babyvoeding, kruidenmix, gepekelde groente of gearomatiseerde zuivel is
niet uitwisselbaar met het receptingrediënt zelf.
"""
import re
import unicodedata

def norm(value):
    value=unicodedata.normalize("NFKD",str(value or "").casefold())
    value="".join(x for x in value if not unicodedata.combining(x))
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ",value)).strip()

# Altijd verboden voor losse hoofdingrediënten, ongeacht prijs of actie.
PREPARED=re.compile(
 r"\b(?:babyvoeding|babyhapje|babymaaltijd|baby puree|babyvoedsel|"
 r"olvarit|ellas kitchen|ella s kitchen|nutricia|organix baby|"
 r"fruitspread|jam|confituur|marmelade|beleg|tapenade|"
 r"puree|smoothie|knijpfruit|fruitmoes|fruitpuree|appelmoes|"
 r"kant en klaar|kant klare|maaltijdmix|maaltijdpakket|"
 r"kruidenmix|kruidenpasta|kruidenpoeder|boemboe|"
 r"soep|chips|cracker|koek|taart|limonade|sap|frisdrank|"
 r"shampoo|dierenvoer|hondenvoer|kattenvoer)\b"
)

RULES={
 "blauwe_bessen":{
  "positive":r"\b(?:blauwe bessen|blauwebessen|bosbessen|blueberries)\b",
  "reject":r"\b(?:aardbei|aardbeien|framboos|cranberry|bramen|fruitmix|fruit mix|"
           r"vruchtenmix|vruchten mix|vruchten|fruit|gedroogd|yoghurt|kwark|gurt|"
           r"reep|ontbijt|muesli|puree|siroop|saus|compote|concentraat)\b"
 },
 "aardbeien":{
  "positive":r"\b(?:aardbeien|aardbei|strawberries)\b",
  "reject":r"\b(?:yoghurt|kwark|gurt|soja|drank|roomijs|zuivel|"
           r"gedroogd|chocolade|vruchtenmix|fruitsalade|mix|"
           r"muesli|ontbijt|gebak|vla|dessert|ijs|repen)\b"
 },
 "banaan":{"reject":r"\b(?:yoghurt|kwark|reep|gedroogd|chips|nectar|ijs|melk|vla)\b"},
 "wortel":{"reject":r"\b(?:doperwten|doperwtjes|erwten|erwtjes|mais|ma is|mix|zoetzuur|pickle|ingemaakt)\b"},
 "ui":{"reject":r"\b(?:amsterdamse|zilveruitjes|zilveruien|zoetzure|"
      r"ingelegde|ingelegd|gebakken|krokant|uitjes|uienringen|poeder|mix)\b"},
 "shoarma":{"reject":r"\b(?:rijst|rice|bami|nasi|pasta|orzo|maaltijd|maaltijdsalade|diner|schotel|wrap|broodje|pizza|soep|saus|topping|kant en klaar|kant klare)\b"},
 "kipfilet":{"reject":r"\b(?:knorr|maggi|romana|trattoria|"
      r"saus|mix|bereiding|schotel|maaltijd|diner|kruiden|beleg|"
      r"kipfiletstukjes in saus|gegrilde kip salade|pizza|soep)\b"},
 "kipdij":{"reject":r"\b(?:saus|maaltijd|mix|kruiden|beleg|pizza)\b"},
 "gehakt":{"reject":r"\b(?:half om half|halfomhalf|varken|varkens|"
      r"kip|vegetarisch|plantaardig|soja|mix|saus|burger|bereid)\b"},
 "kikkererwten":{"reject":r"\b(?:hummus|falafel|crunch|snack|"
      r"groentemix|groentenmix|curry|mix|maaltijd|salade|saus)\b"},
 "bonen":{"reject":r"\b(?:salade|maaltijd|mix|chili|saus|soep)\b"},
 "spinazie":{"reject":r"\b(?:maaltijd|schotel|lasagne|"
      r"mix|pizza|quiche|roomspinazie|a la creme|saus|stampot)\b"},
 "broccoli":{"reject":r"\b(?:groentemix|maaltijd|schotel|"
      r"saus|soep|quiche|mix|pizza|roerbak|wokgroenten)\b"},
 "kwark":{"reject":r"\b(?:plantaardig|soja|vegan|alpro|kokos|"
      r"dessert|kwarktaart|drank|knijp|roomkwark|vla)\b"},
 "yoghurt":{"reject":r"\b(?:plantaardig|soja|vegan|alpro|"
      r"yoghurtdrank|gurt|dessert|vla|melkdrank)\b"},
 "tomaten":{"reject":r"\b(?:tomatensoep|tomaten soep|tomatensap|tomaten saus|"
      r"passata|gezeefd|polpa|puree|concentraat|salsa|ketchup)\b"},
 "paprika":{"reject":r"\b(?:paprikapoeder|paprika poeder|"
      r"kruiden|wokmix|chips|mix|saus|pesto)\b"},
 "champignons":{"reject":r"\b(?:soep|roomsaus|"
      r"champignonsaus|champignon saus|pizza|mix)\b"},
 "tonijn":{"reject":r"\b(?:maaltijd|schotel|"
      r"salade|pasta|wrap|sandwich|beleg|sushi|saus|pizza)\b"},
 "zalm":{"reject":r"\b(?:maaltijd|schotel|salade|"
      r"pasta|wrap|sandwich|beleg|sushi|saus|pizza)\b"},
 "pasta":{"reject":r"\b(?:maaltijd|kant en klaar|"
      r"salade|soep|saus|pasta saus|pastasaus)\b"},
 "rijst":{"reject":r"\b(?:maaltijd|kant en klaar|"
      r"risotto|rijstwafel|melk|soep|saus|bloem|mix)\b"},
 "rookworst":{"reject":r"\b(?:plantaardig|vega|vegetarisch|smaak|maaltijd)\b"}
}

def compatible(name,ingredient):
    name=norm(name)
    if not name:return False
    # Voor kruiden, olie en houdbare bewerkte basissauzen is productnaamtoets
    # nog steeds relevant; het gevaar is grootst voor hele ingrediënten.
    if PREPARED.search(name):return False
    rule=RULES.get(ingredient)
    if not rule:return True
    return (not rule.get("positive") or bool(re.search(rule["positive"],name))) and not bool(
        re.search(rule["reject"],name))

def recipe_line_errors(recipe):
    issues=[]
    for field in ("ingredients","deal_basket"):
        lines=recipe.get(field,[])
        if isinstance(lines,dict):lines=lines.get("ingredients",[])
        for line in lines or []:
            if line.get("components"):
                pieces=line["components"]
                # Componenten horen een eigen productnaam én sleutels te bevatten.
                for part in pieces:
                    name=part.get("product") or ""
                    if name and not compatible(name,line.get("key")):issues.append((field,line.get("key"),name))
            else:
                name=line.get("product") or ""
                if name and not compatible(name,line.get("key")):issues.append((field,line.get("key"),name))
    return issues
