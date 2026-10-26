"""Repeatable local inventory and data-integrity audit; never fetches or alters prices."""
import ast,json,sys
from datetime import date,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]

def audit():
 from receptenradar_checks import validate_publication
 from product_compatibiliteit import recipe_line_errors
 data=json.loads((ROOT/'recepten/data.json').read_text())
 today=datetime.now(ZoneInfo('Europe/Amsterdam')).date().isoformat()
 inventory=[]
 for path in sorted((ROOT/'src').glob('*.py')):
  tree=ast.parse(path.read_text());inventory.append({'file':str(path.relative_to(ROOT)),'functions':sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in ast.walk(tree)),'lines':len(path.read_text().splitlines())})
 checked=validate_publication(data['recipes'])
 matching_errors=[{'store':s,'recipe':r['title'],'errors':recipe_line_errors(r)} for s,recipes in data['recipes'].items() for r in recipes if recipe_line_errors(r)]
 stores={}
 for s in data['store_names']:
  offers=data['deals'][s];valid=[]
  for p in offers:
   start=p.get('valid_from') or '';end=p.get('valid_until') or ''
   try:date.fromisoformat(start);date.fromisoformat(end)
   except ValueError:continue
   if start<=today<=end:valid.append(p)
  stores[s]={'regular_prices':data['counts']['ordinary'][s],'promotion_mentions':len(offers),'date_confirmed_current':len(valid),'mathematically_verified_discounts':sum(bool(x.get('discount_verified')) for x in valid),'complete_recipes':sum(bool(r.get('complete')) for r in data['recipes'][s])}
 return {'checked_on':today,'source_import':data['updated_at'],'recipe_calculations_validated':checked,'ingredient_safety_errors':matching_errors,'stores':stores,'python_inventory':inventory,'workflows':[str(p.relative_to(ROOT)) for p in sorted((ROOT/'.github/workflows').glob('*.yml'))],'limits':['Shelf import is not a fresh retailer verification','Pantry, delivery and unverified drained weights remain outside exact total','External recipe title index is not a fully priced verified recipe','No cross-device account sync or reliable historical low-price score']}
if __name__=='__main__':
 result=audit();(ROOT/'docs/platform-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps({k:v for k,v in result.items() if k!='python_inventory'},ensure_ascii=False))
 if result['ingredient_safety_errors']:sys.exit(1)
