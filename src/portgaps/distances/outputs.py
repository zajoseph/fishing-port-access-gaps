import numpy as np, pandas as pd, pickle, json, itertools
from post import build, vincenty, NM
from common import *
from frame import inv
RAW='route_raw_noaa_refs.pkl'
res,geoms,R=build(RAW)
pickle.dump((res,geoms),open('routes_all.pkl','wb'))
P=R['P']; S=R['S'].set_index('id')
H=[i for i in P.id if not i.startswith('REF')]
GEOM='OSM land polygons (osmdata.openstreetmap.de split WGS84, 2026-11-13) + OSM water polygons near harbors (Overpass, 2026-11-13)'
METH='least-cost water path on 100 m raster (8-connected MCP, coast-aligned oblique frame), any-angle smoothed, WGS84 geodesic length; snapped point to snapped point'
rows=[]; asym=[]
for a,b in itertools.permutations(H,2):
    d1=res[(a,b)][0]; d2=res[(b,a)][0]; asym.append((a,b,d1,d2,res[(a,b)][1]))
    km=(d1+d2)/2; rows.append((a,b,round(km,3),round(km/NM,3),METH,GEOM))
dm=pd.DataFrame(rows,columns=['from_port_id','to_port_id','sea_km','sea_nm','route_method','geometry_source'])
# snapped ports
pp=P.set_index('id'); out=[]
for h in H:
    s=S.loc[h]; x,y=to_xy(s.tile,s.r,s.c); la,lo=inv(x,y)
    d=float(vincenty(np.array([pp.loc[h,'lat']]),np.array([pp.loc[h,'lon']]),np.array([la]),np.array([lo]))[0])*1000
    out.append((h,pp.loc[h,'lat'],pp.loc[h,'lon'],round(float(la),5),round(float(lo),5),round(d,1),s.tile))
sp=pd.DataFrame(out,columns=['port_id','lat','lon','snapped_lat','snapped_lon','snap_distance_m','raster_tile'])
pickle.dump(dict(dm=dm,sp=sp,asym=asym),open('outputs.pkl','wb'))
print(dm.shape, dm.sea_km.isna().sum(), sp.snap_distance_m.max())
print(sp.sort_values('snap_distance_m',ascending=False).head(6).to_string())
