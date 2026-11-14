import numpy as np, struct, sys
from PIL import Image, ImageDraw
from scipy import ndimage
from frame import fwd
RES=0.1; SS=4; SAVE25=True
TILES={'S':(-30,480,-15,340),'M':(420,1300,250,430),'N':(1240,1920,-40,370)}
def read_records(fn):
    b=open(fn,'rb').read(); pos=0; out=[]
    while pos<len(b):
        rec,clen=struct.unpack('>ii',b[pos:pos+8]); clen*=2; c=pos+8
        st=struct.unpack('<i',b[c:c+4])[0]
        if st==5:
            bbox=struct.unpack('<4d',b[c+4:c+36]); npart,npt=struct.unpack('<ii',b[c+36:c+44])
            parts=np.frombuffer(b,'<i4',npart,c+44); pts=np.frombuffer(b,'<f8',2*npt,c+44+4*npart).reshape(-1,2)
            rings=[pts[parts[i]:(parts[i+1] if i+1<npart else npt)] for i in range(npart)]
            out.append((bbox,rings))
        pos=c+clen
    return out
def signed_area(r):
    x,y=r[:,0],r[:,1]; return 0.5*np.sum(x[:-1]*y[1:]-x[1:]*y[:-1])
def build(name,recs,water=None):
    x0,x1,y0,y1=TILES[name]
    nx=int(round((x1-x0)/RES)); ny=int(round((y1-y0)/RES)); W,H=nx*SS,ny*SS
    land=np.zeros((H,W),bool)
    for bbox,rings in recs:
        # quick reject via projected bbox corners
        cx,cy=fwd(np.array([bbox[1],bbox[1],bbox[3],bbox[3]]),np.array([bbox[0],bbox[2],bbox[0],bbox[2]]))
        if cx.max()<x0-2 or cx.min()>x1+2 or cy.max()<y0-2 or cy.min()>y1+2: continue
        pr=[]
        for r in rings:
            px,py=fwd(r[:,1],r[:,0]); pr.append((((px-x0)/RES*SS),((y1-py)/RES*SS),signed_area(r)))
        allx=np.concatenate([p[0] for p in pr]); ally=np.concatenate([p[1] for p in pr])
        c0=max(int(np.floor(allx.min()))-1,0); c1=min(int(np.ceil(allx.max()))+2,W)
        r0=max(int(np.floor(ally.min()))-1,0); r1=min(int(np.ceil(ally.max()))+2,H)
        if c1<=c0 or r1<=r0: continue
        im=Image.new('1',(c1-c0,r1-r0),0); d=ImageDraw.Draw(im)
        for px,py,a in sorted(pr,key=lambda t:t[2]):   # outers (cw, negative area) first
            if a<0: d.polygon(list(zip((px-c0).tolist(),(py-r0).tolist())),fill=1,outline=1)
        for px,py,a in pr:
            if a>0: d.polygon(list(zip((px-c0).tolist(),(py-r0).tolist())),fill=0)
        for px,py,a in pr:   # keep every land boundary pixel so thin spits/jetties stay continuous at 25 m
            d.line(list(zip((px-c0).tolist(),(py-r0).tolist())),fill=1,width=1)
        land[r0:r1,c0:c1]|=np.asarray(im)
    if water:
        for kind,outs,ins,tg,oid in water:
            for rings,val in ((outs,0),(ins,1)):
                for r in rings:
                    px,py=fwd(r[:,1],r[:,0]); px=(px-x0)/RES*SS; py=(y1-py)/RES*SS
                    c0=max(int(px.min())-1,0); c1=min(int(px.max())+2,W); r0=max(int(py.min())-1,0); r1=min(int(py.max())+2,H)
                    if c1<=c0 or r1<=r0: continue
                    im=Image.new('1',(c1-c0,r1-r0),0); ImageDraw.Draw(im).polygon(list(zip((px-c0).tolist(),(py-r0).tolist())),fill=1)
                    m=np.asarray(im)
                    if val==0: land[r0:r1,c0:c1]&=~m
                    else: pass  # islands inside water polygons: leave land as given by coastline polygons
    if SAVE25: np.save(f'land25_{name}.npy',np.packbits(land,axis=1))
    landfrac=land.reshape(ny,SS,nx,SS).mean(axis=(1,3)); del land
    landm=landfrac>=0.5; water=~landm
    lab,nl=ndimage.label(water,structure=np.ones((3,3)))
    sizes=ndimage.sum(water,lab,range(1,nl+1)); ocean=lab==(1+int(np.argmax(sizes)))
    np.savez_compressed(f'tile_{name}.npz',ocean=ocean,water=water,lake=np.zeros_like(ocean),landfrac=landfrac.astype(np.float16),bounds=np.array(TILES[name]),res=RES)
    print(name,ny,nx,'ocean',int(ocean.sum()),'other comps',nl-1,flush=True)
if __name__=='__main__':
    import osmwater
    recs=read_records(sys.argv[1]); print('records',len(recs),flush=True)
    water=osmwater.load(sys.argv[2]) if sys.argv[2]!='none' else None
    if water: print('water polys',len(water),flush=True)
    for t in sys.argv[3:]: build(t,recs,water)
