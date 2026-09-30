import json, numpy as np
from detect2 import detect, STEP
from strip import RAW
out={}
for k in RAW:
    S,P,res=detect(k); c0=S.shape[1]//2
    off=np.array([((r[0]+r[1])/2-c0)*STEP if r else np.nan for r in res])
    wid=np.array([(r[1]-r[0])*STEP if r else np.nan for r in res])
    out[k]={"off":[None if np.isnan(v) else float(v) for v in off],"w":[None if np.isnan(v) else float(v) for v in wid]}
    f=np.isfinite(off)
    print(k, RAW[k]['group'], RAW[k]['width_m'], len(off), 'found %.0f%%'%(100*f.mean()), 'off med %.1f p10 %.1f p90 %.1f'%(np.nanmedian(off),np.nanpercentile(off,10),np.nanpercentile(off,90)) if f.any() else '', 'w med %.1f'%np.nanmedian(wid) if f.any() else '')
json.dump(out,open('det_raw.json','w'))
