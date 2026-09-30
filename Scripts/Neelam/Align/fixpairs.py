import json, numpy as np
from strip import RAW
O=json.load(open('offsets.json'))
def centres(k, off):
    p=np.array(RAW[k]['pts']); n=len(p); out=[]
    for i in range(n):
        a=p[max(i-2,0)]; b=p[min(i+2,n-1)]; d=b[:2]-a[:2]; t=d/max(np.hypot(*d),1e-6); nr=np.array([-t[1],t[0]])
        out.append(p[i,:2]+nr*off[i]*100)
    return np.array(out)
pairs=[("rd_620857542","rd_620857547"),("rd_469039169","rd_584887818"),("rd_618748750","rd_618748746"),("rd_584887817","rd_469497530"),("rd_618748788","rd_618748795")]
for a,b in pairs:
    for it in range(3):
        ca=centres(a,O[a]['off']); cb=centres(b,O[b]['off']); wa=O[a]['width_m']; wb=O[b]['width_m']
        oa=np.array(O[a]['off']); ob=np.array(O[b]['off']); fa=np.zeros(len(oa),bool); fb=np.zeros(len(ob),bool)
        for i in range(len(ca)):
            d=np.hypot(*(cb-ca[i]).T); j=int(np.argmin(d))
            if d[j] < (wa+wb)*50-150:
                if abs(oa[i])>=abs(ob[j]): fa[i]=True
                else: fb[j]=True
        # widen masks by 10 samples and blend back to 0 offset smoothly
        def relax(o,f):
            m=np.convolve(f.astype(float),np.ones(21),'same')>0
            t=o.copy(); t[m]=0.0
            k=np.ones(11)/11; return np.convolve(np.pad(t,5,mode='edge'),k,'valid')
        if fa.any(): O[a]['off']=[round(float(v),2) for v in relax(oa,fa)]
        if fb.any(): O[b]['off']=[round(float(v),2) for v in relax(ob,fb)]
        print(a,b,it,int(fa.sum()),int(fb.sum()))
json.dump(O,open('offsets.json','w'))
