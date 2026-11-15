"""Trace water shapes from Spencer's game diagram into map units (one-time)."""
import json
import numpy as np
from PIL import Image
import contourpy
from kit import PRIV
Image.MAX_IMAGE_PIXELS = None
S = '/tmp/claude-0/-home-user-NERTA/e322c9a0-cf7a-58e6-ba0c-569be3cbeed5/scratchpad/p9-000.png'
im = Image.open(S).convert('RGB')
f = 5  # 1 sample = 5 px = 0.5 map unit
sm = im.resize((im.width // f, im.height // f), Image.BILINEAR)
a = np.asarray(sm).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
water = ((b > 200) & (r < 175) & (g > 190) & (b - r > 60)).astype(float)
# close small gaps where lines cross water
from scipy import ndimage
water = ndimage.binary_closing(water, iterations=4).astype(float)
water = ndimage.binary_opening(water, iterations=2).astype(float)
water[:, -1] = 0; water[:, 0] = 0; water[0] = 0; water[-1] = 0
# blank the black strip at the right edge of the source image
water[:, int(10250 / f):] = water[:, int(10250 / f) - 1:int(10250 / f)]
cg = contourpy.contour_generator(z=ndimage.gaussian_filter(water, 1.2))
polys = []
for line in cg.lines(0.5):
    if len(line) < 12:
        continue
    xy = np.array(line)
    polys.append([[x * f / 10, -y * f / 10] for x, y in xy[::2]])
json.dump(polys, open(PRIV / 'water_units.json', 'w'))
print(len(polys), 'water shapes')
