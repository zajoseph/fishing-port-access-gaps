"""Thin-barrier preservation for the 100 m routing raster (applied after finalize_tiles.py)."""
import numpy as np
from scipy import ndimage
def split_table():
    T=np.zeros(1<<16,bool)
    for pat in range(1<<16):
        land=np.array([(pat>>i)&1 for i in range(16)],bool).reshape(4,4); w=~land
        if w.sum()<2 or land.sum()==0: continue
        lab,n=ndimage.label(w)   # 4-connected
        if n<2: continue
        border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]))-{0}
        T[pat]=len(border)>=2
    return T
def apply(name,T):
    z=dict(np.load(f'tile_{name}.npz')); L=np.unpackbits(np.load(f'land25_{name}.npy'),axis=1)
    ny,nx=z['ocean'].shape; L=L[:ny*4,:nx*4]; pat=np.zeros((ny,nx),np.uint16)
    for i in range(16):
        pat|=(L[i//4::4, i%4::4].astype(np.uint16)<<np.uint16(i))
    del L
    barrier=T[pat]&z['water']&~z['zone']
    water=z['water']&~barrier
    lf=z['landfrac'].astype(np.float32); nfix=0
    for _ in range(10):
        a=water[:-1,:-1]; b=water[:-1,1:]; c=water[1:,:-1]; d=water[1:,1:]
        diag1=a&d&~b&~c; diag2=b&c&~a&~d
        k=diag1|diag2
        if not k.any(): break
        r,cc=np.nonzero(diag1)
        for rr,c0 in zip(r,cc):
            if lf[rr,c0]>=lf[rr+1,c0+1]: water[rr,c0]=False
            else: water[rr+1,c0+1]=False
        r,cc=np.nonzero(diag2)
        for rr,c0 in zip(r,cc):
            if lf[rr,c0+1]>=lf[rr+1,c0]: water[rr,c0+1]=False
            else: water[rr+1,c0]=False
        nfix+=int(k.sum())
    lab,nl=ndimage.label(water,structure=np.ones((3,3)))
    s=np.bincount(lab.ravel()); s[0]=0; ocean=lab==s.argmax()
    z.update(water=water,ocean=ocean,barrier=barrier)
    np.savez_compressed(f'tile_{name}.npz',**z)
    print(name,'barrier cells',int(barrier.sum()),'diagonal fixes',nfix,'ocean',int(ocean.sum()))
if __name__=='__main__':
    T=split_table()
    import sys
    for n in (sys.argv[1:] or 'SMN'): apply(n,T)
