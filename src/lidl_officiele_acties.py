"""Gedateerde, controleerbare Lidl-aanvulling bij een onvolledige API-feed.

Alleen officieel vermelde producten; geen automatische prijsverlenging.
Een Lidl Plus-prijs is geen algemene korting en wordt nooit als zodanig geteld.
Deze momentopname is geen vervanging voor automatische bronontdekking.
"""
from datetime import date

SOURCE = "Lidl.nl officiële aanbiedingen (controle week 44, 2026)"
URL = "https://www.lidl.nl/c/aanbiedingen/a10008785"
# naam, prijs, verpakking, eenheid, oude prijs, Lidl Plus, geldig vanaf, geldig t/m
ROWS = (
 ("Fijngesneden boerenkool",1.49,500,"g",1.99,True,"2026-10-26","2026-11-01"),
 ("SALADINETTES Aardappelschijfjes",0.99,700,"g",1.29,True,"2026-10-26","2026-11-01"),
 ("VEMONDO Plantaardige hamburgers",1.89,227,"g",2.19,True,"2026-10-26","2026-11-01"),
 ("Runderriblappen",8.99,700,"g",10.96,True,"2026-10-26","2026-11-01"),
 ("Scharrelkipdijreepjes shoarma",4.79,500,"g",5.99,True,"2026-10-26","2026-11-01"),
 ("CHEF SELECT Aardappelgratin",1.79,450,"g",2.15,False,"2026-10-26","2026-11-01"),
 ("MILBONA Goudse belegen stuk 48+",6.99,910,"g",8.45,True,"2026-10-26","2026-11-01"),
 ("CHEF SELECT Maaltijdsalade Caesar",2.49,None,None,None,True,"2026-10-26","2026-11-01"),
 ("ALESTO Cashewnoten",4.99,500,"g",None,False,"2026-10-26","2026-11-01"),
 ("BELLAROM Koffie goud",7.99,1000,"g",None,False,"2026-10-26","2026-11-01"),
 ("Extra mager rundergehakt",9.99,750,"g",None,False,"2026-10-12","2026-11-22"),
 ("Verse zalmfilet op huid",7.99,500,"g",None,False,"2026-10-26","2026-11-01"),
 ("Hamlappen",7.99,960,"g",None,False,"2026-10-26","2026-11-01"),
 ("Gekruide varkensoester",4.49,300,"g",None,False,"2026-10-26","2026-11-01"),
 ("MILBONA Smeerkaas naturel 48+",0.99,None,None,None,True,"2026-10-30","2026-11-01"),
 ("Kogelbiefstuk",6.99,350,"g",8.39,True,"2026-10-30","2026-11-05"),
 ("Rustiek meergranen desem",1.69,None,None,2.19,True,"2026-10-30","2026-11-01"),
)

def supplement(offers, upcoming, today, horizon_days=7):
    """Vul alleen hiaten; laat bewezen feedmatches met zelfde naam intact."""
    from datetime import timedelta
    import unicodedata
    import re
    if isinstance(today,str):
        today=date.fromisoformat(today)
    def norm(value):
        value=unicodedata.normalize("NFKD",value.lower())
        value="".join(ch for ch in value if not unicodedata.combining(ch))
        return re.sub(r"\s+"," ",re.sub(r"[^\w\s]"," ",value)).strip()
    for name,price,quantity,unit,original,loyalty,start,end in ROWS:
        first=date.fromisoformat(start)
        last=date.fromisoformat(end)
        if last<today or first>today+timedelta(days=horizon_days):
            continue
        dest=offers["lidl"] if first<=today else upcoming["lidl"]
        if any(norm(item.get("name",""))==norm(name) for item in dest):
            continue
        dest.append({
            "name":name,"norm":norm(name),"price":price,"quantity":quantity,
            "unit":unit,"size_label":f"{quantity} {unit}" if quantity else "Verpakking: zie winkel",
            "original_price":original,"multi_buy_quantity":None,"multi_buy_price":None,
            "promotion_type":"Lidl Plus" if loyalty else "Officiële weekaanbieding",
            "valid_from":start,"valid_until":end,
            "discount":round((1-price/original)*100,1) if original else None,
            "url":URL,"ean":"","source":SOURCE,"is_loyalty":loyalty
        })
