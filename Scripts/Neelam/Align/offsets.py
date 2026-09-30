import json, numpy as np
from strip import RAW
D=json.load(open('det_raw.json'))
def nanmed_roll(a, h):
    out=np.full_like(a,np.nan)
    for i in range(len(a)):
        w=a[max(0,i-h):i+h+1]; w=w[np.isfinite(w)]
        if len(w)>=max(3,h//2): out[i]=np.median(w)
    return out
def fill(a):
    f=np.isfinite(a)
    if not f.any(): return None
    x=np.arange(len(a)); return np.interp(x,x[f],a[f])
res={}
for k,r in RAW.items():
    off=np.array([np.nan if v is None else v for v in D[k]['off']]); w=np.array([np.nan if v is None else v for v in D[k]['w']])
    frac=np.isfinite(off).mean()
    o=nanmed_roll(off,7)                       # 45 m rolling median
    info={"found":round(float(frac),2)}
    if len(off)<20:
        f=np.isfinite(off)
        o=np.full(len(off), float(np.nanmedian(off)) if f.mean()>=0.5 else 0.0); o=np.clip(o,-8,8); wd=r['width_m']; mode='short'
    elif frac>=0.5 and np.isfinite(o).any():
        o=fill(o); o=np.clip(o,-10,10)
        k9=np.ones(9)/9; o=np.convolve(np.pad(o,4,mode='edge'),k9,'valid')
        lanes=r['lanes']; wd=float(np.clip(np.nanmedian(w), lanes*3.0, lanes*3.5+3.0)); mode="track"
    elif frac>=0.15 and np.nanpercentile(off,90)-np.nanpercentile(off,10)<3.0:
        o=np.full(len(off),float(np.nanmedian(off))); wd=r['width_m']; mode="const"
    else:
        o=np.zeros(len(off)); wd=r['width_m']; mode="keep"
    res[k]={"off":[round(float(v),2) for v in o],"width_m":round(wd*2)/2,"mode":mode,**info}
json.dump(res,open('offsets.json','w'))
import collections; print(collections.Counter(v['mode'] for v in res.values()))
for k,v in res.items(): print(k,RAW[k]['group'],v['mode'],v['found'],RAW[k]['width_m'],'->',v['width_m'],'off %.1f..%.1f'%(min(v['off']),max(v['off'])))
