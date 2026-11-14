import numpy as np, pandas as pd
from frame import fwd, inv
T={}
def tile(name):
    if name not in T:
        z=np.load(f'tile_{name}.npz'); T[name]={k:z[k] for k in z.files}
    return T[name]
def to_rc(name,x,y):
    t=tile(name); x0,x1,y0,y1=t['bounds']; r=float(t['res'])
    return np.floor((y1-np.asarray(y))/r).astype(int), np.floor((np.asarray(x)-x0)/r).astype(int)
def to_xy(name,r_,c_):
    t=tile(name); x0,x1,y0,y1=t['bounds']; r=float(t['res'])
    return x0+(np.asarray(c_)+0.5)*r, y1-(np.asarray(r_)+0.5)*r
def ports():
    p=pd.read_csv('/home/claude/fishing-port-access-gaps/data/processed/ports.csv')
    p['x'],p['y']=fwd(p.lat.values,p.lon.values); return p
def tiles_for(x,y):
    out=[]
    for n,(x0,x1,y0,y1) in {'S':(-30,480,-15,340),'M':(420,1300,250,430),'N':(1240,1920,-40,370)}.items():
        if x0+2<x<x1-2 and y0+2<y<y1-2: out.append(n)
    return out
