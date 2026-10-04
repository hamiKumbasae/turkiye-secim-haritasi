"""Validate public data. Unresolved historical records are individually fingerprinted."""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def issues(data):
 for level in ('iller','ilceler'):
  seen=set()
  for r in data.get(level,[]):
   ident=str(r.get('geomId') or r.get('plaka'))+':'+r['ad']
   if ident in seen:yield level,ident,'duplicate'
   seen.add(ident)
   if r.get('katilim') is not None and not 0<=r['katilim']<=100:yield level,ident,'turnout-range'
   for party,v in r.get('oy',{}).items():
    for field in ('oran','oranSandalye'):
     if v.get(field) is not None and not 0<=v[field]<=100:yield level,ident,'percent-range:'+party
    if v.get('oy') is not None and (not isinstance(v['oy'],int) or v['oy']<0):yield level,ident,'vote-count:'+party
   valid=r.get('gecerliOy');votes=[v.get('oy') for v in r.get('oy',{}).values()]
   if valid and votes and all(v is not None for v in votes) and abs(sum(votes)-valid)>max(1,valid*.0001):yield level,ident,'vote-scope'
   if valid and votes and all(v is not None for v in votes) and abs(sum(votes)-valid)<=max(1,valid*.0001):
    if any(v.get('oran') is not None and abs(v['oran']-v['oy']/valid*100)>.11 for v in r['oy'].values()):yield level,ident,'percent-count'
   if r.get('secmen') and valid and valid>r['secmen']:yield level,ident,'valid-exceeds-voters'
 if data.get('tur')=='genel' and data.get('toplamSandalye') is not None:
  if sum(sum(r.get('vekil',{}).values()) for r in data['iller'])!=data['toplamSandalye']:yield 'iller','total','seat-total'
def snapshot():
 found={}
 for folder in ('elections','meclis_harita'):
  for p in sorted((ROOT/'data/normalized'/folder).rglob('*.json')):
   d=json.loads(p.read_text())
   for level,ident,code in issues(d):
    if code not in ('vote-scope','valid-exceeds-voters','duplicate','percent-count'):raise ValueError(f'{p.name}: {ident}: {code}')
    r=[x for x in d[level] if str(x.get('geomId') or x.get('plaka'))+':'+x['ad']==ident]
    found[f'{folder}/{p.stem}/{level}/{ident}/{code}']=hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 return found
if __name__=='__main__':
 try:
  actual=snapshot();expected=json.loads((ROOT/'tests/fixtures/known-validation-issues.json').read_text())
  new={k:v for k,v in actual.items() if expected.get(k)!=v}
  if new:raise ValueError('New or changed unresolved records:\n'+'\n'.join(new))
  print(f'Data checks passed; {len(actual)} documented findings require source verification.')
 except (ValueError,FileNotFoundError) as error:print(error,file=sys.stderr);sys.exit(1)
