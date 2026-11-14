"""Topological land-crossing test: a land run is a CROSSING if the water just before and just after it are
not 4-connected within a 3 km x 3 km window of the 25 m vector water mask (OSM land minus OSM water).
Corner grazes of headlands stay connected around the corner; crossings of spits/peninsulas do not."""
import numpy as np, pickle, sys, pandas as pd
from scipy import ndimage
from frame import fwd, inv
from landcheck import TB, L
HALF=60  # 25 m pixels -> 1.5 km half-window
def tile_of(x,y):
    for n,(x0,x1,y0,y1) in TB.items():
        if x0+1.6<x<x1-1.6 and y0+1.6<y<y1-1.6: return n
def px(n,x,y):
    x0,x1,y0,y1=TB[n]; return int((y1-y)/0.025), int((x-x0)/0.025)
cache={}
def connected(xa,ya,xb,yb):
    n=tile_of((xa+xb)/2,(ya+yb)/2)
    if n is None: return True
    ra,ca=px(n,xa,ya); rb,cb=px(n,xb,yb); rm,cm=(ra+rb)//2,(ca+cb)//2
    key=(n,rm//8,cm//8,ra,ca,rb,cb)
    if key in cache: return cache[key]
    r0,c0=rm-HALF,cm-HALF
    sub=np.unpackbits(L[n][r0:rm+HALF],axis=1)[:,c0:cm+HALF]==0
    lab,_=ndimage.label(sub)
    la=lab[ra-r0,ca-c0]; lb=lab[rb-r0,cb-c0]
    ok=bool(la and lb and la==lb); cache[key]=ok; return ok
def runs(poly,step=0.025):
    from landcheck import land_at
    x,y=fwd(poly[:,0],poly[:,1]); xs=[];ys=[]
    for i in range(len(x)-1):
        n=max(int(np.hypot(x[i+1]-x[i],y[i+1]-y[i])/step),1); t=np.arange(n)/n; xs.append(x[i]+t*(x[i+1]-x[i])); ys.append(y[i]+t*(y[i+1]-y[i]))
    xs=np.concatenate(xs+[x[-1:]]); ys=np.concatenate(ys+[y[-1:]]); ld=land_at(xs,ys)
    d=np.diff(np.r_[0,ld.astype(int),0]); st=np.where(d==1)[0]; en=np.where(d==-1)[0]
    out=[]
    for s,e in zip(st,en):
        if s==0 or e>=len(xs): out.append(('endpoint',(e-s)*25,xs[s],ys[s])); continue
        ok=connected(xs[s-1],ys[s-1],xs[e],ys[e])
        out.append(('graze' if ok else 'CROSSING',(e-s)*25,xs[(s+e)//2],ys[(s+e)//2]))
    return out
if __name__=='__main__':
    res,geoms=pickle.load(open(sys.argv[1],'rb')); rows=[]
    for (a,b),g in geoms.items():
        if a<b:
            for kind,length,x,y in runs(g):
                if kind!='graze':
                    la,lo=inv(x,y); rows.append((a,b,kind,length,round(float(la),5),round(float(lo),5)))
    df=pd.DataFrame(rows,columns=['a','b','kind','run_m','lat','lon']); df.to_csv(sys.argv[2],index=False)
    print(df.kind.value_counts()); print(df[df.kind=='CROSSING'].groupby(['lat','lon']).size().sort_values(ascending=False).head(20))
