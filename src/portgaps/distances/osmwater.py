import json, numpy as np
def assemble(ways):
    """ways: list of [(lon,lat),...]; join by endpoints into closed rings."""
    ways=[list(map(tuple,w)) for w in ways if len(w)>=2]; rings=[]
    while ways:
        cur=ways.pop(0)
        changed=True
        while cur[0]!=cur[-1] and changed:
            changed=False
            for i,w in enumerate(ways):
                if w[0]==cur[-1]: cur=cur+w[1:]
                elif w[-1]==cur[-1]: cur=cur+w[::-1][1:]
                elif w[-1]==cur[0]: cur=w+cur[1:]
                elif w[0]==cur[0]: cur=w[::-1]+cur[1:]
                else: continue
                ways.pop(i); changed=True; break
        if len(cur)>=4 and cur[0]==cur[-1]: rings.append(np.array(cur))
    return rings
def load(fn, include_marina=False):
    d=json.load(open(fn)); polys=[]  # (kind, outers, inners, tags, id)
    for e in d['elements']:
        tg=e.get('tags',{})
        if tg.get('leisure')=='marina' and tg.get('natural')!='water' and not include_marina: continue
        if e['type']=='way' and 'geometry' in e:
            g=[(p['lon'],p['lat']) for p in e['geometry']]
            if len(g)>=4 and g[0]==g[-1]: polys.append(('way',[np.array(g)],[],tg,e['id']))
        elif e['type']=='relation':
            outs=[[(p['lon'],p['lat']) for p in m['geometry']] for m in e.get('members',[]) if m.get('role')=='outer' and 'geometry' in m]
            ins=[[(p['lon'],p['lat']) for p in m['geometry']] for m in e.get('members',[]) if m.get('role')=='inner' and 'geometry' in m]
            polys.append(('relation',assemble(outs),assemble(ins),tg,e['id']))
    return polys
