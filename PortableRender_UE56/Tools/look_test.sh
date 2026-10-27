#!/bin/bash
# Quick PT test of 3 representative views at 1080p + luminance stats.  bash Tools/look_test.sh <tag>
R="$(cd "$(dirname "$0")/.." && pwd)"; T=$1
echo "import mrq_render as R, importlib; importlib.reload(R); result = R.render([('2BHK','SEQ_Living'),('2BHK','SEQ_Bed1'),('3BHK','SEQ_Camera')], res=(1920,1080), path_tracer=True, spp=64, tag='_$T')" | bash "$R/Saved/ClaudeBridge/ue.sh" - 120 >/dev/null
cd "$R/Saved/MovieRenders"; until [ -f 2BHK/Living_$T.png ] && [ -f 2BHK/Bed1_$T.png ] && [ -f 3BHK/Camera_$T.png ]; do sleep 5; done; sleep 3
"C:/Users/Admin/AppData/Local/Programs/Python/Python314/python" -c "
import numpy as np; from PIL import Image
fs=['2BHK/Living_$T.png','2BHK/Bed1_$T.png','3BHK/Camera_$T.png']; o=Image.new('RGB',(1920,1080),'white')
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB'); a=np.asarray(im.convert('L'),np.float32)/255; p=np.percentile(a,[5,50,95])
    print('%-24s p5 %.2f p50 %.2f p95 %.2f clip %.1f%%' % (f, *p, (a>0.97).mean()*100))
    o.paste(im.resize((960,540)),((i%2)*960,(i//2)*540))
o.save('look_$T.jpg', quality=92)"
