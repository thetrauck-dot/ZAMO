import numpy as np, cv2, potrace
from PIL import Image
im = np.asarray(Image.open('source.png').convert('RGB')).astype(float)
bg = np.array([49,50,54.]); fg = np.array([255,158,23.])
d = fg-bg
a = np.clip(((im-bg)@d)/(d@d), 0, 1)          # cobertura naranja 0..1 (antialias)
S = 16
up = cv2.resize(a, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
up = cv2.GaussianBlur(up, (0,0), S*0.35)
mask = up > 0.5
bmp = potrace.Bitmap(~mask)
path = bmp.trace(turdsize=40, alphamax=1.0, opticurve=True, opttolerance=0.4)
h, w = mask.shape
ds = []
for c in path:
    s = c.start_point; seg = [f"M{s.x/S:.3f},{s.y/S:.3f}"]
    for p in c.segments:
        if p.is_corner:
            seg.append(f"L{p.c.x/S:.3f},{p.c.y/S:.3f}L{p.end_point.x/S:.3f},{p.end_point.y/S:.3f}")
        else:
            seg.append(f"C{p.c1.x/S:.3f},{p.c1.y/S:.3f} {p.c2.x/S:.3f},{p.c2.y/S:.3f} {p.end_point.x/S:.3f},{p.end_point.y/S:.3f}")
    ds.append("".join(seg)+"Z")
# recortar al contenido
ys, xs = np.nonzero(a > 0.5); pad = 2
x0, y0, x1, y1 = xs.min()-pad, ys.min()-pad, xs.max()+1+pad, ys.max()+1+pad
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1-x0} {y1-y0}" width="{(x1-x0)*4}" height="{(y1-y0)*4}">\n'
       f'<path fill="#FF9E17" fill-rule="evenodd" d="{"".join(ds)}"/>\n</svg>\n')
open('smith_nephew.svg','w').write(svg)
print(len(path), (x0,y0,x1,y1))
