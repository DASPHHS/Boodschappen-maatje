"""Genereer maaltijden UIT supermarktacties, niet andersom.

Conservatieve ingrediëntindeling op productnaam + verpakking. Elke gegenereerde
maaltijd bevat een proteïnebron en groenten, plus eventueel een bijgerecht.
De bestaande prijsengine controleert afzonderlijk alle kassaprijzen.
"""
from receptenradar_catalog import ING
import re

PROTEINS={
 "kipfilet":("Kipfilet","Kip",650,"g"),"kipdij":("Kipdij","Kip",700,"g"),
 "kipgehakt":("Kipgehakt","Kip",650,"g"),"shoarma":("Kipshoarma","Kip",650,"g"),
 "varkenshaas":("Varkenshaas","Vlees",800,"g"),
 "gehakt":("Gehakt","Vlees",650,"g"),
 "zalm":("Zalm","Vis",650,"g"),
 "gerookte_zalm":("Gerookte zalm","Vis",400,"g"),
 "tonijn":("Tonijn","Vis",500,"g"),
 "tofu":("Tofu","Vegetarisch",750,"g"),
 "kikkererwten":("Kikkererwten","Vegetarisch",850,"g"),
 "linzen":("Linzen","Vegetarisch",850,"g"),
 "bonen":("Zwarte bonen","Vegetarisch",850,"g"),
 "eieren":("Eieren","Vegetarisch",10,"st")
}
VEGETABLES={
 "broccoli":("broccoli",800,"g"),"bloemkool":("bloemkool",1,"st"),
 "spinazie":("spinazie",800,"g"),"boerenkool":("boerenkool",800,"g"),
 "wok":("wokgroenten",900,"g"),"spruiten":("spruitjes",800,"g"),
 "courgette":("courgette",3,"st"),"paprika":("paprika",4,"st"),
 "champignons":("champignons",700,"g"),"wortel":("wortelen",800,"g"),
 "tomaten":("tomaten",800,"g"),"sla":("salade",300,"g"),
 "komkommer":("komkommer",2,"st")
}
SIDES={
 "aardappel":("krieltjes",650,"g"),"zoete_aardappel":("zoete aardappel",650,"g"),
 "rijst":("zilvervliesrijst",180,"g"),"pasta":("volkoren pasta",180,"g"),
 "couscous":("volkoren couscous",180,"g"),
 "wraps":("volkoren wraps",4,"st"),
}
SELECTION_EXCLUSIONS=re.compile(
 r"vegetar|vegan|plantaardig|maaltijd|pizza|broodbeleg|saus|kruiden|spread|"
 r"burger|schnitzel|soep|stamppot|wrap met|sandwich|salade met|chips|"
 r"frikandel|gekruid|gemarineerde kipfilet in saus",re.I)
# Deze productgroepen hebben andere hoeveelheden/eenheden; niet zonder bewijs koppelen.
GROUPS={"proteine":PROTEINS,"groente":VEGETABLES,"bijgerecht":SIDES}

# Beproefde combinatiegroepen: een kortingspercentage is geen recept.
PAIRINGS={
 "kipfilet":("broccoli bloemkool spinazie wok courgette paprika champignons wortel tomaten sla spruiten","aardappel rijst pasta wraps"),
 "kipdij":("broccoli bloemkool spinazie wok courgette paprika champignons wortel tomaten spruiten","aardappel rijst zoete_aardappel"),
 "kipgehakt":("spinazie courgette paprika champignons tomaten wok broccoli","rijst pasta wraps"),
 "shoarma":("wok paprika courgette sla tomaten komkommer","wraps aardappel rijst"),
 "varkenshaas":("broccoli bloemkool champignons spruiten spinazie wortel","aardappel zoete_aardappel"),
 "gehakt":("broccoli bloemkool courgette paprika champignons tomaten spinazie wok wortel","aardappel pasta rijst wraps"),
 "zalm":("broccoli bloemkool spinazie courgette spruiten wortel","aardappel rijst pasta"),
 "gerookte_zalm":("spinazie courgette sla komkommer tomaten","pasta wraps"),
 "tonijn":("paprika tomaten sla komkommer courgette","pasta rijst wraps"),
 "tofu":("broccoli wok paprika courgette champignons wortel spinazie","rijst couscous"),
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
        if ("gratis" in typ or "1+1" in typ) and not (
                offer.get("multi_buy_quantity") and offer.get("multi_buy_price")):
            continue
        for role,group in GROUPS.items():
            for key in group:
                label,pattern,exclude=ING[key]
                if offer.get("unit") != group[key][-1]:continue
                if re.search(pattern,name,re.I) and not re.search(exclude,name,re.I):
                    if not re.search(r"mix van|groentemix met|aardappelgratin|soepgroenten",name,re.I):
                        grouped[role].setdefault(key,[]).append(offer)
    return grouped

def meal_candidates(offers,limit=65):
    """Selecteer gevarieerde complete maaltijden op basis van ACTIECOMBINATIES.

    Alleen combinations met 2+ verschillende soorten actieproducten.
    Productprijzen worden niet afgeleid; alle regels zijn 4 porties.
    """
    groups=classify_offers(offers)
    def strength(key,role):
        o=groups[role].get(key,[])
        return min(45,max((x.get("discount") or 0 for x in o),default=0))
    proteins=sorted(groups["proteine"],key=lambda x:-strength(x,"proteine"))
    veggies=sorted(groups["groente"],key=lambda x:-strength(x,"groente"))
    sides=sorted(groups["bijgerecht"],key=lambda x:-strength(x,"bijgerecht"))
    if not proteins or not veggies:return []
    scored=[]
    for pk in proteins:
        pname,cat,pamount,punit=PROTEINS[pk]
        for vk in veggies:
            if pk==vk or not sensible_meal(pk,vk):continue
            vname,vamount,vunit=VEGETABLES[vk]
            selected_sides=[None]+sides[:4]
            # Ook een tweede afgeprijsde groente kan een maaltijd compleet maken.
            # Alleen de eerste drie extra groenten beperken combinatorische groei.
            second_vegetables=[None]+[x for x in veggies if x!=vk][:3]
            for sk in selected_sides:
                for vk2 in second_vegetables:
                    if not sensible_meal(pk,vk,sk,vk2):continue
                    # Een tweede groente zonder bijgerecht is zinvol als
                    # koolhydraatbewuste maaltijd. Met bijgerecht max. 4 items.
                    ings=[(pk,pamount,punit),(vk,vamount,vunit)]
                    title=pname+" met "+vname
                    if vk2:
                        v2name,v2amount,v2unit=VEGETABLES[vk2]
                        # Voorkom absurd veel groente per 4 porties.
                        v2amount=round(v2amount*0.65) if v2unit=="g" else max(1,round(v2amount*0.65))
                        ings.append((vk2,v2amount,v2unit))
                        title+=", "+v2name
                    if sk:
                        sname,samount,sunit=SIDES[sk]
                        ings.append((sk,samount,sunit))
                        title+=" en "+sname
                    elif not vk2:
                        title+=" (koolhydraatbewust)"
                    offer_keys=2+bool(sk)+bool(vk2)
                    score=offer_keys*30+strength(pk,"proteine")+strength(vk,"groente")+(
                        strength(sk,"bijgerecht") if sk else 3)+(
                        strength(vk2,"groente") if vk2 else 0)
                    scored.append((score,pk,vk,sk,vk2,(title,cat,35,ings)))
    scored.sort(key=lambda x:(-x[0],x[1],x[2],str(x[3]),str(x[4])))
    # Beperk repetitieve varianten van hetzelfde eiwit & groente.
    selected=[];pair_count={};protein_count={};side_count={}
    for score,pk,vk,sk,vk2,recipe in scored:
        pair=(pk,vk)
        if pair_count.get(pair,0)>=3 or protein_count.get(pk,0)>=15:continue
        if sk and side_count.get(sk,0)>=20:continue
        pair_count[pair]=pair_count.get(pair,0)+1
        protein_count[pk]=protein_count.get(pk,0)+1
        if sk:side_count[sk]=side_count.get(sk,0)+1
        selected.append(recipe)
        if len(selected)>=limit:break
    return selected
