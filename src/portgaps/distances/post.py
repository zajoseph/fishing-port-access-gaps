import numpy as np, pandas as pd, pickle, sys, heapq, itertools, json
from common import *
from frame import inv
NM=1.852
def vincenty(lat1,lon1,lat2,lon2):
    a=6378137.0; f=1/298.257223563; b=(1-f)*a
    L=np.radians(lon2-lon1); U1=np.arctan((1-f)*np.tan(np.radians(lat1))); U2=np.arctan((1-f)*np.tan(np.radians(lat2)))
    sU1,cU1,sU2,cU2=np.sin(U1),np.cos(U1),np.sin(U2),np.cos(U2); lam=L.copy()
    for _ in range(200):
        sl,cl=np.sin(lam),np.cos(lam)
        ss=np.sqrt((cU2*sl)**2+(cU1*sU2-sU1*cU2*cl)**2); cs=sU1*sU2+cU1*cU2*cl; sig=np.arctan2(ss,cs)
        sa=np.where(ss==0,0,cU1*cU2*sl/np.where(ss==0,1,ss)); c2a=1-sa**2
        c2sm=np.where(c2a==0,0,cs-2*sU1*sU2/np.where(c2a==0,1,c2a))
        C=f/16*c2a*(4+f*(4-3*c2a)); lp=lam
        lam=L+(1-C)*f*sa*(sig+C*ss*(c2sm+C*cs*(-1+2*c2sm**2)))
        if np.all(np.abs(lam-lp)<1e-12): break
    u2=c2a*(a*a-b*b)/(b*b); A=1+u2/16384*(4096+u2*(-768+u2*(320-175*u2))); B=u2/1024*(256+u2*(-128+u2*(74-47*u2)))
    ds=B*ss*(c2sm+B/4*(cs*(-1+2*c2sm**2)-B/6*c2sm*(-3+4*ss**2)*(-3+4*c2sm**2)))
    return b*A*(sig-ds)/1000.0
def visible(oc,p,q):
    n=int(max(abs(q[0]-p[0]),abs(q[1]-p[1]))*3)+2
    rr=np.rint(np.linspace(p[0],q[0],n)).astype(int); cc=np.rint(np.linspace(p[1],q[1],n)).astype(int)
    return bool(oc[rr,cc].all())
def _greedy(oc,path):
    n=len(path); idx=[0]; i=0
    while i<n-1:
        offs=[]; o=1
        while i+o<n-1: offs.append(o); o*=2
        offs.append(n-1-i)
        best=1; nxt=None
        for k,o in enumerate(offs):
            if visible(oc,path[i],path[i+o]): best=o; nxt=offs[k+1] if k+1<len(offs) else None
        lo=i+best; hi=i+nxt-1 if nxt else lo
        while lo<hi:
            mid=(lo+hi+1)//2
            if visible(oc,path[i],path[mid]): lo=mid
            else: hi=mid-1
        i=lo; idx.append(i)
    return idx
def _refine(oc,P,idx,max_iter=8):
    """Move each bend vertex along the raw path (between its neighbours) to the vertex minimising the two leg
    lengths subject to both legs staying in water; repeat until no gain."""
    for _ in range(max_iter):
        changed=False
        for k in range(1,len(idx)-1):
            a,b,c=idx[k-1],idx[k],idx[k+1]
            if c-a<3: continue
            cand=np.arange(a+1,c)
            Ld=np.hypot(*(P[cand]-P[a]).T)+np.hypot(*(P[c]-P[cand]).T)
            cur=np.hypot(*(P[b]-P[a]))+np.hypot(*(P[c]-P[b]))
            order=cand[np.argsort(Ld)]; Ls=np.sort(Ld)
            for j,Lj in zip(order[:400],Ls[:400]):
                if Lj>=cur-1e-9: break
                if visible(oc,tuple(P[a]),tuple(P[j])) and visible(oc,tuple(P[j]),tuple(P[c])):
                    idx[k]=int(j); changed=True; break
        # drop vertices made redundant
        k=1
        while k<len(idx)-1:
            if visible(oc,tuple(P[idx[k-1]]),tuple(P[idx[k+1]])): idx.pop(k); changed=True
            else: k+=1
        if not changed: break
    return idx
def smooth(oc,path):
    """Any-angle string pulling (exponential-probe greedy, then bend-point refinement)."""
    P=np.asarray(path,dtype=float); tp=[tuple(x) for x in np.asarray(path)]
    idx=_refine(oc,P,_greedy(oc,tp))
    return np.asarray(path)[idx]
def dijkstra(adj,src):
    dist={src:0.0}; prev={}; h=[(0.0,src)]
    while h:
        d,u=heapq.heappop(h)
        if d>dist.get(u,1e18): continue
        for v,w,t in adj.get(u,[]):
            nd=d+w
            if nd<dist.get(v,1e18): dist[v]=nd; prev[v]=(u,t); heapq.heappush(h,(nd,v))
    return dist,prev
def build(raw_fn, ids=None):
    R=pickle.load(open(raw_fn,'rb')); P,S,nodes,edges,paths=R['P'],R['S'],R['nodes'],R['edges'],R['paths']
    pts=[i for i in P['id'] if (ids is None or i in ids)]
    res={}; geoms={}
    seg_cache={}
    strict_cache={}
    def strict_of(t):
        if t not in strict_cache:
            T=tile(t); strict_cache[t]=T['ocean']&(T['landfrac'].astype(np.float32)<=0.25)
        return strict_cache[t]
    def ll_of(t,sm):
        x,y=to_xy(t,sm[:,0],sm[:,1]); lat,lon=inv(x,y); return np.c_[lat,lon]
    def seglen(ll): return float(np.sum(vincenty(ll[:-1,0],ll[:-1,1],ll[1:,0],ll[1:,1]))) if len(ll)>1 else 0.0
    def seg_poly(a,b,t):
        """Canonical smoothed segment (smoothed from the lexically first end), reversed as needed so a->b and
        b->a share one geometry. Also records the length smoothed from the other end (audit for check C2)."""
        lo_,hi_=sorted((a,b)); key=(lo_,hi_,t)
        if key not in seg_cache:
            pth=paths[(lo_,hi_,t)] if (lo_,hi_,t) in paths else paths[(hi_,lo_,t)][::-1]
            st=strict_of(t); ll=ll_of(t,smooth(st,pth)); llr=ll_of(t,smooth(st,pth[::-1]))[::-1]
            L1,L2=seglen(ll),seglen(llr)
            if L2<L1: ll,L1,L2=llr,L2,L1          # keep the shorter smoothing; audit keeps the other
            seg_cache[key]=(ll,L1,L2)
        ll,L1,L2=seg_cache[key]
        return (ll if a==lo_ else ll[::-1]), L1, L2
    # edge weight = geodesic length of the smoothed segment (grid octile costs tie across many portals)
    adj={}; seen=set()
    for (a,b,t),w in edges.items():
        key=tuple(sorted((a,b)))+(t,)
        if key in seen: continue
        seen.add(key); ll,L,_=seg_poly(a,b,t)
        adj.setdefault(a,[]).append((b,L,t)); adj.setdefault(b,[]).append((a,L,t))
    for a in pts:
        dist,prev=dijkstra(adj,a)
        for b in pts:
            if b==a: continue
            if b not in dist: res[(a,b)]=(np.nan,np.nan,''); continue
            seq=[]; v=b
            while v!=a: u,t=prev[v]; seq.append((u,v,t)); v=u
            seq=seq[::-1]; poly=[]; alt=0.0
            for (u,v,t) in seq:
                ll,L1,L2=seg_poly(u,v,t); alt+=L2
                poly.append(ll if not poly else ll[1:])
            poly=np.vstack(poly)
            L=float(np.sum(vincenty(poly[:-1,0],poly[:-1,1],poly[1:,0],poly[1:,1])))
            res[(a,b)]=(L,alt,'|'.join(sorted(set(t for _,_,t in seq))))
            geoms[(a,b)]=poly
    return res,geoms,R
