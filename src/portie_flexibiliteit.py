"""Beperkte, transparante receptflexibiliteit om onnodige extra verpakkingen te vermijden.

Gebruik alleen een iets kleinere hoeveelheid wanneer vier porties
culinair geloofwaardig blijven. Reken de aangepaste voedingswaarden opnieuw.
"""
FLEXIBLE_GRAMS={"kipfilet","kipdij","kipgehakt","shoarma","gehakt",
                "varkenshaas","zalm","gerookte_zalm","tofu",
                "wok","spinazie","broccoli","spruiten","boerenkool",
                "bloemkool","paprika","courgette","champignons",
                "wortel","tomaten","sla"}
PROTEIN_KEYS={"kipfilet","kipdij","kipgehakt","shoarma","gehakt",
              "varkenshaas","zalm","gerookte_zalm","tofu"}

def needed_quantity(ingredient,required,unit,package_size):
    """Geeft aangepaste hoeveelheid terug, niet het gewicht van een hele kassamand.

    Maximaal 10% verschil, maximaal 75 g voor eiwitten en 100 g voor groente.
    Alleen als een geheel aantal verpakkingen nét onder de receptbehoefte ligt.
    """
    if unit!="g" or ingredient not in FLEXIBLE_GRAMS or not package_size or required<=0:
        return required
    max_shortage=min(required*0.10,75 if ingredient in PROTEIN_KEYS else 100)
    packs=int(required//package_size)
    if packs<=0:
        return required
    available=packs*package_size
    if 0<required-available<=max_shortage+1e-8:
        return available
    return required
