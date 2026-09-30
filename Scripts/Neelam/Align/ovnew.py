import json, numpy as np, sys
from PIL import Image, ImageDraw
from strip import RAW, cams, FLAT
O=json.load(open('offsets.json'))
def proj(c,x,y,z):
    d=c['loc'][2]-z; s=(c['w']/2)/d
    return (c['w']/2+(y-c['loc'][1])*s, c['h']/2-(x-c['loc'][0])*s)
def edges(k, off, w):
    p=np.array(RAW[k]['pts']); n=len(p); L=[];R=[]
    for i in range(n):
        a=p[max(i-2,0)]; b=p[min(i+2,n-1)]; d=b[:2]-a[:2]; t=d/max(np.hypot(*d),1e-6); nr=np.array([-t[1],t[0]])
        c=p[i,:2]+nr*off[i]*100
        L.append((*(c+nr*w*50),FLAT[k]['pts'][i][2])); R.append((*(c-nr*w*50),FLAT[k]['pts'][i][2]))
    return L,R
for a in sys.argv[1:]:
    i=int(a); c=cams[i]; im=Image.open('align/align_%d.jpg'%i); dr=ImageDraw.Draw(im)
    for k in RAW:
        L,R=edges(k,[0]*len(RAW[k]['pts']),RAW[k]['width_m'])
        for E in (L,R): dr.line([proj(c,*q) for q in E],fill=(255,0,0),width=2)
        L,R=edges(k,O[k]['off'],O[k]['width_m'])
        for E in (L,R): dr.line([proj(c,*q) for q in E],fill=(0,255,0),width=3)
    im.resize((1600,900)).save('on_%d.jpg'%i)
