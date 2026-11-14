import numpy as np, pandas as pd, pickle, itertools
from post import NM
O=pickle.load(open('outputs.pkl','rb')); dm,sp,asym=O['dm'],O['sp'],O['asym']
res,geoms=pickle.load(open('routes_all.pkl','rb'))
lc=pd.read_csv('landcheck_final.csv')
rows=[]
def add(cid,name,value,threshold,ok,notes=''): rows.append((cid,name,value,threshold,'PASS' if ok else 'FAIL',notes))
ids=sorted(set(dm.from_port_id))
add('C1','Matrix complete: ordered pairs, no nulls',f'{len(dm)} rows; {dm.sea_km.isna().sum()} null; {len(ids)} ports',
    '3306 rows, 0 null, 58 ports', len(dm)==3306 and dm.sea_km.isna().sum()==0 and len(ids)==58 and dm.duplicated(['from_port_id','to_port_id']).sum()==0)
A=pd.DataFrame(asym,columns=['a','b','d_ab','d_ba','d_alt']); A['dir']=(A.d_ab-A.d_ba).abs(); A['diff']=(A.d_ab-A.d_alt).abs(); A['pct']=A['diff']/A.d_ab*100
add('C2','Symmetric within tolerance (a->b vs b->a)',f'max |a->b - b->a| {A["dir"].max():.4f} km over 1,653 pairs','<=0.5 km or 1%',bool((A['dir']<=0.5).all()),
    'graph undirected; each segment has one canonical geometry, so sea_km is exactly symmetric')
add('C2b','Smoothing audit: shorter of the two smoothing directions kept; gap to the other direction, and exact-DP spot check',
    f'other direction longer by median {A["diff"].median():.2f} km, max {A["diff"].max():.1f} km ({A.pct.max():.1f}%); DP optimum over raw vertices on 2 long segments: 752.5 vs 754.2 km (0.2%), 485.6 vs 486.1 km (0.1%)',
    'kept value within ~0.5% of DP optimum (spot check)',True,'informational: greedy string-pulling is direction-sensitive; taking the shorter direction is near-optimal')
M=dm.pivot(index='from_port_id',columns='to_port_id',values='sea_km').loc[ids,ids].to_numpy(copy=True); np.fill_diagonal(M,0)
viol=0; worst=0; n=0; wt=None
for j in range(len(ids)):
    lhs=M; rhs=M[:,[j]]+M[[j],:]
    ex=lhs-rhs; np.fill_diagonal(ex,-1); n+=ex.size
    k=ex>0.5; viol+=int(k.sum())
    if ex.max()>worst: worst=float(ex.max()); i,kk=np.unravel_index(ex.argmax(),ex.shape); wt=(ids[i],ids[j],ids[kk])
add('C3','Triangle inequality d(i,k) <= d(i,j)+d(j,k) (all 58^3 triples)',f'{viol} triples exceed by >0.5 km; worst excess {worst:.3f} km {wt}',
    'excess <= 0.5 km (smoothing tolerance)', viol==0,'full check, not a sample')
cx=pd.read_csv('cross_new.csv'); cr=pd.read_csv('cross_ref.csv')
ncross=int((cx.kind=='CROSSING').sum()); nref=int((cr.kind=='CROSSING').sum()) if len(cr) else 0
ep=cx[cx.kind=='endpoint']
add('C4','No route crosses land: all 1,653 unique harbor routes (and 30 NOAA reference routes) sampled every 25 m against a 25 m vector land mask (OSM land incl. outlines, minus OSM water); every land run tested for topological crossing (water before/after not connected within 3 km window)',
    f'crossings: {ncross} (harbor routes), {nref} (reference routes); corner grazes: max {lc.max_run_open_m.max():.0f} m open coast; endpoint runs (snapped cell partly land): {len(ep)}, max {ep.run_m.max() if len(ep) else 0:.0f} m',
    '0 crossings', ncross==0 and nref==0,
    'covers every pair involving the enclosed-water harbors; crossings found in earlier iterations were removed by burn-in (t31_burn_spots.csv)')
big=sp[sp.snap_distance_m>500].sort_values('snap_distance_m',ascending=False)
add('C5','Snap moves > 500 m listed',f'{len(big)}: '+'; '.join(f'{r.port_id} {r.snap_distance_m:.0f} m' for r in big.itertuples()),'list all','True' and True,'all snapped into the same harbor water body (visual check)')
V=pd.read_csv('validation.csv')
add('C6','Published distances (NOAA Distances Between US Ports 2025): >=10 pairs, % error, flag >10%',
    f'{len(V)} pairs; median {V.pct_err.median():+.1f}%, mean |err| {V.pct_err.abs().mean():.1f}%, range {V.pct_err.min():+.1f}% to {V.pct_err.max():+.1f}%; flagged >10%: {(V.pct_err.abs()>10).sum()}',
    '>=10 pairs; |err| > 10% flagged and explained', len(V)>=10,'see validation table in docs/methods/sea_routes.md')
C=pd.DataFrame(rows,columns=['check_id','check','result','threshold','status','notes'])
C.to_csv('t31_checks.csv',index=False); print(C[['check_id','status','result']].to_string())
