"""Shared ingredient typing through the exact same parser used in the website."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PROFILE_VERSION=2

def profiles(raw):
    result=subprocess.run(['node',str(ROOT/'scripts/recipe_profiles.cjs')],
        input=json.dumps([x for x in raw if isinstance(x,str)]),text=True,capture_output=True,check=True,timeout=8)
    return json.loads(result.stdout)
