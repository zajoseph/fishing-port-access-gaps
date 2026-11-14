import pickle, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from raster_osm import read_records
import pandas as pd, sys
res,geoms=pickle.load(open(sys.argv[1],'rb'))
recs=read_records('osm_uswest.bin')
P=pd.read_csv('/home/claude/fishing-port-access-gaps/data/processed/ports.csv').set_index('port_id')
boxes={'SF Bay':(-122.75,-122.15,37.45,38.2,['CA-san-francisco','CA-vallejo','CA-berkeley']),
'Humboldt':(-124.35,-124.05,40.65,40.9,['CA-humboldt-bay']),
'Columbia':(-124.15,-123.75,46.1,46.35,['OR-astoria','OR-warrenton','WA-ilwaco','WA-chinook']),
'Willapa/Grays':(-124.2,-123.85,46.4,47.0,['WA-tokeland','WA-bay-center','WA-nahcotta','WA-westport']),
'Puget':(-123.0,-122.15,47.55,49.05,['WA-seattle','WA-everett','WA-la-conner','WA-anacortes','WA-bellingham','WA-blaine','WA-port-townsend']),
'LA-LB/Huntington':(-118.5,-117.85,33.55,33.85,['CA-los-angeles-long-beach','CA-huntington-harbour','CA-redondo-beach','CA-newport-beach']),
'San Diego':(-117.35,-117.1,32.62,32.82,['CA-san-diego-bay','CA-mission-bay']),
'Catalina':(-118.7,-117.6,33.25,33.85,['CA-avalon']),
'Oregon rivers':(-124.5,-123.95,43.0,44.1,['OR-florence','OR-winchester-bay','OR-charleston','OR-bandon'])}
fig,axs=plt.subplots(3,3,figsize=(18,18))
for ax,(nm,(x0,x1,y0,y1,ids)) in zip(axs.flat,boxes.items()):
    polys=[]
    for bb,rings in recs:
        if bb[2]<x0 or bb[0]>x1 or bb[3]<y0 or bb[1]>y1: continue
        polys+= [r for r in rings]
    ax.add_collection(PolyCollection(polys,facecolor='#e0d8c0',edgecolor='#a09070',lw=0.3))
    segs=[]
    for (a,b),g in geoms.items():
        if a in ids and a<b: segs.append(g[:,::-1])
    ax.add_collection(LineCollection(segs,colors='tab:red',lw=0.6,alpha=0.5))
    for i in ids: ax.plot(P.loc[i,'lon'],P.loc[i,'lat'],'ko',ms=4)
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect(1/np.cos(np.radians((y0+y1)/2))); ax.set_title(nm); ax.set_facecolor('#d8e8f8')
plt.tight_layout(); plt.savefig(sys.argv[2],dpi=55)
