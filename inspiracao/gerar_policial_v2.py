# Versão policial v2: sombra uniforme leve + texto embaixo. Base: grade fria "aço", luz de giroflex (vermelho/azul), spotlight no rosto.
# Conteúdo da foto preservado: apenas cor, luz, contraste e granulação.
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC, FONT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(SRC).convert("RGB"); W, H = im.size

# clareza (contraste local) antes do grade
im = im.filter(ImageFilter.UnsharpMask(radius=45, percent=55, threshold=0))
im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
a = np.asarray(im).astype(np.float32) / 255.0
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
L = lambda c: 0.2126*c[...,0] + 0.7152*c[...,1] + 0.0722*c[...,2]

# dessaturação forte + curva em S (pretos esmagados)
lum = L(a); a = lum[...,None] + (a - lum[...,None]) * 0.45
a = np.clip(a, 0, 1); a = a*a*(3 - 2*a)              # S-curve
a = np.clip((a - 0.04) / 0.96, 0, 1) ** 1.15
# split-tone: sombras azul-aço, realces neutros/frios
lum = L(a); sh = (1 - lum) ** 2
a[...,0] += -0.05*sh; a[...,1] += 0.005*sh; a[...,2] += 0.07*sh
a[...,2] += 0.02*lum**2

# sombra uniforme leve sobre toda a foto
DARK = 0.38
a *= (1 - DARK)

# luz de giroflex: vermelho à esquerda, azul à direita (screen)
def glow(cx, cy, rx, ry, col, k):
    g = np.exp(-(((x-cx)/rx)**2 + ((y-cy)/ry)**2))[...,None] * k
    return g * np.array(col, np.float32)
light = glow(-W*0.02, H*0.44, W*0.38, H*0.26, (1.0, 0.06, 0.08), 0.75) \
      + glow(W*1.02, H*0.38, W*0.38, H*0.26, (0.08, 0.30, 1.0), 0.85)
a = np.clip(a, 0, 1)
a = a + light*(0.10 + 0.9*np.sqrt(a))*0.45

img = Image.fromarray((np.clip(a, 0, 1)*255).astype(np.uint8))
g = np.random.default_rng(3).normal(0, 6, (H, W, 1))
img = Image.fromarray(np.clip(np.asarray(img, np.float32) + g, 0, 255).astype(np.uint8))

# texto (embaixo)
WHITE = (240, 243, 248); RED = (214, 30, 38); BLUE = (40, 110, 235)
d = ImageDraw.Draw(img)
margin, bottom, gap, min_top = 70, H - 64, 14, 1250
f = None
for s_ in range(220, 40, -1):
    f = ImageFont.truetype(FONT, s_)
    w1 = d.textbbox((0,0), "DO NADA,", font=f); w2 = d.textbbox((0,0), "NADA SAI", font=f)
    nb = d.textbbox((0,0), "N", font=f); cap = nb[3] - nb[1]
    if max(w1[2]-w1[0], w2[2]-w2[0]) <= W - 2*margin and bottom - (2*cap + gap) >= min_top: break
top = bottom - (2*cap + gap)
layer = Image.new("RGBA", img.size, (0,0,0,0)); ld = ImageDraw.Draw(layer)
for i, t in enumerate(["DO NADA,", "NADA SAI"]):
    bb = ld.textbbox((0,0), t, font=f)
    ld.text(((W-(bb[2]-bb[0]))//2 - bb[0], top + i*(cap+gap) - nb[1]), t, font=f, fill=WHITE+(255,))
alpha = layer.split()[3]
sh_ = Image.new("RGBA", img.size, (0,0,0,0))
sh_.putalpha(alpha.filter(ImageFilter.GaussianBlur(22)).point(lambda v: min(255, int(v*1.1))))
sh2 = Image.new("RGBA", img.size, (0,0,0,0))
sh2.putalpha(alpha.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v*0.8)))
img = Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(img.convert("RGBA"), sh_), sh2), layer)
# barra giroflex acima do texto
d = ImageDraw.Draw(img); yb = top - 26; half = 70
d.rectangle([(W//2-half, yb), (W//2-3, yb+6)], fill=RED+(255,))
d.rectangle([(W//2+3, yb), (W//2+half, yb+6)], fill=BLUE+(255,))
img.convert("RGB").save(OUT, quality=95, subsampling=0)
print(OUT, img.size, "fonte", f.size, "texto y", top, "-", bottom)
