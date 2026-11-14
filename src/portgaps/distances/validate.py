import pandas as pd, pickle, numpy as np
from post import NM
res,geoms=pickle.load(open('routes_all.pkl','rb'))
P=pd.read_csv('noaa_pairs.csv'); out=[]
for r in P.itertuples():
    d=(res[(r.a,r.b)][0]+res[(r.b,r.a)][0])/2
    out.append((r.a.replace('REF-',''),r.b.replace('REF-',''),r.table,r.pair_type,'NOAA table coordinates',r.published_nm,round(d/NM,1)))
# Table 30 Columbia pairs with inventory harbor points (proxy endpoints)
O=pickle.load(open('outputs.pkl','rb'))['dm'].set_index(['from_port_id','to_port_id'])
for a,b,nm in [('WA-ilwaco','OR-astoria',13),('OR-warrenton','OR-astoria',4),('WA-ilwaco','OR-warrenton',12)]:
    out.append((a,b,'T30','in-estuary (Columbia)','inventory harbor points (proxy)',nm,round(O.loc[(a,b),'sea_nm'],1)))
V=pd.DataFrame(out,columns=['a','b','table','pair_type','endpoints','published_nm','model_nm'])
V['diff_nm']=V.model_nm-V.published_nm; V['pct_err']=(V.diff_nm/V.published_nm*100).round(1); V['flag_gt10pct']=V.pct_err.abs()>10
V.to_csv('validation.csv',index=False); print(V.to_string())
