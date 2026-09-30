import json, glob, math, numpy as np
from PIL import Image
RAW=json.load(open('/mnt/user-data/uploads/ArchVizExplorer-Neelam/Scripts/Neelam/Data/road_build_raw.json'))['roads']
FLAT=json.load(open('rb_flat.json'))['roads']
cams={}; imgs={}
for f in glob.glob('align/align_*.json'):
    i=int(f.split('_')[-1][:-5]); cams[i]=json.load(open(f))
def img(i):
    if i not in imgs: imgs[i]=np.asarray(Image.open('align/align_%d.jpg'%i),dtype=np.float32)
    return imgs[i]
def best_cam(x,y):
    return min(cams, key=lambda i: max(abs(x-cams[i]['loc'][0])/22000, abs(y-cams[i]['loc'][1])/39000))
def sample(i, X, Y, Z):
    c=cams[i]; d=c['loc'][2]-Z; s=(c['w']/2)/d
    u=c['w']/2+(Y-c['loc'][1])*s; v=c['h']/2-(X-c['loc'][0])*s
    a=img(i); h,w=a.shape[:2]
    u0=np.clip(np.floor(u).astype(int),0,w-2); v0=np.clip(np.floor(v).astype(int),0,h-2)
    fu=(u-u0)[...,None]; fv=(v-v0)[...,None]
    out=(a[v0,u0]*(1-fu)*(1-fv)+a[v0,u0+1]*fu*(1-fv)+a[v0+1,u0]*(1-fu)*fv+a[v0+1,u0+1]*fu*fv)
    ok=(u>=0)&(u<w-1)&(v>=0)&(v<h-1)
    out[~ok]=np.nan
    return out
OFF=np.arange(-3000,3001,25.0)   # cm, 0.25 m
def strip(k):
    p=np.array(RAW[k]['pts']); z=np.array([q[2] for q in FLAT[k]['pts']])
    n=len(p); t=np.zeros((n,2))
    for i in range(n):
        a=p[max(i-2,0)]; b=p[min(i+2,n-1)]; d=b[:2]-a[:2]; t[i]=d/max(np.hypot(*d),1e-6)
    nrm=np.stack([-t[:,1],t[:,0]],1)   # left normal (UE: x fwd, y right)
    X=p[:,0,None]+nrm[:,0,None]*OFF[None]; Y=p[:,1,None]+nrm[:,1,None]*OFF[None]; Z=z[:,None]+0*OFF[None]
    S=np.full((n,len(OFF),3),np.nan,np.float32)
    for i in range(n):
        ci=best_cam(p[i,0],p[i,1])
        S[i]=sample(ci,X[i],Y[i],Z[i])
    return S, nrm
if __name__=='__main__':
    import sys
    for k in sys.argv[1:]:
        S,_=strip(k); im=np.nan_to_num(S).clip(0,255).astype(np.uint8)
        # rows = along-track (3 m per row) -> stretch x4 so 1 px ~0.75 m
        Image.fromarray(im).resize((im.shape[1], im.shape[0]*4)).save('strip_%s.jpg'%k)
        print(k, im.shape)
