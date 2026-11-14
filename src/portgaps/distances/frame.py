import numpy as np
R=6371.0088
def xyz(lat,lon):
    la,lo=np.radians(lat),np.radians(lon); return np.stack([np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)],-1)
A=xyz(32.6,-117.2); B=xyz(48.9,-123.0)
n=np.cross(A,B); n/=np.linalg.norm(n); e1=A; e2=np.cross(n,e1)
def fwd(lat,lon):
    P=xyz(np.asarray(lat,float),np.asarray(lon,float))
    return np.arctan2(P@e2,P@e1)*R, np.arcsin(np.clip(P@n,-1,1))*R   # along, across (km)
def inv(x,y):
    a=np.asarray(x)/R; c=np.asarray(y)/R
    P=(np.cos(c)*np.cos(a))[...,None]*e1+(np.cos(c)*np.sin(a))[...,None]*e2+np.sin(c)[...,None]*n
    return np.degrees(np.arcsin(P[...,2])), np.degrees(np.arctan2(P[...,1],P[...,0]))
