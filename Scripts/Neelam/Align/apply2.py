import json, numpy as np, copy
RAWF='/mnt/user-data/uploads/ArchVizExplorer-Neelam/Scripts/Neelam/Data/road_build_raw.json'
raw=json.load(open(RAWF)); O=json.load(open('offsets.json')); R=raw['roads']
P={k:np.array(r['pts'])[:,:2] for k,r in R.items()}
D={}
for k in R:
    p=P[k]; n=len(p); off=np.array(O[k]['off']); nr=np.zeros((n,2))
    for i in range(n):
        a=p[max(i-2,0)]; b=p[min(i+2,n-1)]; d=b-a; t=d/max(np.hypot(*d),1e-6); nr[i]=[-t[1],t[0]]
    D[k]=nr*off[:,None]*100
# junctions: endpoint of A within 8 m of a point of B -> A's end follows B's displacement (longest roads win)
order=sorted(R, key=lambda k:-len(R[k]['pts']))
rank={k:i for i,k in enumerate(order)}
links=[]
for a in R:
    for end in (0,-1):
        e=P[a][end]; best=None
        for b in R:
            if b==a: continue
            d=np.hypot(*(P[b]-e).T); j=int(np.argmin(d))
            if d[j]<800 and (best is None or rank[b]<rank[best[0]]): best=(b,j)
        if best and rank[best[0]]<rank[a]: links.append((a,end,best[0],best[1]))
for it in range(3):
    for a,end,b,j in sorted(links,key=lambda l:-rank[l[0]]*0+rank[l[2]]):
        tgt=D[b][j].copy(); p=P[a]; n=len(p)
        s=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(p,axis=0).T))])
        dist=s if end==0 else s[-1]-s
        w=np.clip(1-dist/4000.0,0,1)[:,None]
        D[a]=D[a]*(1-w)+tgt*w
new=copy.deepcopy(raw)
for k,r in new['roads'].items():
    q=P[k]+D[k]; r['pts']=[[round(float(x),1),round(float(y),1),p[2]] for (x,y),p in zip(q,R[k]['pts'])]
    r['width_m']=O[k]['width_m']; r['align']=O[k]['mode']
json.dump(new,open('road_build_aligned_raw.json','w'))
print('links',len(links))
# check joins: endpoint gaps before/after
g0=[];g1=[]
N={k:np.array(r['pts'])[:,:2] for k,r in new['roads'].items()}
for a,end,b,j in links:
    g0.append(np.hypot(*(P[a][end]-P[b][j]))); g1.append(np.hypot(*(N[a][end]-N[b][j])))
print('join gap cm raw max %.0f new max %.0f'%(max(g0),max(g1)))
