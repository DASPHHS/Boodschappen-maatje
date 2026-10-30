#!/usr/bin/env python3
"""Wait for the actual live assets, not an assumed Pages deployment duration."""
import hashlib
import time
from pathlib import Path
from urllib.request import Request, urlopen
BASE='https://dasphhs.github.io/Boodschappen-maatje/docs/'
FILES=('app.js','product-semantics.js','product-resolver.js','catalog-search.js','price-observations.js','recipe-shop-options.js','style.css')
def same(local,remote):return hashlib.sha256(local).digest()==hashlib.sha256(remote).digest()
def main():
    root=Path(__file__).resolve().parents[1]/'docs'
    expected={name:(root/name).read_bytes() for name in FILES}
    deadline=time.monotonic()+300;attempt=0;reason='not checked'
    while time.monotonic()<deadline:
        attempt+=1
        try:
            for name,data in expected.items():
                req=Request(BASE+name+'?buildcheck='+str(time.time_ns()),headers={'Cache-Control':'no-cache','User-Agent':'Boodschappenmaatje/1.0 deployment-check'})
                with urlopen(req,timeout=10) as response:actual=response.read(1000000)
                if not same(data,actual):raise ValueError('previous asset version: '+name)
            print('Published assets match this checkout; live behavior test may start.')
            return 0
        except Exception as exc:reason=str(exc)[:200]
        time.sleep(min(10,max(0,deadline-time.monotonic())))
    raise SystemExit('Pages did not publish expected assets within five minutes: '+reason)
if __name__=='__main__':main()
