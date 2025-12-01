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

# Tripple-K brand palette
MAROON      = (153, 0, 0)        # #990000
LIME_GREEN  = (50, 205, 50)      # #32CD32
ORANGE      = (255, 140, 0)      # #FF8C00
WHITE       = (255, 255, 255)
DARK_NAVY   = (15, 15, 35)

# Remote assets
LOGO_URL    = "https://www.tripplek.co.ke/wp-content/uploads/2024/10/Tripple-K-Com-Logo-255-by-77.png"
PRODUCT_URL = "https://www.tripplek.co.ke/wp-content/uploads/2025/02/iphone-16e-33.png"
AUDIO_URL   = "https://ik.imagekit.io/ericmwangi/tech-ambient.mp3?updatedAt=1764372632499"

# --------------------------------------------------------
# CACHED HELPERS
# --------------------------------------------------------
@st.cache_data(show_spinner=False)
def download(url, suffix=".png"):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception as e:
        st.warning(f"Download failed {url[:30]}…  {e}")
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
    return requests.get(url, timeout=10).content

def get_font(size, bold=True):
    size = max(30, int(size))
    try:
        return ImageFont.truetype(io.BytesIO(_font_bytes(bold)), size)
    except Exception:
        try:
            return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
        except:
            return ImageFont.load_default()

# --------------------------------------------------------
# ANIMATED ABSTRACT BACKGROUND (brand colours)
# --------------------------------------------------------
def abstract_bg(t):
    """Generate 1080×1920 RGB frame with floating brand geometry"""
    base = Image.new("RGB", (WIDTH, HEIGHT), DARK_NAVY)
    draw = ImageDraw.Draw(base, "RGBA")

    # 1) Large slow maroon circles (back)
    for i in range(4):
        x = int(WIDTH/2  + 400*math.sin(t*0.2 + i*1.3))
        y = int(HEIGHT/2 + 400*math.cos(t*0.15 + i*1.1))
        r = 280 + 60*math.sin(t*0.3 + i)
        opacity = int(50 + 30*math.sin(t*0.4 + i))
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*MAROON, opacity))

    # 2) Mid-speed lime rectangles (rotate)
    for i in range(6):
        w = 200 + 50*math.sin(t*0.7 + i)
        h = 200 + 50*math.cos(t*0.5 + i)
        cx = WIDTH/2  + 350*math.sin(t*0.6 + i*0.9)
        cy = HEIGHT/2 + 350*math.cos(t*0.5 + i*0.8)
        angle = math.degrees(t*0.4 + i*60)
        coords = []
        for k in range(4):
            θ = math.radians(angle + k*90)
            coords.append((cx + w/2*math.cos(θ), cy + h/2*math.sin(θ)))
        opacity = int(70 + 40*math.sin(t*0.8 + i))
        draw.polygon(coords, fill=(*LIME_GREEN, opacity))

    # 3) Orange hexagons (front layer)
    for i in range(5):
        cx = WIDTH/2  + 300*math.sin(t*0.9 + i*1.7)
        cy = HEIGHT/2 + 300*math.cos(t*1.0 + i*1.5)
        size = 120 + 30*math.sin(t*1.2 + i)
        opacity = int(90 + 50*math.sin(t*1.3 + i))
        hexagon = []
        for k in range(6):
            θ = math.radians(k*60 + t*30 + i*30)
            hexagon.append((cx + size*math.cos(θ), cy + size*math.sin(θ)))
        draw.polygon(hexagon, fill=(*ORANGE, opacity))

    # 4) White glints (top)
    for i in range(20):
        x = int(WIDTH * (0.05 + 0.9*(math.sin(t*2.1 + i*2.3) + 1)/2))
        y = int(HEIGHT * (0.05 + 0.9*(math.cos(t*2.3 + i*1.9) + 1)/2))
        s = 6 + 4*math.sin(t*3 + i)
        opacity = int(180 + 75*math.sin(t*4 + i))
        draw.ellipse([x-s, y-s, x+s, y+s], fill=(*WHITE, opacity))

    return np.array(base)

# --------------------------------------------------------
# DRAW SINGLE FRAME
# --------------------------------------------------------
def draw_frame(t, product, specs, price, overlay_rgb=None):
    rgb  = abstract_bg(t)
    base = Image.fromarray(rgb).convert("RGBA")
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # optional brand colour wash
    if overlay_rgb:
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (*overlay_rgb, 30))
        base = Image.alpha_composite(base, overlay)

    # -- LOGO (top-left) -------------------------------------------------
    logo = load_image(LOGO_URL, (420, 100))
    canvas.paste(logo, (60, 60), logo)

    # -- HEADLINE (CENTRED) ----------------------------------------------
    font_head = get_font(90)
    left, top, right, bottom = draw.textbbox((0, 0), product.upper(), font=font_head)
    w = right - left
    draw.text(((WIDTH - w) // 2, 220), product.upper(), font=font_head, fill=WHITE)

    # -- PRODUCT (centre, gentle float) ----------------------------------
    phone = load_image(PRODUCT_URL, (650, 900))
    float_y = int(450 + 15*math.sin(t*1.1))
    canvas.paste(phone, (WIDTH//2 - 325, float_y), phone)

    # -- RIGHT-SIDE SPECS (fade-in) --------------------------------------
    font_spec = get_font(42, bold=False)
    spec_lines = specs.split("\n")[:4]
    start_y = 480
    for i, txt in enumerate(spec_lines):
        alpha = int(255*min(1, max(0, (t-0.5-i*0.2)*2)))
        if alpha <= 0: continue
        x, y = 750, start_y + i*90
        draw.rounded_rectangle((x-20, y-10, x+320, y+70), radius=18,
                              fill=(255, 255, 255, alpha//2))
        draw.text((x, y), txt, font=font_spec, fill=(30, 30, 30, alpha))

    # -- PRICE TAG (bottom-right, pulse) ---------------------------------
    pulse = 1 + 0.05*math.sin(t*3)
    pw, ph = int(300*pulse), int(90*pulse)
    px, py = WIDTH - pw - 80, HEIGHT - ph - 120
    draw.rounded_rectangle((px, py, px+pw, py+ph), radius=25, fill=MAROON)
    draw.text((px+pw//2, py+ph//2), price, font=get_font(48),
             fill=WHITE, anchor="mm")

    # -- CTA (bottom-left) -----------------------------------------------
    draw.rounded_rectangle((60, HEIGHT-180, 60+350, HEIGHT-180+80),
                          radius=30, fill=MAROON)
    draw.text((60+175, HEIGHT-180+40), "SHOP NOW", font=get_font(46),
             fill=WHITE, anchor="mm")

    # -- WEBSITE ---------------------------------------------------------
    draw.text((WIDTH//2, HEIGHT-50), "www.tripplek.co.ke",
             font=get_font(32, bold=False), fill=WHITE, anchor="mm")

    return Image.alpha_composite(base, canvas)

# --------------------------------------------------------
# EXPORT MP4
# --------------------------------------------------------
def build_video(product, specs, price, overlay_rgb=None):
    frames = []
    bar = st.progress(0)
    for i in range(TOTAL_FRAMES):
        frames.append(np.asarray(draw_frame(i/FPS, product, specs, price, overlay_rgb)))
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
# STREAMLIT UI
# --------------------------------------------------------
st.set_page_config(page_title="TrippleK Ad Studio", layout="centered")
st.title("📱 TrippleK 4-s Abstract Ad Generator")
st.caption("Pure geometric animation • Brand colours • Social-media ready")

c1, c2 = st.columns([1,2])
with c1:
    product = st.text_input("Phone Name", "iPhone 16e")
    specs   = st.text_area("Specs (1 per line)",
                          "A18 Bionic Chip\n48 MP Camera\n256 GB Storage\n20 % Off",
                          height=120)
    price   = st.text_input("Price text", "KSh 145,000")

    # ----- uploads / options -----
    uploaded = st.file_uploader("Upload logo or product (PNG)", type=["png"])
    if uploaded:
        bytes_data = uploaded.read()
        name = "uploaded_logo.png" if "logo" in uploaded.name.lower() else "uploaded_product.png"
        with open(name, "wb") as f: f.write(bytes_data)
        if "logo" in name:
            LOGO_URL = name
        else:
            PRODUCT_URL = name

    brand_colour = st.color_picker("Brand tint overlay (0% = off)", "#990000")
    use_overlay = st.checkbox("Apply colour wash")
    overlay_rgb = tuple(int(brand_colour[i:i+2],16) for i in (1,3,5)) if use_overlay else None

    caption = st.text_area("Caption", f"🔥 {product} now available!\n💥 Limited stock – tap link in bio.", height=80)
    hashtags = st.text_input("Hashtags", "#TrippleK #SmartphoneDeal #KenyaTech")
    if st.button("📋 Copy caption + hashtags"):
        st.code(f"{caption}\n\n{hashtags}")

    # ----- export -----
    if "rendering" not in st.session_state:
        st.session_state.rendering = False
    export = st.button("🚀 Generate 4-s MP4", type="primary", use_container_width=True,
                      disabled=st.session_state.rendering)

with c2:
    if export:
        if not product.strip():
            st.error("Add a product name!"); st.stop()
        st.session_state.rendering = True
        with st.spinner("Rendering…"):
            path = build_video(product, specs, price, overlay_rgb)
        st.session_state.rendering = False
        st.success("✅ Done!")
        with open(path,"rb") as f:
            st.download_button("⬇️ Download MP4", f, file_name="TrippleK_Ad.mp4", use_container_width=True)
        st.video(path)
        try: os.remove(path)
        except: pass
        gc.collect()
        st.experimental_rerun()
    else:
        preview = np.asarray(draw_frame(1.0, product, specs, price, overlay_rgb))
        st.image(preview, use_column_width=True)
