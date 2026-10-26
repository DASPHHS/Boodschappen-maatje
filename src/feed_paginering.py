"""Controleer API-paginering zonder schijnvolledigheid.

Dezelfde volledige pagina twee keer achtereen wijst op genegeerde
page-parameters. Zo'n feed is NIET compleet, ook als HTTP 200 terugkomt.
"""
import hashlib, json

def page_fingerprint(rows):
    signature=[(x.get("id"),x.get("base_product_id"),x.get("name"),
                x.get("price"),x.get("valid_from")) for x in rows if isinstance(x,dict)]
    return hashlib.sha256(json.dumps(signature,sort_keys=True,default=str).encode()).hexdigest()

def pagination_issue(current_rows,seen_fingerprints,page,total=None,page_size=100):
    if not isinstance(current_rows,list):
        return "ongeldig_formaat"
    if len(current_rows)>page_size:
        return "pagina_groter_dan_gevraagd"
    if current_rows and page_fingerprint(current_rows) in seen_fingerprints:
        return "herhaalde_pagina"
    if isinstance(total,int) and total<0:
        return "ongeldig_totaal"
    if page>1 and not current_rows and isinstance(total,int) and (page-1)*page_size<total:
        return "voortijdig_lege_pagina"
    return None
