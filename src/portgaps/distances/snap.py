import numpy as np, pandas as pd
from scipy import ndimage
from common import *
p=ports(); rows=[]
for n in 'SMN':
    t=tile(n); oc=t['ocean']
    d,(ir,ic)=ndimage.distance_transform_edt(~oc,return_indices=True)
    for i,q in p.iterrows():
        if n not in tiles_for(q.x,q.y): continue
        r,c=to_rc(n,q.x,q.y)
        rows.append((q.port_id,n,r,c,ir[r,c],ic[r,c],d[r,c]*100,bool(t['water'][r,c])))
df=pd.DataFrame(rows,columns='port_id tile r c sr sc snap_m in_water'.split())
df.to_csv('snap_raw.csv',index=False)
print(df.drop_duplicates('port_id').sort_values('snap_m',ascending=False).head(25).to_string())
