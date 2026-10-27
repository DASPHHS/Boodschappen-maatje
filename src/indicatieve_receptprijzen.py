"""Indicatieve prijs per supermarkt voor expliciet als variant gemarkeerde recepten.

Geen claim van originele receptingrediënten. Bij ontbrekende assortimentprijs
wordt geen volledige basisvariantprijs gepubliceerd.
"""
import json
from pathlib import Path
from receptvarianten_schatting import candidates
from receptenradar_v2 import ingredient_price, ING

ROOT=Path(__file__).resolve().parents[1]
def load_index(root=ROOT):
    p=Path(root)/"recepten"/"inspiratie.json"
    if not p.exists():return []
    try:return json.loads(p.read_text(encoding="utf-8")).get("items",[])
    except (ValueError,OSError,AttributeError):return []

def build(shelves,offers,items=None,limit=450):
    source=candidates(items if items is not None else load_index(),limit=limit)
    output={}
    for store in shelves:
        rows=[];cached={}
        for recipe in source:
            lines=[];missing=[]
            for key,amount,unit in recipe["ingredients"]:
                token=(key,amount,unit)
                if token not in cached:
                    cached[token]=ingredient_price(key,amount,unit,shelves[store],offers.get(store,[]))
                line=cached[token]
                if line:lines.append(line)
                else:missing.append(key)
            if missing:continue
            rows.append({
                "title":recipe["title"],"original_title":recipe["original_title"],
                "cuisine":recipe.get("cuisine"),"source":recipe.get("source"),
                "url":recipe.get("url"),"price_status":"partial_estimate",
                "checkout":round(sum(x["cash_price"] for x in lines),2),
                "per_serving":round(sum(x["cash_price"] for x in lines)/4,2),
                "sale_count":sum(bool(x.get("sale")) for x in lines),
                "ingredients":lines,
                "assumptions":recipe["assumptions"],
                "not_full_recipe":True,
                "servings":4
            })
        rows.sort(key=lambda x:(-x["sale_count"],x["checkout"]))
        output[store]=rows
    return output
