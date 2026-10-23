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
            if pk==vk:continue
            vname,vamount,vunit=VEGETABLES[vk]
            selected_sides=[None]+sides[:4]
            for sk in selected_sides:
                # Altijd minstens 2 bevestigde categorieën in de aanbieding.
                ings=[(pk,pamount,punit),(vk,vamount,vunit)]
                title=pname+" met "+vname
                if sk:
                    sname,samount,sunit=SIDES[sk]
                    ings.append((sk,samount,sunit))
                    title+=" en "+sname
                else:
                    # Geen zetmeelbron nodig voor een goede eiwitrijke maaltijd;
                    # voeg extra groente toe als mogelijke lunch/avondmaaltijd.
                    title+=" (koolhydraatbewust)"
                offer_keys=sum(bool(groups[r].get(k)) for r,k in
                               [("proteine",pk),("groente",vk),("bijgerecht",sk)] if k)
                score=offer_keys*20+strength(pk,"proteine")+strength(vk,"groente")+(
                    strength(sk,"bijgerecht") if sk else 3)
                scored.append((score,pk,vk,sk,(title,cat,35,ings)))
    scored.sort(key=lambda x:(-x[0],x[1],x[2],str(x[3])))
    # Beperk repetitieve varianten van hetzelfde eiwit & groente.
    selected=[];pair_count={};protein_count={};side_count={}
    for score,pk,vk,sk,recipe in scored:
        pair=(pk,vk)
        if pair_count.get(pair,0)>=2 or protein_count.get(pk,0)>=15:continue
        if sk and side_count.get(sk,0)>=20:continue
        pair_count[pair]=pair_count.get(pair,0)+1
        protein_count[pk]=protein_count.get(pk,0)+1
        if sk:side_count[sk]=side_count.get(sk,0)+1
        selected.append(recipe)
        if len(selected)>=limit:break
    return selected
