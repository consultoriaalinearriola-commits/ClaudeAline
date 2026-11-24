import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC="/root/.claude/uploads/8e59e2e6-3645-593b-80b5-678f7b4d2089/97b9348d-image.jpg"
FONT="Anton-Regular.ttf"  # Google Fonts (OFL), ofl/anton
OUT="/home/user/ClaudeAline/inspiracao/do-nada-nada-sai.jpg"
im=Image.open(SRC).convert("RGB"); W,H=im.size
a=np.asarray(im).astype(np.float32)/255.0
# --- color grade (cinematic, moody) ---
lum=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
a=lum[...,None]+(a-lum[...,None])*0.72          # desaturate 28%
a=np.clip((a-0.5)*1.18+0.5,0,1)                  # contrast
a=a**1.12                                        # deepen mids/shadows
lum=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
sh=(1-lum)**2; hi=lum**2
a[...,0]+= -0.035*sh + 0.045*hi                  # teal shadows / warm highlights
a[...,1]+=  0.010*sh + 0.020*hi
a[...,2]+=  0.040*sh - 0.040*hi
# vignette
y,x=np.mgrid[0:H,0:W]; d=np.sqrt(((x-W*0.5)/(W*0.62))**2+((y-H*0.48)/(H*0.62))**2)
a*= (1-0.55*np.clip(d-0.45,0,1)**1.4)[...,None]
# top gradient for text legibility
t=np.clip(1-y/(H*0.19),0,1)**1.3
a*= (1-0.80*t)[...,None]
# bottom gradient
b=np.clip((y-H*0.80)/(H*0.20),0,1)**1.8
a*= (1-0.6*b)[...,None]
img=Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
# light film grain
g=np.random.default_rng(7).normal(0,4,(H,W,1))
img=Image.fromarray(np.clip(np.asarray(img).astype(np.float32)+g,0,255).astype(np.uint8))
# --- text ---
GOLD=(214,170,92); WHITE=(245,242,235)
d=ImageDraw.Draw(img)
def fit(text,maxw,start):
    s=start
    while True:
        f=ImageFont.truetype(FONT,s)
        if d.textbbox((0,0),text,font=f)[2]<=maxw: return f
        s-=2
margin=56; top=34; bottom_limit=232; gap=10
s=200
while True:
    f1=ImageFont.truetype(FONT,s)
    b1=d.textbbox((0,0),"DO NADA,",font=f1); b2=d.textbbox((0,0),"NADA SAI",font=f1)
    capH=d.textbbox((0,0),"N",font=f1); capH=capH[3]-capH[1]
    total=2*capH+gap
    if max(b1[2]-b1[0],b2[2]-b2[0])<=W-2*margin and top+total<=bottom_limit: break
    s-=1
lh=capH+gap
layer=Image.new("RGBA",img.size,(0,0,0,0)); ld=ImageDraw.Draw(layer)
for i,(txt,col) in enumerate([("DO NADA,",WHITE),("NADA SAI",GOLD)]):
    bb=ld.textbbox((0,0),txt,font=f1); w=bb[2]-bb[0]
    nb=ld.textbbox((0,0),'N',font=f1); ld.text(((W-w)//2-bb[0],top+i*lh-nb[1]),txt,font=f1,fill=col+(255,))
shadow=Image.new("RGBA",img.size,(0,0,0,0)); shadow.putalpha(layer.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v:int(v*0.75)))
img=img.convert("RGBA"); img=Image.alpha_composite(img,shadow); img=Image.alpha_composite(img,layer)
# accent rule under text
d=ImageDraw.Draw(img); ytxt=top+2*lh+8
pass
img.convert("RGB").save(OUT,quality=95,subsampling=0)
print(OUT,img.size,"font",s)
