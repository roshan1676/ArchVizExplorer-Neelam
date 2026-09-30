import json, numpy as np, sys
from PIL import Image, ImageDraw
from strip import strip, OFF, RAW
STEP=0.25
def profiles(S, half=5):
    n=S.shape[0]; P=np.empty((n,S.shape[1],3),np.float32)
    for i in range(n): P[i]=np.nanmedian(S[max(0,i-half):i+half+1],axis=0)
    return P
def detect_row(p, want_w):
    m=len(p); c0=m//2
    mx=np.nanmax(p,1); mn=np.nanmin(p,1); sat=mx-mn
    near=np.arange(max(0,c0-40),min(m,c0+41))          # +-10 m
    cand=near[(sat[near]<22)&(mx[near]>80)&(mx[near]<230)]
    if len(cand)<8: return None
    ref=np.median(p[cand],0)
    d=np.linalg.norm(p-ref,axis=1)
    on=(d<22)&(sat<28)
    # close small gaps (cars / markings) of <= 1 m
    on2=on.copy()
    for i in range(m):
        if not on[i]:
            l=max(0,i-4); r=min(m,i+5)
            if on[l:i].any() and on[i+1:r].any(): on2[i]=True
    # run nearest centre
    runs=[]; i=0
    while i<m:
        if on2[i]:
            j=i
            while j<m and on2[j]: j+=1
            runs.append((i,j-1)); i=j
        else: i+=1
    runs=[r for r in runs if (r[1]-r[0])*STEP>=5.0]
    if not runs: return None
    def dist(r): return 0 if r[0]<=c0<=r[1] else min(abs(r[0]-c0),abs(r[1]-c0))
    r=min(runs,key=dist)
    if dist(r)*STEP>12: return None
    return r
def detect(k):
    S,nrm=strip(k); P=profiles(S)
    w=RAW[k]['width_m']; res=[]
    for i in range(len(P)): res.append(detect_row(P[i],w))
    return S,P,res
if __name__=='__main__':
    for k in sys.argv[1:]:
        S,P,res=detect(k)
        im=Image.fromarray(np.nan_to_num(S).clip(0,255).astype(np.uint8)).resize((S.shape[1]*2,S.shape[0]*4))
        dr=ImageDraw.Draw(im)
        c0=S.shape[1]//2
        for i,r in enumerate(res):
            y=i*4+2
            dr.point((c0*2,y),fill=(255,255,0))
            if r: dr.point((r[0]*2,y),fill=(255,0,0)); dr.point((r[1]*2,y),fill=(0,0,255)); dr.point((r[0]+r[1],y),fill=(0,255,0))
        im.rotate(90,expand=True).save('d2_%s.jpg'%k)
        ws=[(r[1]-r[0])*STEP for r in res if r]; cs=[((r[0]+r[1])/2-c0)*STEP for r in res if r]
        print(k, RAW[k]['width_m'], 'found',len(ws),'/',len(res), 'w med',np.median(ws) if ws else None,'centre off med',np.median(cs) if cs else None)
