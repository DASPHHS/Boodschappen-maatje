"""Transactional PrijsProfeet v1 cursor sync, independently implemented from OpenAPI.
A complete bootstrap precedes deltas; a failed page never commits its cursor.
"""
from copy import deepcopy
from urllib.error import HTTPError

def valid_page(data):
    if data.get('retailer_filter'):raise ValueError('Retailer filter was not applied')
    if not isinstance(data.get('products'),list) or not isinstance(data.get('total'),int):raise ValueError('Invalid product page')
    return data['products'],data['total']

def cursor_page(data):
    if data.get('retailer_filter') or type(data.get('cursor')) is not int or type(data.get('has_more')) is not bool or not isinstance(data.get('changes'),list):raise ValueError('Invalid change feed')
    return data

def sync(retailer,previous,get):
    """get(path, params) handles transport/rate limits. State is scoped per retailer."""
    if previous and previous.get('retailer')==retailer and type(previous.get('cursor')) is int and isinstance(previous.get('products'),dict) and all(isinstance(p,dict) and p.get('product_id')==k and p.get('retailer')==retailer for k,p in previous['products'].items()):
        state=deepcopy(previous);mode='delta'
    else:state=None
    if state is None:return bootstrap(retailer,get)
    try:
        for _ in range(100):
            data=cursor_page(get('/products/changes',{'retailer':retailer,'cursor':state['cursor'],'limit':500}))
            for change in data['changes']:
                if change.get('retailer')!=retailer:raise ValueError('Mixed retailer in change feed')
                key=change.get('product_id');op=change.get('change')
                if not isinstance(key,str) or not key:raise ValueError('Missing change identity')
                if op=='delete':state['products'].pop(key,None)
                elif op=='upsert':
                    product=change.get('product')
                    if not isinstance(product,dict) or product.get('product_id')!=key or product.get('retailer')!=retailer:raise ValueError('Conflicting upsert identity')
                    state['products'][key]=product
                else:raise ValueError('Unknown change operation')
            if data['has_more'] and data['cursor']==state['cursor']:raise ValueError('Non-advancing cursor')
            state['cursor']=data['cursor'];state['as_of']=data.get('as_of')
            if not data['has_more']:return state,mode
        raise ValueError('Change feed pagination exceeded')
    except HTTPError as exc:
        if exc.code!=410:raise
        return bootstrap(retailer,get)

def bootstrap(retailer,get):
    # Capture BEFORE full sync; later deltas replay concurrent updates safely.
    cursor=cursor_page(get('/products/changes',{'retailer':retailer}))
    products={};expected=None;seen=0
    for page in range(1,151):
        rows,total=valid_page(get('/products',{'retailer':retailer,'page':page,'page_size':100,'sort_by':'product_id','sort_order':'asc'}))
        if expected is None:expected=total
        if total!=expected:raise ValueError('Catalog changed during bootstrap; retry next run')
        for product in rows:
            key=product.get('product_id')
            if not key or product.get('retailer')!=retailer:raise ValueError('Invalid bootstrap product identity')
            if key in products:raise ValueError('Duplicate identity across bootstrap pages')
            products[key]=product
        seen+=len(rows)
        if seen>=expected:
            if seen!=expected:raise ValueError('Wrong bootstrap row count')
            return {'retailer':retailer,'cursor':cursor['cursor'],'as_of':cursor.get('as_of'),'products':products},'bootstrap'
        if len(rows)<100:raise ValueError('Incomplete bootstrap page')
    raise ValueError('Bootstrap pagination exceeded')
