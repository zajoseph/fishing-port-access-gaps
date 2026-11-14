import numpy as np, pickle, sys, pandas as pd
from frame import fwd
TB={'S':(-30,480,-15,340),'M':(420,1300,250,430),'N':(1240,1920,-40,370)}
L={n:np.load(f'land25_{n}.npy') for n in 'SMN'}
def land_at(x,y):
    out=np.zeros(len(x),bool); done=np.zeros(len(x),bool)
    for n,(x0,x1,y0,y1) in TB.items():
        k=(~done)&(x>x0+0.05)&(x<x1-0.05)&(y>y0+0.05)&(y<y1-0.05)
        if not k.any(): continue
        r=((y1-y[k])/0.025).astype(int); c=((x[k]-x0)/0.025).astype(int)
        byte=L[n][r,c>>3]; out[k]=(byte>>(7-(c&7)))&1; done|=k
    return out
def check(poly,step=0.025):
    x,y=fwd(poly[:,0],poly[:,1]); seg=np.hypot(np.diff(x),np.diff(y))
    xs=[];ys=[]
    for i in range(len(seg)):
        n=max(int(seg[i]/step),1); t=np.arange(n)/n; xs.append(x[i]+t*(x[i+1]-x[i])); ys.append(y[i]+t*(y[i+1]-y[i]))
    xs=np.concatenate(xs+[x[-1:]]); ys=np.concatenate(ys+[y[-1:]])
    ld=land_at(xs,ys)
    # runs
    d=np.diff(np.r_[0,ld.astype(int),0]); st=np.where(d==1)[0]; en=np.where(d==-1)[0]
    runs=(en-st)*step*1000
    # classify runs by distance to nearest harbor point (zone = within 3.5 km)
    if len(runs):
        mx_=xs[(st+en)//2]; my_=ys[(st+en)//2]
        dz=np.min(np.hypot(mx_[:,None]-HX[None,:],my_[:,None]-HY[None,:]),axis=1)
        inz=dz<3.5
        out_runs=runs[~inz]; in_runs=runs[inz]
        k=np.argmax(np.where(~inz,runs,-1))
        return len(xs), ld.mean(), runs.max(), (out_runs.max() if len(out_runs) else 0.0), (in_runs.max() if len(in_runs) else 0.0), mx_[k], my_[k]
    return len(xs), ld.mean(), 0.0, 0.0, 0.0, np.nan, np.nan
import common
_p=common.ports(); HX=_p.x.values; HY=_p.y.values
if __name__=='__main__':
    res,geoms=pickle.load(open(sys.argv[1],'rb'))
    rows=[]
    for (a,b),g in geoms.items():
        if a<b:
            rows.append((a,b)+check(g))
    df=pd.DataFrame(rows,columns='a b n_samples land_frac max_land_run_m max_run_open_m max_run_harborzone_m open_run_x open_run_y'.split())
    df.to_csv(sys.argv[2],index=False)
    print(df[['max_run_open_m','max_run_harborzone_m']].describe())
    print((df.max_run_open_m>150).sum(),'routes with open-coast land run >150 m')
    print(df.sort_values('max_run_open_m',ascending=False).head(12).to_string())
