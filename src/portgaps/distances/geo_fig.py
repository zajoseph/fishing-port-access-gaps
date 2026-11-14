import json, pickle, pandas as pd, numpy as np
res,geoms=pickle.load(open('routes_h.pkl','rb'))
dm=pickle.load(open('outputs.pkl','rb'))['dm'].set_index(['from_port_id','to_port_id'])
feats=[]
for (a,b),g in sorted(geoms.items()):
    if a<b:
        feats.append({'type':'Feature','properties':{'port_a':a,'port_b':b,'sea_km':float(dm.loc[(a,b),'sea_km']),'sea_nm':float(dm.loc[(a,b),'sea_nm']),'n_vertices':len(g)},
                      'geometry':{'type':'LineString','coordinates':[[round(float(lo),5),round(float(la),5)] for la,lo in g]}})
json.dump({'type':'FeatureCollection','name':'t31_sea_routes','crs':{'type':'name','properties':{'name':'urn:ogc:def:crs:OGC:1.3:CRS84'}},'features':feats},open('sea_routes.geojson','w'),separators=(',',':'))
print(len(feats))
