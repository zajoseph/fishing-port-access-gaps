"""Sea-route distances: per-tile MCP least-cost paths on 100 m ocean raster, stitched at portal lines,
then any-angle smoothing and geodesic length. Usage: python3 route.py [extra_points.csv]"""
import numpy as np, pandas as pd, pickle, sys, time, heapq
from skimage.graph import MCP_Geometric
from common import *
from frame import inv
PORTAL_X={'SM':450.0,'MN':1270.0}; PORTAL_STEP=20   # cells (2 km)
RELAX_COST=1.5
TB={'S':(-30,480,-15,340),'M':(420,1300,250,430),'N':(1240,1920,-40,370)}
def home_tile(x,y):
    cands=tiles_for(x,y)
    return min(cands,key=lambda n: abs(x-(TB[n][0]+TB[n][1])/2)) if cands else None
def load_points(extra=None):
    p=ports()[['port_id','lat','lon','x','y']].rename(columns={'port_id':'id'}); p['kind']='harbor'
    if extra:
        e=pd.read_csv(extra); from frame import fwd
        e['x'],e['y']=fwd(e.lat.values,e.lon.values); e['kind']='ref'; p=pd.concat([p,e[['id','lat','lon','x','y','kind']]],ignore_index=True)
    return p
def snap_points(P):
    from scipy import ndimage
    out=[]
    for n in 'SMN':
        oc=tile(n)['ocean']; d,(ir,ic)=ndimage.distance_transform_edt(~oc,return_indices=True)
        for i,q in P.iterrows():
            if home_tile(q.x,q.y)!=n: continue
            r,c=to_rc(n,q.x,q.y); out.append((q['id'],n,int(ir[r,c]),int(ic[r,c]),d[r,c]*100))
        del d,ir,ic
    return pd.DataFrame(out,columns=['id','tile','r','c','snap_frame_m'])
def portals():
    pts={}
    for key,X in PORTAL_X.items():
        a,b=key[0],key[1]; lst=[]
        ra,ca=None,None
        ylo=max(TB[a][2],TB[b][2])+1; yhi=min(TB[a][3],TB[b][3])-1
        ys=np.arange(ylo,yhi,0.1*PORTAL_STEP)
        for y in ys:
            r1,c1=to_rc(a,X,y); r2,c2=to_rc(b,X,y)
            if tile(a)['ocean'][r1,c1] and tile(b)['ocean'][r2,c2]: lst.append((f'P{key}_{y:.1f}',{a:(int(r1),int(c1)),b:(int(r2),int(c2))}))
        pts[key]=lst
    return pts
def run(extra=None):
    P=load_points(extra); S=snap_points(P); PT=portals()
    nodes={}  # node -> {tile:(r,c)}
    for _,s in S.iterrows(): nodes[s['id']]={s.tile:(s.r,s.c)}
    for key,lst in PT.items():
        for nm,d in lst: nodes[nm]=d
    print('portals',{k:len(v) for k,v in PT.items()},flush=True)
    import os
    TILES_RUN=os.environ.get('TILES','SMN'); prev=os.environ.get('PREV')
    edges={}; paths={}
    if prev:
        old=pickle.load(open(prev,'rb'))
        for k in old['edges']:
            if k[2] not in TILES_RUN: edges[k]=old['edges'][k]; paths[k]=old['paths'][k]
    for n in TILES_RUN:
        T=tile(n); oc=T['ocean']; relaxed=oc&(T['landfrac'].astype(np.float32)>=0.5)
        costarr=np.where(oc,np.where(relaxed,RELAX_COST,1.0),-1.0)
        tn=[k for k,v in nodes.items() if n in v]
        hs=[k for k in tn if not k.startswith('P')]
        ps=[k for k in tn if k.startswith('P')]
        # sources: all harbors; portals only if tile has 2 portal lines (M) -> portal-to-portal
        srcs=hs+(ps if n=='M' else [])
        t0=time.time()
        for si,s in enumerate(srcs):
            m=MCP_Geometric(costarr,fully_connected=True)
            ends=[nodes[k][n] for k in tn if k!=s]
            cum,_=m.find_costs([nodes[s][n]],ends=ends,find_all_ends=True)
            for k in tn:
                if k==s: continue
                if s.startswith('P') and k.startswith('P') and k.split('_')[0]==s.split('_')[0]: continue
                rc=nodes[k][n]; cst=cum[rc]
                if not np.isfinite(cst): continue
                edges[(s,k,n)]=cst*0.1
                paths[(s,k,n)]=np.array(m.traceback(rc),dtype=np.int16)
            if si%10==0: print(n,si,len(srcs),round(time.time()-t0),flush=True)
        del m
    pickle.dump(dict(P=P,S=S,nodes=nodes,edges=edges,paths=paths),open(f'route_raw{"_"+extra.split(".")[0] if extra else ""}.pkl','wb'))
if __name__=='__main__': run(sys.argv[1] if len(sys.argv)>1 else None)
