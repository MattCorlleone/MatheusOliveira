#!/usr/bin/env python3
"""Render a lightweight, subtle looping motion-graphics GIF for a GitHub profile README.
Requires Pillow. No external assets, fonts embedded or network requests.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'assets'
OUT.mkdir(parents=True,exist_ok=True)
W,H=1200,316
BG=(0,8,35)
P=(84,21,255)
P2=(150,106,255)
GREEN=(34,197,94)
TEXT=(248,248,252)
MUTED=(161,175,210)
FONTS='/usr/share/fonts/truetype/dejavu'
font_bold=lambda n:ImageFont.truetype(f'{FONTS}/DejaVuSans-Bold.ttf',n)
font_regular=lambda n:ImageFont.truetype(f'{FONTS}/DejaVuSans.ttf',n)
font_mono=lambda n:ImageFont.truetype(f'{FONTS}/DejaVuSansMono.ttf',n)

# Persistent background: navy, subtle architectural grid and a purple volumetric bloom.
base=Image.new('RGB',(W,H),BG)
bloom=Image.new('RGBA',(W,H),(0,0,0,0))
bl=ImageDraw.Draw(bloom)
bl.ellipse((745,-170,1330,425),fill=(84,21,255,44))
bl.ellipse((965,-85,1400,300),fill=(34,197,94,11))
bloom=bloom.filter(ImageFilter.GaussianBlur(68))
base=Image.alpha_composite(base.convert('RGBA'),bloom)
g=ImageDraw.Draw(base)
for x in range(0,W,42):
    g.line((x,0,x,H),fill=(65,73,126,15),width=1)
for y in range(0,H,42):
    g.line((0,y,W,y),fill=(65,73,126,15),width=1)
g.rounded_rectangle((30,28,1170,H-28),radius=20,fill=(8,16,47,172),outline=(81,93,157,75),width=2)
g.rounded_rectangle((30,28,38,H-28),radius=4,fill=P)
g.text((67,62),'MATHEUS',font=font_bold(51),fill=TEXT)
g.text((68,125),'OLIVEIRA',font=font_bold(51),fill=TEXT)
g.text((69,201),'Full Stack  /  DevOps  /  AI & Automation',font=font_regular(21),fill=MUTED)
g.rounded_rectangle((67,252,232,278),radius=13,fill=(63,39,132),outline=(130,98,221,130),width=1)
g.text((83,255),'DESIGN & BUILD',font=font_mono(14),fill=(229,215,255))
g.rounded_rectangle((245,252,405,278),radius=13,fill=(21,67,61),outline=(53,141,114,100),width=1)
g.text((268,255),'TEST & SHIP',font=font_mono(14),fill=(183,240,209))
# Design-system-inspired flow diagram on the right
panel=(764,69,1130,264)
g.rounded_rectangle(panel,radius=15,fill=(19,26,62,235),outline=(100,91,170,150),width=2)
g.rounded_rectangle((783,87,1110,245),radius=12,fill=(10,15,47,245),outline=(57,65,112,120),width=1)
g.ellipse((795,99,802,106),fill=(255,106,140))
g.ellipse((808,99,815,106),fill=(255,192,97))
g.ellipse((821,99,828,106),fill=(63,220,151))
g.text((845,95),'motion.pipeline',font=font_mono(13),fill=(172,178,213))
# Nodes and connectors are animated over top of static window.
frames=[]
N=24
for k in range(N):
    phase=k/N
    canvas=base.copy()
    d=ImageDraw.Draw(canvas,'RGBA')
    xs=[836,947,1060]
    # connection rails
    d.line((857,163,926,163),fill=(115,95,190,150),width=3)
    d.line((968,163,1039,163),fill=(115,95,190,150),width=3)
    # Animated motes go from code -> motion -> output
    x=857+182*phase
    d.ellipse((x-6,157,x+6,169),fill=(116,83,255,70))
    d.ellipse((x-3,160,x+3,166),fill=(202,177,255,255))
    glyphs=['{ }','◈','▣']
    labels=['CODE','MOTION','RENDER']
    for i,xx in enumerate(xs):
        pulse=(math.sin(phase*2*math.pi+i*2.2)+1)/2
        rad=18+2*pulse
        d.ellipse((xx-rad,163-rad,xx+rad,163+rad),fill=(30,27,77,255),outline=(120,91,254,int(155+75*pulse)),width=2)
        d.text((xx-13,151),glyphs[i],font=font_mono(19),fill=TEXT)
        tw=d.textbbox((0,0),labels[i],font=font_mono(12))[2]
        d.text((xx-tw/2,192),labels[i],font=font_mono(12),fill=MUTED)
    d.rounded_rectangle((808,226,1084,231),radius=3,fill=(56,61,103,200))
    d.rounded_rectangle((808,226,808+276*phase,231),radius=3,fill=(125,89,255,255))
    d.ellipse((1089,226,1095,232),fill=(34,197,94,int(130+125*((math.cos(phase*2*math.pi)+1)/2))))
    # Subtle right-edge accent, avoiding strobe
    d.line((1109,124,1109,182),fill=(95,61,216,int(100+55*(math.sin(phase*2*math.pi)+1)/2)),width=2)
    frames.append(canvas.convert('RGB'))
# one stable palette avoids cross-frame color flashes; no dithering to keep GIF compact
q0=frames[0].quantize(colors=90,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
pal=q0.getpalette()
quantized=[]
for f in frames:
    pal_image=Image.new('P',(1,1)); pal_image.putpalette(pal)
    quantized.append(f.quantize(palette=pal_image,dither=Image.Dither.NONE))
quantized[0].save(OUT/'profile-motion.gif',save_all=True,append_images=quantized[1:],duration=110,loop=0,optimize=True,disposal=2)
frames[3].save(OUT/'profile-static.png',optimize=True)
print('Rendered',OUT/'profile-motion.gif')
