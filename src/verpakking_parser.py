"""Uniforme verpakkingsherkenning voor actuele én toekomstige productacties.

Voorkom dat "1 stuk ca. 405 g" als 1 stuk wordt gematcht op een
receptingrediënt van 800 gram. Geen onbekende hoeveelheden verzinnen.
"""
import math,re

MULTI=re.compile(r"(?<!\d)(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*(kg|gram|gr|g|liter|l|ml|cl)\b",re.I)
MASS=re.compile(r"(?<![\d\w])(\d+(?:[.,]\d+)?)\s*(kg|gram|gr|g|liter|l|ml|cl)\b",re.I)
PIECES=re.compile(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(stuks?|st|stukken)\b",re.I)
UNIT={"kg":("g",1000),"gram":("g",1),"gr":("g",1),"g":("g",1),
      "liter":("ml",1000),"l":("ml",1000),"cl":("ml",10),"ml":("ml",1)}
def _weight(match,multiple=1,is_multi=False):
    n=float(match.group(2 if is_multi else 1).replace(",","."))
    u=match.group(3 if is_multi else 2).lower()
    unit,factor=UNIT[u]
    q=n*factor*multiple
    return (round(q,4),unit) if math.isfinite(q) and 0<q<=100000 else (None,None)

def parse_packaging(product):
    # Explicit package size first; also check the product title for grams.
    # For meat sold by the piece, the listed approximate weight is preferable.
    candidates=[str(product.get(k) or "") for k in ("size","quantity_label","package_size","name","quantity")]
    for value in candidates:
        multi=MULTI.search(value)
        if multi:
            count=int(multi.group(1))
            q,unit=_weight(multi,count,is_multi=True)
            if q:return q,unit
        single=MASS.search(value)
        if single:
            q,unit=_weight(single)
            if q:return q,unit
    for value in candidates:
        match=PIECES.search(value)
        if match:
            n=float(match.group(1).replace(",","."))
            if 0<n<=1000:return n,"st"
        if value.strip().lower() in ("stuk","per stuk","st"):return 1,"st"
    return None,None
