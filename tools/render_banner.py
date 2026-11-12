#!/usr/bin/env python3
"""Rebuild Matheus Oliveira's GitHub motion banner with precise geometry.

  python -m pip install Pillow
  python tools/render_banner.py
  python tools/render_banner.py --verify

Every diagram element shares NODE_Y. Labels use bounding-box centering and
all connector endpoints are computed from the node centers, not hand placed.
No font binaries are embedded. System font fallback works on Windows/Linux/macOS.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
W, H = 1200, 316
SCALE = 2
FRAMES = 28
FRAME_DURATION_MS = 110

NAVY = (0, 8, 35)
SURFACE = (8, 16, 46)
WINDOW = (10, 17, 47)
PURPLE = (84, 21, 255)
LAVENDER = (161, 135, 255)
WHITE = (248, 248, 252)
MUTED = (164, 175, 212)
GREEN = (34, 197, 94)

@dataclass(frozen=True)
class Layout:
    outer: tuple = (30, 26, 1170, 290)
    window_outer: tuple = (748, 56, 1142, 274)
    window_inner: tuple = (764, 74, 1125, 257)
    node_x: tuple = (816, 945, 1074)
    node_y: int = 169
    radius: int = 22
    progress: tuple = (784, 238, 1096, 245)
    status_x: int = 1110

LAYOUT = Layout()


def find_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = {
        "bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "DejaVuSans-Bold.ttf",
        ],
        "regular": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "DejaVuSans.ttf",
        ],
        "mono": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "C:/Windows/Fonts/consola.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "DejaVuSansMono.ttf",
        ],
    }
    for path in candidates[name]:
        try:
            return ImageFont.truetype(path, size * SCALE)
        except (OSError, ValueError):
            pass
    return ImageFont.load_default(size * SCALE)

FONT_NAME = find_font("bold", 48)
FONT_TAG = find_font("regular", 21)
FONT_MONO = find_font("mono", 13)
FONT_MONO_SMALL = find_font("mono", 11)
FONT_BRACE = find_font("mono", 18)
FONT_BADGE = find_font("mono", 12)


def C(coords):
    return tuple(round(v * SCALE) for v in coords)


def rgba(rgb, alpha=255):
    return tuple(rgb) + (int(max(0, min(255, alpha))),)


def rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(C(box), radius=round(radius*SCALE),
                           fill=fill, outline=outline, width=max(1,round(width*SCALE)))


def ellipse(draw, box, fill, outline=None, width=1):
    draw.ellipse(C(box), fill=fill, outline=outline, width=max(1, round(width*SCALE)))


def line(draw, pts, fill, width=1):
    draw.line(C(pts), fill=fill, width=max(1, round(width*SCALE)), joint="curve")


def centered_text(draw, text, x, y, font, fill):
    """Center text by actual glyph bounding box, not approximate character widths."""
    box = draw.textbbox((0, 0), text, font=font)
    tx = x*SCALE - (box[0]+box[2])/2
    ty = y*SCALE - (box[1]+box[3])/2
    draw.text((round(tx), round(ty)), text, font=font, fill=fill)


def left_text(draw, text, x, top, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text((x*SCALE-bb[0], top*SCALE-bb[1]), text, font=font, fill=fill)


def create_base():
    """Static background and card, drawn once at 2x and downsampled at export."""
    image = Image.new("RGBA", (W*SCALE, H*SCALE), rgba(NAVY))
    bloom = Image.new("RGBA", image.size, (0,0,0,0))
    b = ImageDraw.Draw(bloom, "RGBA")
    ellipse(b, (800,-200,1330,420), rgba(PURPLE,33))
    ellipse(b, (1000,-100,1430,350), rgba(GREEN,10))
    bloom = bloom.filter(ImageFilter.GaussianBlur(62*SCALE))
    image = Image.alpha_composite(image,bloom)
    d=ImageDraw.Draw(image, "RGBA")

    # Fine grid, intentionally light to avoid banding in GIF palette.
    for x in range(0,W+1,44):
        line(d,(x,0,x,H),rgba((78,93,149),24))
    for y in range(0,H+1,44):
        line(d,(0,y,W,y),rgba((78,93,149),24))

    rect(d,LAYOUT.outer,20,rgba(SURFACE),rgba((103,104,172),218),1.25)
    rect(d,(30,48,36,267),3,rgba(PURPLE))

    left_text(d,"MATHEUS",72,69,FONT_NAME,rgba(WHITE))
    left_text(d,"OLIVEIRA",72,124,FONT_NAME,rgba(WHITE))
    left_text(d,"Full Stack  /  DevOps  /  AI & Automation",73,206,FONT_TAG,rgba(MUTED))

    # Pill badges — padding is computed from available centered text.
    rect(d,(73,251,239,277),13,rgba((58,41,125)),rgba((130,103,224),230),1)
    centered_text(d,"DESIGN & BUILD",156,264,FONT_BADGE,rgba((232,222,255)))
    rect(d,(253,251,405,277),13,rgba((17,66,60)),rgba((70,151,127),220),1)
    centered_text(d,"TEST & SHIP",329,264,FONT_BADGE,rgba((194,241,214)))

    # Window chrome: nested rounded edges with symmetric padding.
    rect(d,LAYOUT.window_outer,16,rgba((19,27,63)),rgba((127,105,202),231),1.5)
    rect(d,LAYOUT.window_inner,12,rgba(WINDOW),rgba((77,84,138),190),1)
    for j,col in enumerate([(250,112,146),(255,195,104),(68,220,157)]):
        cx=783+13*j
        ellipse(d,(cx-4,91-4,cx+4,91+4),rgba(col))
    left_text(d,"motion.pipeline",834,84,FONT_MONO,rgba((176,181,218)))
    line(d,(783,115,1106,115),rgba((65,76,132),100),1)
    return image


def motion_frame(base: Image.Image, tick: int) -> Image.Image:
    phase=tick/FRAMES
    frame=base.copy()
    # All effects sit within the window and never change element geometry.
    effects=Image.new("RGBA", frame.size,(0,0,0,0))
    e=ImageDraw.Draw(effects,"RGBA")
    x1,x2,x3=LAYOUT.node_x
    cy=LAYOUT.node_y
    radius=LAYOUT.radius
    connector_pad=7

    # Straight rails: same exact baseline as every circle center.
    for a,b in ((x1,x2),(x2,x3)):
        line(e,(a+radius+connector_pad,cy,b-radius-connector_pad,cy),rgba((119,105,206),220),2.5)

    # A small flowing highlight follows one connector, then the next.
    segment=int(phase*2)%2
    local=(phase*2)%1
    a,b=((x1,x2),(x2,x3))[segment]
    lx=a+radius+connector_pad
    rx=b-radius-connector_pad
    px=lx+(rx-lx)*local
    ellipse(e,(px-6,cy-6,px+6,cy+6),rgba((147,112,255),60))
    ellipse(e,(px-3.2,cy-3.2,px+3.2,cy+3.2),rgba((202,186,255),255))

    # Nodes share exact coordinates and equal radii; outlines pulse without resize.
    for i,x in enumerate(LAYOUT.node_x):
        pulse=(1+math.sin(phase*math.tau-i*1.8))/2
        line_alpha=int(164+65*pulse)
        ellipse(e,(x-radius,cy-radius,x+radius,cy+radius),rgba((28,29,80)),rgba((147,111,255),line_alpha),1.6)

    # Built-in primitive icons, avoiding platform-specific Unicode glyph metrics.
    # CODE braces: centered as a single font glyph pair.
    centered_text(e,"{ }",x1,cy-1,FONT_BRACE,rgba(WHITE))
    # MOTION: centered diamond, inner diamond mark.
    e.polygon([
        (x2*SCALE,(cy-9)*SCALE), ((x2+8)*SCALE,cy*SCALE),
        (x2*SCALE,(cy+9)*SCALE), ((x2-8)*SCALE,cy*SCALE)],
              fill=rgba((149,115,255),65),outline=rgba((240,233,255)))
    e.polygon([ (x2*SCALE,(cy-4)*SCALE), ((x2+4)*SCALE,cy*SCALE),
                (x2*SCALE,(cy+4)*SCALE), ((x2-4)*SCALE,cy*SCALE)],
              fill=rgba((230,221,255)))
    # RENDER: monitor/frame drawn symmetrically around center.
    rect(e,(x3-8,cy-7,x3+8,cy+6),2,None,rgba((243,237,255)),1.6)
    line(e,(x3-4,cy+9,x3+4,cy+9),rgba((243,237,255)),1.4)
    line(e,(x3,cy+6,x3,cy+9),rgba((243,237,255)),1.3)

    labels=["CODE","MOTION","RENDER"]
    for x,label in zip(LAYOUT.node_x,labels):
        centered_text(e,label,x,213,FONT_MONO_SMALL,rgba(MUTED))

    # Progress rail and always-contained moving fill.
    px1,py1,px2,py2=LAYOUT.progress
    rect(e,LAYOUT.progress,3.5,rgba((55,62,105),240))
    ratio=0.19+0.57*((math.sin(phase*math.tau-math.pi/2)+1)/2)
    fill_end=px1+(px2-px1)*ratio
    rect(e,(px1,py1,fill_end,py2),3.5,rgba((132,95,255)))
    status_alpha=int(165+90*((math.sin(phase*math.tau)+1)/2))
    ellipse(e,(LAYOUT.status_x-3.6,238.0,LAYOUT.status_x+3.6,245.2),rgba(GREEN,status_alpha))

    # Alpha compositing before RGB conversion prevents palette flicker.
    frame=Image.alpha_composite(frame,effects)
    return frame.convert("RGB").resize((W,H),Image.Resampling.LANCZOS)


def verify_layout(gif_path:Path, png_path:Path):
    xs=LAYOUT.node_x
    assert xs[1]-xs[0] == xs[2]-xs[1], "Node centers are not equally spaced"
    assert LAYOUT.node_y == 169 and all(764+24 < x < 1125-24 for x in xs)
    assert LAYOUT.progress[2] < LAYOUT.status_x - 5
    assert LAYOUT.progress[3] < LAYOUT.window_inner[3]-6
    with Image.open(gif_path) as gif:
        assert gif.size == (W,H), "Wrong banner dimensions"
        assert getattr(gif,"n_frames",1) == FRAMES, "GIF animation is incomplete"
        images=[]
        for k in (0,FRAMES//4,FRAMES//2,FRAMES-1):
            gif.seek(k)
            images.append(gif.convert('RGB').copy())
        assert ImageChops.difference(images[0],images[1]).getbbox(), "GIF does not animate"
    with Image.open(png_path) as png:
        assert png.size == (W,H)
    print(f"PASS | banner {W}x{H} | {FRAMES} frames | equal spacing {xs[1]-xs[0]}px")
    print("PASS | centered labels/icons | shared rail baseline | fully contained progress bar")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify",action="store_true",help="Validate existing outputs without re-rendering")
    args=parser.parse_args()
    ASSETS.mkdir(parents=True,exist_ok=True)
    outgif=ASSETS/"profile-motion.gif"
    outpng=ASSETS/"profile-static.png"
    if not args.verify:
        base=create_base()
        frames=[motion_frame(base,i) for i in range(FRAMES)]
        # One single shared palette is used on every frame to prevent color jitter.
        # Keep tiny status lights and UI accents vivid even after GIF palette reduction.
        # Pure median-cut would otherwise discard red/yellow/green dots as rare pixels.
        accent_colors = [
            (250,112,146), (255,195,104), (68,220,157), GREEN,
            PURPLE, LAVENDER, WHITE, MUTED, (202,186,255),
            (132,95,255), (119,105,206), (10,17,47), (28,29,80),
            (55,62,105), (103,104,172), (194,241,214),
        ]
        sample=frames[FRAMES//3].quantize(colors=220,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
        sample_palette=sample.getpalette()
        combined=list(accent_colors)
        for i in range(0,len(sample_palette),3):
            rgb=tuple(sample_palette[i:i+3])
            if len(rgb)==3 and rgb not in combined:
                combined.append(rgb)
            if len(combined)==256:
                break
        combined.extend([(0,0,0)]*(256-len(combined)))
        palette_image=Image.new("P",(1,1))
        palette_image.putpalette([channel for rgb in combined for channel in rgb])
        quantized=[im.quantize(palette=palette_image,dither=Image.Dither.NONE) for im in frames]
        quantized[0].save(outgif,save_all=True,append_images=quantized[1:],duration=FRAME_DURATION_MS,
                          loop=0,optimize=True,disposal=2)
        frames[8].save(outpng,optimize=True)
        print(f"Created: {outgif} ({outgif.stat().st_size/1024:.0f} KB)")
        print(f"Created: {outpng} ({outpng.stat().st_size/1024:.0f} KB)")
    verify_layout(outgif,outpng)

if __name__=='__main__':
    main()
