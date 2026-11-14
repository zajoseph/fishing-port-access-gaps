"""Pipeline: OSM land (+water carve) -> 100 m tiles -> harbor zones (only where needed) -> thin-barrier fixes."""
import numpy as np, subprocess, sys
from scipy import ndimage
from common import *
import barriers
ZONE_KM=3.0; RELAX=0.75
def zone_mask(shape,n,ids,p):
    zone=np.zeros(shape,bool); R=int(ZONE_KM/0.1)
    for _,q in p[p.port_id.isin(ids)].iterrows():
        if n not in tiles_for(q.x,q.y): continue
        r,c=to_rc(n,q.x,q.y); r0,r1=max(r-R,0),min(r+R+1,shape[0]); c0,c1=max(c-R,0),min(c+R+1,shape[1])
        yy,xx=np.ogrid[r0:r1,c0:c1]; zone[r0:r1,c0:c1]|=((yy-r)**2+(xx-c)**2)<=R*R
    return zone
def make(n,ids,p,T):
    z=dict(np.load(f'base_{n}.npz')); lf=z['landfrac'].astype(np.float32)
    zone=zone_mask(lf.shape,n,ids,p); water=(lf<0.5)|(zone&(lf<RELAX))
    z.update(water=water,zone=zone,ocean=water); np.savez_compressed(f'tile_{n}.npz',**z)
    barriers.apply(n,T); burn(n,p)
def burn(n,p,half_km=1.0):
    import os, pandas as pd
    from frame import fwd
    if not os.path.exists('burn_spots.csv'): return
    B=pd.read_csv('burn_spots.csv'); z=dict(np.load(f'tile_{n}.npz')); lf=z['landfrac'].astype(np.float32)
    water=z['water'].copy(); H=int(half_km/0.1); nb=0
    for b in B.itertuples():
        x,y=fwd(b.lat,b.lon)
        if n not in tiles_for(float(x),float(y)): continue
        H=int(getattr(b,'half_km',half_km)/0.1); r,c=to_rc(n,x,y); r0,r1=max(r-H,0),min(r+H+1,lf.shape[0]); c0,c1=max(c-H,0),min(c+H+1,lf.shape[1])
        k=(lf[r0:r1,c0:c1]>0)&water[r0:r1,c0:c1]
        if not bool(getattr(b,'force',False)): k&=~z['zone'][r0:r1,c0:c1]
        water[r0:r1,c0:c1]&=~k; nb+=int(k.sum())
    lab,nl=ndimage.label(water,structure=np.ones((3,3))); s=np.bincount(lab.ravel()); s[0]=0
    z.update(water=water,ocean=lab==s.argmax()); np.savez_compressed(f'tile_{n}.npz',**z)
    print(n,'burned cells',nb,flush=True)
def need(n,p):
    t=tile(n); oc=t['ocean']; d=ndimage.distance_transform_edt(~oc); lf=t['landfrac'].astype(np.float32); out=[]
    for _,q in p.iterrows():
        if n not in tiles_for(q.x,q.y): continue
        r,c=to_rc(n,q.x,q.y)
        if d[r,c]*0.1<=0.3: continue
        R=int(ZONE_KM/0.1); r0,r1=max(r-R-60,0),min(r+R+61,lf.shape[0]); c0,c1=max(c-R-60,0),min(c+R+61,lf.shape[1])
        loc=oc[r0:r1,c0:c1]|zone_mask(lf.shape,n,[q.port_id],p)[r0:r1,c0:c1]&(lf[r0:r1,c0:c1]<RELAX)
        lab,_=ndimage.label(loc,structure=np.ones((3,3)))
        seed=oc[r0:r1,c0:c1]; keep=np.isin(lab,np.unique(lab[seed])) & (lab>0)
        dd=ndimage.distance_transform_edt(~keep)[r-r0,c-c0]*0.1
        if d[r,c]*0.1-dd>0.3: out.append(q.port_id)
    return out
if __name__=='__main__':
    p=ports(); T=barriers.split_table(); T_=None
    for n in (sys.argv[1:] or 'SMN'):
        ids=[]
        for it in range(4):
            make(n,ids,p,T); add=[i for i in need(n,p) if i not in ids]
            print(n,'iteration',it,'zones',ids,'add',add,flush=True)
            if not add: break
            ids+=add
