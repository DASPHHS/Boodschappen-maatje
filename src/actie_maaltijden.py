"""Genereer maaltijden UIT supermarktacties, niet andersom.

Conservatieve ingrediëntindeling op productnaam + verpakking. Elke gegenereerde
maaltijd bevat een proteïnebron en groenten, plus eventueel een bijgerecht.
De bestaande prijsengine controleert afzonderlijk alle kassaprijzen.
"""
from receptenradar_catalog import ING
import re

PROTEINS={
 "kipfilet":("Kipfilet","Kip",800,"g"),"kipdij":("Kipdij","Kip",800,"g"),
 "kipgehakt":("Kipgehakt","Kip",800,"g"),"shoarma":("Kipshoarma","Kip",800,"g"),
 "varkenshaas":("Varkenshaas","Vlees",800,"g"),
 "gehakt":("Gehakt","Vlees",800,"g"),
 "zalm":("Zalm","Vis",800,"g"),
 "gerookte_zalm":("Gerookte zalm","Vis",400,"g"),
 "tonijn":("Tonijn","Vis",500,"g"),"garnalen":("Garnalen","Vis",800,"g"),
 "tofu":("Tofu","Vegetarisch",800,"g"),
 "kikkererwten":("Kikkererwten","Vegetarisch",850,"g"),
 "linzen":("Linzen","Vegetarisch",850,"g"),
 "bonen":("Zwarte bonen","Vegetarisch",850,"g"),
 "eieren":("Eieren","Vegetarisch",10,"st")
}
VEGETABLES={
 "broccoli":("broccoli",1100,"g"),"bloemkool":("bloemkool",1,"st"),
 "spinazie":("spinazie",1100,"g"),"boerenkool":("boerenkool",1100,"g"),
 "wok":("wokgroenten",1100,"g"),"spruiten":("spruitjes",1100,"g"),
 "courgette":("courgette",3,"st"),"paprika":("paprika",4,"st"),
 "champignons":("champignons",1100,"g"),"wortel":("wortelen",1100,"g"),
 "tomaten":("tomaten",1100,"g"),"sla":("salade",1000,"g"),
 "komkommer":("komkommer",2,"st")
}
SIDES={
 "aardappel":("krieltjes",400,"g"),"zoete_aardappel":("zoete aardappel",400,"g"),
 "rijst":("zilvervliesrijst",140,"g"),"pasta":("volkoren pasta",140,"g"),
 "couscous":("volkoren couscous",140,"g"),
 "wraps":("volkoren wraps",4,"st"),"naan":("naanbrood",4,"st"),
}
SELECTION_EXCLUSIONS=re.compile(
 r"vegetar|vegan|plantaardig|maaltijd|pizza|broodbeleg|saus|kruiden|spread|"
 r"burger|schnitzel|soep|stamppot|wrap met|sandwich|salade met|chips|"
 r"frikandel|gekruid|gemarineerde kipfilet in saus",re.I)
# Deze productgroepen hebben andere hoeveelheden/eenheden; niet zonder bewijs koppelen.
GROUPS={"proteine":PROTEINS,"groente":VEGETABLES,"bijgerecht":SIDES}

# Beproefde combinatiegroepen: een kortingspercentage is geen recept.
PAIRINGS={
 "kipfilet":("broccoli bloemkool spinazie wok courgette paprika champignons wortel tomaten sla spruiten","aardappel rijst pasta wraps naan"),
 "kipdij":("broccoli bloemkool spinazie wok courgette paprika champignons wortel tomaten spruiten","aardappel rijst zoete_aardappel"),
 "kipgehakt":("spinazie courgette paprika champignons tomaten wok broccoli","rijst pasta wraps"),
 "shoarma":("wok paprika courgette sla tomaten komkommer","wraps aardappel rijst"),
 "varkenshaas":("broccoli bloemkool champignons spruiten spinazie wortel","aardappel zoete_aardappel"),
 "gehakt":("broccoli bloemkool courgette paprika champignons tomaten spinazie wok wortel","aardappel pasta rijst wraps"),
 "zalm":("broccoli bloemkool spinazie courgette spruiten wortel","aardappel rijst pasta"),
 "gerookte_zalm":("spinazie courgette sla komkommer tomaten","pasta wraps"),
 "tonijn":("paprika tomaten sla komkommer courgette","pasta rijst wraps"),
 "garnalen":("wok broccoli spinazie courgette paprika","rijst naan"),
 "tofu":("broccoli wok paprika courgette champignons wortel spinazie","rijst couscous naan"),
 "kikkererwten":("spinazie bloemkool tomaten paprika courgette wortel","rijst couscous"),
 "linzen":("spinazie tomaten wortel courgette paprika champignons","rijst pasta"),
 "bonen":("paprika tomaten sla courgette wok","rijst wraps"),
 "eieren":("spinazie champignons paprika tomaten courgette broccoli","aardappel wraps")
}
SECOND_VEG={
 "spinazie":"champignons tomaten courgette",
 "broccoli":"paprika wortel champignons",
 "bloemkool":"paprika wortel tomaten",
 "spruiten":"champignons wortel",
 "wok":"paprika champignons",
 "courgette":"paprika champignons tomaten spinazie",
 "paprika":"courgette tomaten champignons broccoli wok sla",
 "champignons":"spinazie courgette paprika spruiten broccoli",
 "wortel":"broccoli bloemkool spruiten paprika",
 "tomaten":"courgette paprika spinazie sla",
 "sla":"paprika tomaten komkommer",
 "komkommer":"sla tomaten",
 "boerenkool":""
}
def sensible_meal(protein,veg,side=None,veg2=None):
    allowed_veg,allowed_sides=PAIRINGS.get(protein,("",""))
    if veg not in allowed_veg.split() or (side and side not in allowed_sides.split()):
        return False
    if veg2 and (veg2 not in allowed_veg.split() or
                 veg2 not in SECOND_VEG.get(veg,"").split()):
        return False
    return True

# Recepttemplates i.p.v. willekeurige combinatie van afgeprijsde producten.
# (eiwit, hoofdgroente, bijgerecht, extra groente, titel, kookaanpak)
# None betekent dat er géén bijgerecht of tweede groente nodig is.
DISH_TEMPLATES=[
 ("kipfilet","broccoli","naan",None,"Tandoorikip met broccoli en naan","Kruid de kip met tandoorikruiden en bak volledig gaar. Stoom of rooster de broccoli beetgaar. Verwarm naan volgens de verpakking en serveer met de kip en groenten."),
 ("tofu","spinazie","naan",None,"Tandoori-tofu met spinazie en naan","Bak tofu krokant met tandoorikruiden. Laat spinazie in een aparte pan slinken en verwarm naan volgens de verpakking. Serveer samen."),
 ("garnalen","wok","naan",None,"Garnalenwok met groenten en naan","Roerbak de groenten beetgaar en voeg ontdooide garnalen op het einde toe. Verhit volledig en serveer met verwarmde naan."),
 ("kipfilet","broccoli","aardappel",None,"Ovenkip met broccoli en geroosterde krieltjes","Kruid kip en krieltjes met paprikapoeder, knoflook, peper en wat olie. Rooster in de oven, voeg broccoli later toe."),
 ("kipfilet","broccoli",None,None,"Knoflookkip met geroosterde broccoli","Bak gekruide kipfilet goudbruin. Rooster broccoli met knoflook en citroen."),
 ("kipfilet","broccoli","aardappel","paprika","Ovenkip met paprika, broccoli en krieltjes","Rooster kip, paprika, broccoli en krieltjes met olie, knoflook en paprikapoeder. Voeg broccoli later toe."),
 ("kipfilet","broccoli","rijst","wortel","Teriyaki-kip met broccoli, wortel en zilvervliesrijst","Roerbak kip, broccoli en wortel. Maak af met sojasaus, honing, gember en knoflook; serveer met rijst."),
 ("kipfilet","wok","rijst",None,"Gemberkip met wokgroenten en rijst","Bak kipfilet volledig gaar met knoflook en gember. Roerbak wokgroenten beetgaar en serveer met rijst en een beetje sojasaus."),
 ("kipfilet","wok",None,"paprika","Roerbak-kip met wokgroenten en paprika","Roerbak kip met gember en knoflook, voeg wokgroenten en paprika toe en maak af met sojasaus."),
 ("kipfilet","spinazie","pasta","champignons","Kip-spinaziepasta met champignons","Bak kip en champignons. Schep er spinazie en gekookte volkoren pasta met een beetje kookwater door."),
 ("kipfilet","courgette","pasta","tomaten","Volkoren pasta met kip, courgette en tomaat","Bak kip en courgette met Italiaanse kruiden. Voeg tomaten en gekookte pasta toe."),
 ("kipfilet","paprika","wraps","sla","Kipfajita-wraps met paprika en sla","Bak reepjes kip met komijn en paprikapoeder, voeg paprika toe en serveer in wraps met frisse sla."),
 ("kipfilet","sla","wraps","tomaten","Frisse kipwrap met tomaat en sla","Bak gekruide kip volledig gaar en laat afkoelen. Vul wraps met kip, tomaat en sla."),
 ("kipdij","broccoli","rijst","wortel","Sticky kipdij met broccoli, wortel en rijst","Rooster kipdij met sojasaus, honing, gember en knoflook. Serveer met gestoomde broccoli, wortel en rijst."),
 ("kipdij","bloemkool","aardappel",None,"Gekruide kipdij met bloemkool en krieltjes","Rooster kipdij, bloemkool en krieltjes op een bakplaat met paprika en tijm."),
 ("kipgehakt","spinazie","pasta","champignons","Italiaanse kipgehaktballetjes met spinazie, champignons en volkorenpasta","Draai balletjes van kipgehakt met Italiaanse kruiden. Bak met champignons en serveer met spinazie en pasta."),
 ("kipgehakt","courgette","pasta","tomaten","Kipgehaktballetjes in tomatensaus met courgette en pasta","Bak gekruide kipgehaktballetjes. Stoof tomaat en courgette tot saus en serveer met pasta."),
 ("kipgehakt","paprika","wraps","tomaten","Mexicaanse kipgehaktwraps met paprika en tomaat","Bak kipgehakt met komijn en paprikapoeder, voeg paprika en tomaat toe en vul de wraps."),
 ("shoarma","paprika","wraps","sla","Kipshoarmawraps met paprika en sla","Bak kipshoarma met paprika; vul warme wraps met knapperige sla."),
 ("shoarma","wok","aardappel",None,"Kipshoarma met gebakken groenten en krieltjes","Bak kipshoarma en krieltjes apart. Roerbak de groenten en serveer met de gekruide kipshoarma."),
 ("shoarma","wok","aardappel","paprika","Kipshoarma met paprika, wokgroenten en krieltjes","Bak kipshoarma, wokgroenten en paprika in de pan; serveer met krokante krieltjes."),
 ("varkenshaas","broccoli","aardappel",None,"Varkenshaas met broccoli en gebakken krieltjes","Bak varkenshaas kort rondom en laat garen. Serveer met gestoomde broccoli en gebakken krieltjes."),
 ("varkenshaas","spruiten","aardappel",None,"Varkenshaas met geroosterde spruiten en krieltjes","Rooster spruitjes en krieltjes met tijm; bak varkenshaas apart en laat even rusten."),
 ("varkenshaas","champignons","aardappel",None,"Varkenshaas met champignons en krieltjes","Bak varkenshaas en champignons met tijm en knoflook. Serveer met krieltjes."),
 ("gehakt","tomaten","pasta","courgette","Volkoren bolognese met courgette","Bak rundergehakt met Italiaanse kruiden; laat tomaat en courgette meestoven en serveer met pasta."),
 ("gehakt","paprika","wraps","tomaten","Mexicaanse rundergehaktwraps met paprika en tomaat","Bak gehakt met komijn en gerookt paprikapoeder. Voeg paprika en tomaat toe en vul wraps."),
 ("gehakt","broccoli","aardappel",None,"Gekruid rundergehakt met broccoli en gebakken aardappelen","Bak gehakt met peper en paprikapoeder. Serveer met broccoli en gebakken aardappelen."),
 ("zalm","broccoli","aardappel",None,"Ovenzalm met broccoli en krieltjes","Rooster krieltjes, voeg broccoli en zalm toe en maak af met citroen, dille en peper."),
 ("zalm","spinazie","pasta",None,"Volkoren zalmpasta met spinazie en citroen","Bak zalm apart en roer spinazie door de gekookte pasta. Maak af met citroen en zwarte peper."),
 ("zalm","spruiten","aardappel",None,"Ovenzalm met spruitjes en krieltjes","Rooster spruitjes en krieltjes; voeg zalm later toe met citroen en dille."),
 ("gerookte_zalm","sla","wraps","komkommer","Frisse gerookte-zalmwraps met sla en komkommer","Vul wraps met gerookte zalm, komkommer en sla, breng op smaak met citroensap en peper; houd gekoeld."),
 ("tonijn","tomaten","pasta",None,"Mediterrane tonijnpasta met tomaat","Meng tonijn met tomaat, knoflook, olijfolie en volkoren pasta."),
 ("tonijn","sla","wraps","tomaten","Tonijnwraps met sla en tomaat","Meng uitgelekte tonijn met een beetje olijfolie en peper. Vul wraps met sla en tomaat."),
 ("tofu","broccoli","rijst","wortel","Gembertofu met broccoli, wortel en rijst","Bak tofu krokant met gember en sojasaus; roerbak groenten en serveer met rijst."),
 ("tofu","wok","rijst",None,"Krokante tofu met wokgroenten en rijst","Bak tofu krokant, roerbak groenten met knoflook en gember en serveer met rijst."),
 ("tofu","wok",None,"paprika","Krokante tofu met wokgroenten en paprika","Bak tofu goudbruin; wok groenten met paprika, gember en sojasaus."),
 ("kikkererwten","bloemkool","rijst",None,"Kikkererwten-bloemkoolcurry met zilvervliesrijst","Stoof bloemkool en kikkererwten met currykruiden en een scheut water tot de groenten gaar zijn; serveer met rijst."),
 ("linzen","tomaten","pasta","courgette","Linzenbolognese met courgette en volkorenpasta","Laat linzen, tomaat, courgette en Italiaanse kruiden zachtjes pruttelen; serveer met pasta."),
 ("bonen","paprika","wraps","tomaten","Zwartebonenwraps met paprika en tomaat","Stoof zwarte bonen met paprika, tomaat, komijn en gerookt paprikapoeder; vul de wraps."),
 ("eieren","spinazie","wraps","champignons","Spinazie-champignon-eiwraps","Bak spinazie en champignons; giet er geklutste eieren over en verdeel over wraps."),
 ("eieren","broccoli","aardappel",None,"Groente-omelet met broccoli en gebakken aardappeltjes","Bak aardappeltjes, voeg kortgegaarde broccoli toe en giet de eieren erover."),
]
DISH_BY_KEYS={(p,v,s,v2):(title,method) for p,v,s,v2,title,method in DISH_TEMPLATES}

def classify_offers(offers):
    """Welke ingrediëntcategorieën zijn aantoonbaar in aanbieding?

    Een 'actie' zonder maat, controleerbare actiecondities of geldigheid telt
    niet mee. De daadwerkelijke prijskeuze blijft bij ingredient_price().
    """
    grouped={role:{} for role in GROUPS}
    for offer in offers:
        name=offer.get("norm","")
        if SELECTION_EXCLUSIONS.search(name):
            # Burgers en gekruide halffabricaten krijgen pas later eigen templates.
            continue
        if not offer.get("quantity") or offer.get("is_loyalty"):
            continue
        typ=offer.get("promotion_type","").lower()
        multi_qty=offer.get("multi_buy_quantity") or 0
        multi_price=offer.get("multi_buy_price") or 0
        normal=offer.get("original_price") or offer.get("price") or 0
        real_bundle=multi_qty>=2 and multi_price>0 and multi_price<multi_qty*normal
        real_single=bool(offer.get("original_price") and
                         offer.get("price") and offer["price"]<offer["original_price"])
        # Alleen rekenbaar werkelijk voordeel telt voor actiegestuurde maaltijden.
        if not (real_bundle or real_single):
            continue
        incomplete_bundle=(any(x in typ for x in ("gratis","1+1","2+1","multi","bundle"))
                           or bool(re.search(r"\b\d+\s+voor\b",typ)))
        if incomplete_bundle and not real_bundle:
            continue
        for role,group in GROUPS.items():
            for key in group:
                label,pattern,exclude=ING[key]
                if offer.get("unit") != group[key][-1]:continue
                if re.search(pattern,name,re.I) and not re.search(exclude,name,re.I):
                    if not re.search(r"mix van|groentemix met|aardappelgratin|soepgroenten",name,re.I):
                        grouped[role].setdefault(key,[]).append(offer)
    return grouped

def meal_candidates(offers,limit=100,expand=False):
    """Alle passende maaltijdtemplates als kandidaten, niet slechts twee actieproducten.

    Maak eerst het complete recept, en bereken de werkelijke korting pas later
    met ingredient_price. Een korting op alleen krieltjes kan dus een gerecht
    met varkenshaas en reguliere broccoli relevant maken. De bestaande
    compatibiliteitsregels blijven van kracht.
    """
    groups=classify_offers(offers)
    on_sale={key for group in groups.values() for key in group}
    if not expand and (not groups["proteine"] or not groups["groente"]):return []
    scored=[]
    seen=set()
    for pk,vk,sk,vk2,title,method in DISH_TEMPLATES:
        if not sensible_meal(pk,vk,sk,vk2):continue
        ingredients=[(pk,PROTEINS[pk][2],PROTEINS[pk][3])]
        veg_amount=VEGETABLES[vk][1]
        veg_unit=VEGETABLES[vk][2]
        if vk2 and veg_unit=="g":veg_amount=round(veg_amount*.72)
        ingredients.append((vk,veg_amount,veg_unit))
        if vk2:
            a,u=VEGETABLES[vk2][1:]
            ingredients.append((vk2,round(a*.35) if u=="g" else max(1,round(a*.65)),u))
        if sk:ingredients.append((sk,SIDES[sk][1],SIDES[sk][2]))
        if title in seen:continue
        seen.add(title)
        hits=sum(key in on_sale for key,_,_ in ingredients)
        if expand and not hits:continue
        if not expand and (pk not in groups["proteine"] or vk not in groups["groente"]):continue
        scored.append((hits,title,(title,PROTEINS[pk][1],35,ingredients)))
    # Kandidaatselectie ≠ bewijs voor een actie. De kassaprijsengine bepaalt
    # daarna welke acties echt voordeliger zijn en telt ze afzonderlijk.
    scored.sort(key=lambda x:(-x[0],x[1]))
    return [item for _,_,item in scored[:limit]]
