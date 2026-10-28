"""Local-only approved test change. No API endpoint can modify production targets."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--token')
p.add_argument('--harden',action='store_true')
a=p.parse_args()
path=Path(__file__).resolve().parents[1]/'infrastructure/fixture/config.json'
data=json.loads(path.read_text())
if a.token:data['verification_token']=a.token
if a.harden:data['hardened']=True
path.write_text(json.dumps(data))
print('Isolated fixture updated; production systems were not contacted.')
