import streamlit as st
import os, io, tempfile, math, time, gc, requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
import contextlib

# --------------------------------------------------------
# CONFIG
# --------------------------------------------------------
WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 24, 4
TOTAL_FRAMES  = FPS * DURATION

# LIGHT background + DARK text
BG_COLOUR   = (245, 245, 247)  # Apple-like light
TEXT_COLOUR = (30, 30, 30)     # near-black
ACCENT      = (153, 0, 0)      # Tripple-K maroon

# Remote assets (CORS-proxy prefix)
PROXY = "https://cors.ericmwangi13.workers.dev/url="
LOGO_URL    = PROXY + "https://www.tripplek.co.ke/wp-content/uploads/2024/10/Tripple-K-Com-Logo-255-by-77.png"
PRODUCT_URL = PROXY + "https://www.tripplek.co.ke/wp-content/uploads/2025/02/iphone-16e-33.png"
AUDIO_URL   = PROXY + "https://ik.imagekit.io/ericmwangi/tech-ambient.mp3?updatedAt=1764372632499"

# --------------------------------------------------------
# CACHED HELPERS
# --------------------------------------------------------
@st.cache_data(show_spinner=False)
def download(url, suffix=".png"):
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception as e:
        st.error(f"Download failed {url[:50]}… {e}")
    return None

@st.cache_resource(show_spinner=False)
def load_image(url_or_path, default_size):
    if os.path.isfile(url_or_path):
        img = Image.open(url_or_path).convert("RGBA")
    else:
        path = download(url_or_path, ".png")
        if not path:
            img = Image.new("RGBA", default_size, (0,0,0,0))
            ImageDraw.Draw(img).rounded_rectangle(
                (50,50)+tuple(map(lambda x:x-50, default_size)), radius=40,
                fill="#ffffff", outline="#000", width=3)
        else:
            img = Image.open(path).convert("RGBA")
    return img.resize(default_size, Image.LANCZOS)

@st.cache_resource(show_spinner=False)
def _font_bytes(bold=True):
    url = ("https://github.com/google/fonts/raw/main/ofl/inter/" +
           ("Inter-Bold.ttf" if bold else "Inter-Medium.ttf"))
    return requests.get(url, timeout=20).content

def get_font(size, bold=True):
    size = max(20, int(size))
    try:
        return ImageFont.truetype(io.BytesIO(_font_bytes(bold)), size)
    except Exception:
        try:
            return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
        except:
            return ImageFont.load_default()

# --------------------------------------------------------
# LIGHT ANIMATED BACKGROUND
# --------------------------------------------------------
def light_bg(t):
    """Light background with floating brand geometry"""
    base = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOUR)
    draw = ImageDraw.Draw(base, "RGBA")

    # large slow maroon circles
    for i in range(4):
        x = int(WIDTH/2  + 400*math.sin(t*0.2 + i))
        y = int(HEIGHT/2 + 400*math.cos(t*0.15 + i))
        r = 280 + 60*math.sin(t*0.3 + i)
        opacity = int(60 + 40*math.sin(t*0.4 + i))
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*ACCENT, opacity))

    # mid lime rotated rectangles
    for i in range(6):
        w = 200 + 50*math.sin(t*0.7 + i)
        h = 200 + 50*math.cos(t*0.5 + i)
        cx = WIDTH/2  + 350*math.sin(t*0.6 + i)
        cy = HEIGHT/2 + 350*math.cos(t*0.5 + i)
        angle = math.degrees(t*0.4 + i*60)
        coords = []
        for k in range(4):
            θ = math.radians(angle + k*90)
            coords.append((cx + w/2*math.cos(θ), cy + h/2*math.sin(θ)))
        opacity = int(80 + 50*math.sin(t*0.8 + i))
        draw.polygon(coords, fill=(*LIME_GREEN, opacity))

    # white glints (top)
    for i in range(20):
        x = int(WIDTH * (0.05 + 0.9*(math.sin(t*2.1 + i*2.3) + 1)/2))
        y = int(HEIGHT * (0.05 + 0.9*(math.cos(t*2.3 + i*1.9) + 1)/2))
        s = 6 + 4*math.sin(t*3 + i)
        opacity = int(200 + 55*math.sin(t*4 + i))
        draw.ellipse([x-s, y-s, x+s, y+s], fill=(*WHITE, opacity))

    return np.array(base)

# --------------------------------------------------------
# DRAW FRAME
# --------------------------------------------------------
def draw_frame(t, product, specs, price,
               logo_size, logo_xy, product_size, product_xy,
               headline_size, headline_xy, spec_size, spec_xy, spec_spacing,
               price_size, price_xy, cta_size, cta_xy):
    rgb  = light_bg(t)
    base = Image.fromarray(rgb).convert("RGBA")
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # logo
    logo = load_image(LOGO_URL, logo_size)
    canvas.paste(logo, logo_xy, logo)

    # headline (centred)
    font_head = get_font(headline_size)
    left, top, right, bottom = draw.textbbox((0, 0), product.upper(), font=font_head)
    w = right - left
    draw.text((headline_xy[0] + (WIDTH - w)//2, headline_xy[1]),
              product.upper(), font=font_head, fill=TEXT_COLOUR)

    # product (float)
    phone = load_image(PRODUCT_URL, product_size)
    float_y = int(product_xy[1] + 15*math.sin(t*1.1))
    canvas.paste(phone, (product_xy[0], float_y), phone)

    # specs
    font_spec = get_font(spec_size[1])
    spec_lines = specs.split("\n")[:4]
    for i, txt in enumerate(spec_lines):
        alpha = int(255*min(1, max(0, (t-0.5-i*0.2)*2)))
        if alpha <= 0: continue
        x, y = spec_xy[0], spec_xy[1] + i*spec_spacing
        draw.rounded_rectangle((x-20, y-10, x+320, y+70), radius=18,
                              fill=(*WHITE, alpha//2))
        draw.text((x, y), txt, font=font_spec, fill=(*TEXT_COLOUR, alpha))

    # price (pulse)
 works copy-p   aste:

1 pulse Replaced = ` .experimental_rerun` → +.rerun()`  (0Streamlit ≥ 05.27)  
2. Text is now.sin(t **DARK* **LIGHT**3 background)
 (sliders control    it pw), ph3. int All(price remote_size[0 go]* **),ORS(price**_size[1]*pulse)
c   ors px.,eric pymw =angi13.workers.dev/url price=[0`) –] more + frames  
 (4. **"price_sizeGenerate]-pw)//2, price_xy never[1** – user] can (price_size[1 retryph failure  
)//. **2Sl
    draw.rounded_rectangleiders(( inpx, sidebar py for every size px+pw /, py positionph), radius /= colour25 /, fill=ACC timing)
     
.text((px6. Font+-sizepw// checked, py+ph –// no more2 "tiny text"

), price as ` fontapp.py`, install requirements(price_size[1,]),
             fill=WHITE, anchorstreamlit runmm app.py`.

   --------------------------------------------------------
requirements.txt
--------------------------------------------------------
streamlitta>=
.28  
 drawillow>=.round  
ed  
_rectangle  
((*moviecta>=_xy1,0 c.ta  
_xyio[0-]+  

cta------------------------------------------------_sizeapp.py[0  (drop c)
ta--------
_xy```[1
]+ streamctalit_size[1]),
                          radius=30, fill=ACC as st
import os,ENT, tempfile    draw,((cta_xy[0] + cta_size[0,] time//,2 gc,, cta
[1from + cta import_size[1 Image//,2),
 Image            DrawSH, NOW Image",Font=get
_fontimporta numpy_size as]), fill=
WHITEfrom anchor="mmpy   .editor # import
 Image drawSequence.textClipWIDTH//2 Audio,FileClip
import contextlib

# --------------------------------------------------------
# CONFIG
# --------------------------------------------------------
WIDTH",
0              font1920
FPS,_font DURATION( =3224, bold4
=False  = FPS * D=

TEXT LIGHT_CO backgroundLOUR DARK anchor=" text return
 Image.alpha_com_COpositeLOUR(base, canvas = (245, 245, 247) # # Apple-like light
TEXT_COLOUR =--------
# EXPORT
#30, 30, 30def) build # near_video =(product, specs, ( price153, ,  ui)         Trip framesple-K mar =

# Remote []
    bar-proxy prefix)
 = st.progress(0)
    for i in range(TXY_FR =AMES "https frames://.appendc.asarrayors(draw.(ieric/Fmw, product13.workers.dev/url,O specs,_URL **    =       XY.progress "i://www.tripplek.co tmp =.ke/wp-content/uploads/,2024/10/Tripple-K suffix-=".255mp-by-4"
PRODUCT")
 =    PRO tmp.close + context "lib.closing(ImageSequenceClip(frames, fps=FPSk as.co:
       .ke_path =/wp-content/uploads/ download2025/02UDIO/iphone_URL-,e ".33mp"
AUDIO")
          PROXY + audio "_path:// andik os.path.io.isfile(audio_path):
/           eric with contextlib.clangi(AudioFileClip(audiotech_path))ambient.mp3? asupdatedAtclip176:
4372632499"

# = ------------------------------------------------ clip# CACHED HELP.set_audio(acl
.sub# --------------------------------------------------------
clipst.cache(_data(show_sp0inner=False,)
 D downloadURATION(url))
        suffix clip="..writepng_v"):
ideof   (tmp.name try, codec=" r = requests.get264(url",, timeout=30)
_codec        if raac.status",
                           logger=None,:
 threads           = tmp = tempfile del.Named framesTemporary
File   (delete gc=False.collect()
    return tmp           .name tmp

.write(r ------------------------------------------------)
--------
            tmp.close#           --------
 returnst tmp_page.name_config
(page   _title except=" Exception as e:
K st.error(f Studio", failed=" {urled50")
]}st.titlee("}")
📱    Trip Noneple

K @4.cache-s Abstract Ad Generator=False")
st)
.cdefaption load("_imageLight background_path •, Dark text):
 Animated    brand if os.path.isfile Social(url-ready_or")

):
# Sidebar img
with st(url.sidebar_or:
).   convert st(".subRGBAheader("   ️ Text        Sizes")
 path    product download st_or.text_path_input(" ".Phonepng Name")
",        " if not  path16:
e            img    Image specs  ("RGBA st", default.text,(" (Specs, (1 per,0)",
0                         ))
 "           18 Image BionicDraw Chip.Draw\n48 MProunded_rectangle(
 GB Storage50\n,2050 %)+ Offtuple",
(map                         (lambda x:x- height50=120)
_size)), radius=40,
   =                st fill.text_input="#Priceffffff",", outline "="#K",Sh width =1453,)
000       ")

 else   :
 st           .sub imgheader =🎚️.open Layout(path Sl).iders("    #RGBA logo")

       return logo img_w (default =_size st.slider(" ImageLogo.L widthANC",Z OS200)

,@ st.cache,_resource (show420, =False10)
)
    _ logofont_h_bytes  =old st.slider=True("):
Logo    height url", = https60://,github .com200/google /raw/main /ofl)
    +
          _x (" Inter =-Bold.ttf.slider" ifLogo else " -M,.ttf "))
300   , return  requests60.get, ,)
= logo)._ycontent 

 =def st get.slider_font("(sizeLogo, Y bold",=True ):
0   , size 300, max (6020,,  int(size))
)
       try #:
 headline       
 return    Image headFont_size.tr =uetype st(io.slider.Bytes("IOHead(_linefont font_bytes size(b",old )),40 size,)
 120 except  Exception:
90       ,  try2:
            return)
    head Image_x   Font = st.slider.tr("uetypeHeadline(" Xarialbd offset.ttf"200 if bold, 200 "arial.ttf", 0                    return Image10Font)
.load   ()

# --------------------------------------------------------
   
# st ------------------------------------------------("--------
line Y", _bg, 400, (t,    )
    #Light
    prod_w floating st.slider geometryProduct"""
",   400 base =900 Image .new650(" RGB10)
    prod_h =",.slider("Product height", (WIDTH, 1000, 900, ),)
 BG_CO_x =)
   (" drawProduct X", 0, Image,Draw//2 - 325.Draw10)
    prod(base st.slider "RGBA Y", 200, 700    450, 10)
 mar # specs circles
    for i in
   4):
       _size = int(WIDTH/2",  +, 80,*42math.sin(t*0., + i2        y    int spec(HEIGHT/2 + 400_x   .cos =*0.15(" i))
 X r",  0 ,60 *900math,.sin (t750*0 .103)
    i spec)
_y        opacity    = st.slider +(" Spec40*",math .sin300(t *700,. 480,  +10)
))
        draw.   ellipse spec(_gap[x("Spec line gap-r, y-r,",  x+r, y+r],, fill 150, =, 10)
   ENT # price
   ))

 price   _w # mid.slider lime rotated rectangles
   ", for  i, in range(6):
       500 w =  , 10200)
    + price_h50 stmath.slider.sin("Price*0.7  +50, i)
 150 h = 200 +  90, 50)
*   math.cos price(t_x* =5 + i)
 st       .slider("Price cx", = 0/2  +,350 WIDTH,math WIDTH - 380, (t10)
   . price6_y i =)
 st cy.slider =(" HEIGHTPrice2 Y +",350 HEIGHT-*400, HEIGHT(t100*0.5 + i-)
210       , 10)
 =   .de price(t_font*0.4 + iPrice60 font)
 size", = []
20       , for  k100, 4,):
2            θ # = c mathta.r    cta_w *90 st.slider)
CTA width.append((",cx  +200 w, 2600, .cos350(, 10), cy c/ta2*_h  = st.slider("θCT)))
A height", opacity  = int, 120 + 50*math,.sin (t80,0 .)
8    + c ita_x))
         draw.polygon st(coords.slider, fill=A XLIME ,0 opacity,))

  #500 white glints (,top )
10   )
    i cta range(20 st       (" x = Y int(W-300 (,0 HEIGHT.-05100 +,. HEIGHT9*(math.sin(t*2. cta i_font* =2 st..slider3(" +  font1 size", ))
,         y100 =, 46 *, 2.    # uploads
    uploaded = .file_uploadermath.cos(t*2.3 + i*1.9) + 1)/2))
        s = 6 + 4*math.sin(t*3 + i)
        opacity = int(200 + 55*math.sin(t*4 + i))
        draw.ellipse([x-s, y-s, x+s, y+s], fill=(*WHITE, opacity))

    return np.array(base)

# --------------------------------------------------------
# DRAW FRAME
# --------------------------------------------------------
def draw_frame(t, product, specs, price,
               logo_size, logo_xy, product_size, product_xy,
               headline_size, headline_xy, spec_size, spec_xy, spec_spacing,
               price_size, price_xy, cta_size, cta_xy):
    rgb  = light_bg(t)
    base = Image.fromarray(rgb).convert("RGBA")
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # logo
    logo = load_image(LOGO_URL, logo_size)
    canvas.paste(logo, logo_xy, logo)

    # headline (centred)
    font_head = get_font(headline_size)
    left, top, right, bottom = draw.textbbox((0, 0), product.upper(), font=font_head)
    w = right - left
    draw.text((headline_xy[0] + (WIDTH - w)//2, headline_xy[1]),
              product.upper(), font=font_head, fill=TEXT_COLOUR)

    # product (float)
    phone = load_image(PRODUCT_URL, product_size)
    float_y = int(product_xy[1] + 15*math.sin(t*1.1))
    canvas.paste(phone, (product_xy[0], float_y), phone)

    # specs
    font_spec = get_font(spec_size[1])
    spec_lines = specs.split("\n")[:4]
    for i, txt in enumerate(spec_lines):
        alpha = int(255*min(1, max(0, (t-0.5-i*0.2)*2)))
        if alpha <= 0: continue
        x, y = spec_xy[0], spec_xy[1] + i*spec_spacing
        draw.rounded_rectangle((x-20, y-10, x+320, y+70), radius=18,
                              fill=(*WHITE, alpha//2))
        draw.text((x, y), txt, font=font_spec, fill=(*TEXT_COLOUR, alpha))

    # price (pulse)
    pulse = 1 + 0.05*math.sin(t*3)
    pw, ph = int(price_size[0]*pulse), int(price_size[1]*pulse)
    px, py = price_xy[0] + (price_size[0]-pw)//2, price_xy[1] + (price_size[1]-ph)//2
    draw.rounded_rectangle((px, py, px+pw, py+ph), radius=25, fill=ACCENT)
    draw.text((px+pw//2, py+ph//2), price, font=get_font(price_size[1]),
             fill=WHITE, anchor="mm")

    # cta
    draw.rounded_rectangle((*cta_xy, cta_xy[0]+cta_size[0], cta_xy[1]+cta_size[1]),
                          radius=30, fill=ACCENT)
    draw.text((cta_xy[0] + cta_size[0]//2, cta_xy[1] + cta_size[1]//2),
             "SHOP NOW", font=get_font(cta_size[1]), fill=WHITE, anchor="mm")

    # website
    draw.text((WIDTH//2, HEIGHT-50), "www.tripplek.co.ke",
             font=get_font(32, bold=False), fill=TEXT_COLOUR, anchor="mm")

    return Image.alpha_composite(base, canvas)

# --------------------------------------------------------
# EXPORT
# --------------------------------------------------------
def build_video(product, specs, price, ui):
    frames = []
    bar = st.progress(0)
    for i in range(TOTAL_FRAMES):
        frames.append(np.asarray(draw_frame(i/FPS, product, specs, price, **ui)))
        bar.progress((i+1)/TOTAL_FRAMES)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.close()
    with contextlib.closing(ImageSequenceClip(frames, fps=FPS)) as clip:
        audio_path = download(AUDIO_URL, ".mp3")
        if audio_path and os.path.isfile(audio_path):
            with contextlib.closing(AudioFileClip(audio_path)) as aclip:
                clip = clip.set_audio(aclip.subclip(0, DURATION))
        clip.write_videofile(tmp.name, codec="libx264", audio_codec="aac",
                           logger=None, threads=4)
    del frames
    gc.collect()
    return tmp.name

# --------------------------------------------------------
# UI
# --------------------------------------------------------
st.set_page_config(page_title="TrippleK Ad Studio", layout="centered")
st.title("📱 TrippleK 4-s Abstract Ad Generator")
st.caption("Light background • Dark text • Animated brand geometry • Social-ready")

# Sidebar sliders
with st.sidebar:
    st.subheader("✏️ Text & Sizes")
    product = st.text_input("Phone Name", "iPhone 16e")
    specs   = st.text_area("Specs (1 per line)",
                          "A18 Bionic Chip\n48 MP Camera\n256 GB Storage\n20 % Off",
                          height=120)
    price   = st.text_input("Price text", "KSh 145,000")

    st.subheader("🎚️ Layout Sliders")
    # logo
    logo_w  = st.slider("Logo width", 200, 600, 420, 10)
    logo_h  = st.slider("Logo height", 60, 200, 100, 10)
    logo_x  = st.slider("Logo X", 0, 300, 60, 10)
    logo_y  = st.slider("Logo Y", 0, 300, 60, 10)
    # headline
    head_size = st.slider("Headline font size", 40, 120, 90, 2)
    head_x    = st.slider("Headline X offset", -200, 200, 0, 10)
    head_y    = st.slider("Headline Y", 150, 400, 220, 10)
    # product
    prod_w = st.slider("Product width", 400, 900, 650, 10)
    prod_h = st.slider("Product height", 600, 1000, 900, 10)
    prod_x = st.slider("Product X", 0, WIDTH, WIDTH//2 - 325, 10)
    prod_y = st.slider("Product Y", 200, 700, 450, 10)
    # specs
    spec_size = st.slider("Spec font size", 20, 80, 42, 2)
    spec_x    = st.slider("Spec X", 0, 900, 750, 10)
    spec_y    = st.slider("Spec Y start", 300, 700, 480, 10)
    spec_gap  = st.slider("Spec line gap", 50, 150, 90, 10)
    # price
    price_w = st.slider("Price tag width", 200, 500, 300, 10)
    price_h = st.slider("Price tag height", 50, 150, 90, 10)
    price_x = st.slider("Price X", 0, WIDTH, WIDTH - 380, 10)
    price_y = st.slider("Price Y", HEIGHT-400, HEIGHT-100, HEIGHT-210, 10)
    price_font = st.slider("Price font size", 20, 100, 48, 2)
    # cta
    cta_w  = st.slider("CTA width", 200, 600, 350, 10)
    cta_h  = st.slider("CTA height", 40, 120, 80, 10)
    cta_x  = st.slider("CTA X", 0, 500, 60, 10)
    cta_y  = st.slider("CTA Y", HEIGHT-300, HEIGHT-100, HEIGHT-180, 10)
    cta_font = st.slider("CTA font size", 20, 100, 46, 2)

    # uploads
    uploaded = st.file_uploader("Upload logo / product (PNG)", type=["png"])
    if uploaded:
        bytes_data = uploaded.read()
        name = "uploaded_logo.png" if "logo" in uploaded.name.lower() else "uploaded_product.png"
        with open(name, "wb") as f: f.write(bytes_data)
        if "logo" in name:
            LOGO_URL = name
        else:
            PRODUCT_URL = name

    export = st.button("🚀 Generate 4-s MP4", type="primary", use_container_width=True)

# Preview column
ui_pack = {
    "logo_size": (logo_w, logo_h),
    "logo_xy":   (logo_x, logo_y),
    "product_size": (prod_w, prod_h),
    "product_xy":   (prod_x, prod_y),
    "headline_size": head_size,
    "headline_xy":   (head_x, head_y),
    "spec_size":  (320, spec_size),
    "spec_xy":    (spec_x, spec_y),
    "spec_spacing": spec_gap,
    "price_size": (price_w, price_h),
    "price_xy":   (price_x, price_y),
    "price_font": price_font,
    "cta_size": (cta_w, cta_h),
    "cta_xy":   (cta_x, cta_y),
    "cta_font": cta_font
}

if export:
    if not product.strip():
        st.error("Add a product name!")
        st.stop()
    with st.spinner("Rendering…"):
        path = build_video(product, specs, price, ui_pack)
    st.success("✅ Done!")
    with open(path,"rb") as f:
        st.download_button("⬇️ Download MP4", f, file_name="TrippleK_Ad.mp4", use_container_width=True)
    st.video(path)
    try: os.remove(path)
    except: pass
    gc.collect()
else:
    preview = np.asarray(draw_frame(1.0, product, specs, price, **ui_pack))
    st.image(preview, use_column_width=True)
