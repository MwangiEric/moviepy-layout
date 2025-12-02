import streamlit as st
import os, io, tempfile, math, time, gc, requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
import contextlib
import cv2
import base64

# --------------------------------------------------------
# CONFIG
# --------------------------------------------------------
WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 24, 4
TOTAL_FRAMES  = FPS * DURATION

# Colours
MAROON      = (153, 0, 0)
WHITE       = (255, 255, 255)
LIME_GREEN  = (50, 205, 50)
TEXT_COLOUR = (30, 30, 30)
BG_COLOUR   = (245, 245, 247)
ACCENT      = (153, 0, 0)
ACCENT_GOLD = "#D4AF37"

# Remote assets (CORS proxy)
PROXY = "https://cors.ericmwangi13.workers.dev/?url="
LOGO_URL    = "https://ik.imagekit.io/ericmwangi/tklogo.png?updatedAt=1764543349107"
PRODUCT_URL = PROXY + "https://www.tripplek.co.ke/wp-content/uploads/2025/02/iphone-16e-33.png"
AUDIO_URL   = PROXY + "https://ik.imagekit.io/ericmwangi/tech-ambient.mp3?updatedAt=1764372632499"

# --------------------------------------------------------
# MULTI-FORMAT SIZES
# --------------------------------------------------------
FORMAT_SIZES = {
    "TikTok / Reels (9:16)": (1080, 1920),
    "Instagram (4:5)":       (1080, 1350),
    "WhatsApp Story (1:1)":  (1080, 1080),
}

# --------------------------------------------------------
# BASE64 SESSION CACHE  (download once, reuse forever)
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

@st.cache_resource  # ← CHANGE THIS
def url_to_base64(url, name):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        b64 = base64.b64encode(resp.content).decode()
        st.session_state[name] = b64
        return b64
    except Exception as e:
        st.warning(f"❌ {name} download failed: {e}")
        st.session_state[name] = None
        return None

# --------------------------------------------------------
# FONT HELPERS  (cached)
# --------------------------------------------------------
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


def b64_to_pil(b64, target_size, name):
    """
    Base64 string → PIL RGBA image.
    Never crashes, always returns an image.
    """
    if b64 is None:
        st.info(f"🎨 Fallback {name}")
        return _fallback_image(target_size, name)
    try:
        raw = base64.b64decode(b64)
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        st.success(f"✅ {name} loaded")
        return img.resize(target_size, Image.Resampling.LANCZOS)
    except Exception as e:
        st.error(f"❌ {name} decode error: {e}")
        return _fallback_image(target_size, name)


def _fallback_image(size, name):
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if "logo" in name.lower():
        draw.rounded_rectangle([w//10, h//10, 9*w//10, 9*h//10], radius=20, fill=MAROON)
        draw.text((w//2, h//2), "TK", fill=WHITE, font=get_font(h//3), anchor="mm")
    else:
        draw.rounded_rectangle([w//8, h//8, 7*w//8, 7*h//8], radius=50,
                              fill="#F0F0F0", outline="#333", width=3)
        draw.text((w//2, h//2), "PHONE", fill="#666", font=get_font(h//5), anchor="mm")
    return img

# --------------------------------------------------------
# FORCE DOWNLOAD ONCE  (visible in sidebar)
# --------------------------------------------------------
with st.sidebar:
    if st.button("🔁 Re-download images"):
        url_to_base64(LOGO_URL, "logo_b64")
        url_to_base64(PRODUCT_URL, "product_b64")
        st.rerun()

# auto-download on first run
if "logo_b64" not in st.session_state:
    url_to_base64(LOGO_URL, "logo_b64")
if "product_b64" not in st.session_state:
    url_to_base64(PRODUCT_URL, "product_b64")


# --------------------------------------------------------
# CPU FILTERS  (choose one)
# --------------------------------------------------------
def cpu_filters(frame):
    """Zero overhead – original colours"""
    return frame

def minimal_vignette(frame):
    h, w = frame.shape[:2]
    x, y = np.meshgrid(np.arange(w), np.arange(h))
    mask = 1 - (x/w - 0.5)**2 - (y/h - 0.5)**2
    mask = np.clip(mask * 1.2, 0.8, 1.0)
    return (frame * mask[:,:,np.newaxis]).astype(np.uint8)

def ease_out_elastic(t):
    c4 = (2 * math.pi) / 3
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

# --------------------------------------------------------
# LIGHT ANIMATED BACKGROUND  (your original)
# --------------------------------------------------------
def light_bg(t):
    base = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOUR)
    draw = ImageDraw.Draw(base, "RGBA")

    for i in range(4):
        x = int(WIDTH / 2 + 400 * math.sin(t * 0.2 + i))
        y = int(HEIGHT / 2 + 400 * math.cos(t * 0.15 + i))
        r = 280 + 60 * math.sin(t * 0.3 + i)
        opacity = int(60 + 40 * math.sin(t * 0.4 + i))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*ACCENT, opacity))

    for i in range(6):
        w = 200 + 50 * math.sin(t * 0.7 + i)
        h = 200 + 50 * math.cos(t * 0.5 + i)
        cx = WIDTH / 2 + 350 * math.sin(t * 0.6 + i)
        cy = HEIGHT / 2 + 350 * math.cos(t * 0.5 + i)
        angle = math.degrees(t * 0.4 + i * 60)
        coords = []
        for k in range(4):
            θ = math.radians(angle + k * 90)
            coords.append((cx + w / 2 * math.cos(θ), cy + h / 2 * math.sin(θ)))
        opacity = int(80 + 50 * math.sin(t * 0.8 + i))
        draw.polygon(coords, fill=(*LIME_GREEN, opacity))

    for i in range(20):
        x = int(WIDTH * (0.05 + 0.9 * (math.sin(t * 2.1 + i * 2.3) + 1) / 2))
        y = int(HEIGHT * (0.05 + 0.9 * (math.cos(t * 2.3 + i * 1.9) + 1) / 2))
        s = 6 + 4 * math.sin(t * 3 + i)
        opacity = int(200 + 55 * math.sin(t * 4 + i))
        draw.ellipse([x - s, y - s, x + s, y + s], fill=(*WHITE, opacity))

    return np.array(base)

# --------------------------------------------------------
# DYNAMIC TEXT SPLITTING  (auto-wrap to width)
# --------------------------------------------------------
def split_text_dynamic(text, font, max_width):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = ' '.join(cur + [w])
        if font.getbbox(test)[2] <= max_width:
            cur.append(w)
        else:
            if cur: lines.append(' '.join(cur))
            cur = [w]
    if cur: lines.append(' '.join(cur))
    return lines

# --------------------------------------------------------
# AUTO-TITLE FONT  (fits any car/phone name)
# --------------------------------------------------------
@st.cache_resource
def adjust_title_font(text, max_width, bold=True, start=200, min_sz=45):
    size = start
    while size >= min_sz:
        font = get_font(size, bold)
        if font.getbbox(text)[2] <= max_width:
            return font
        size -= 2
    return get_font(min_sz, bold)

# --------------------------------------------------------
# TEXT BOX  (scale to box)
# --------------------------------------------------------
def text_box(text, font, colour):
    dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy)
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    w, h = r - l, b - t
    box = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(box)
    draw.text((-l, -t), text, font=font, fill=colour)
    return box

# --------------------------------------------------------
# DRAW FRAME  (multi-format + dynamic text)
# --------------------------------------------------------
def draw_frame(t, product, specs, price,
               logo_size, logo_xy, product_size, product_xy,
               headline_size, headline_xy, spec_size, spec_xy, spec_spacing,
               price_size, price_xy, price_font,
               cta_size, cta_xy, cta_font, fmt="TikTok / Reels (9:16)"):

    w, h = FORMAT_SIZES[fmt]
    rgb  = light_bg(t)
    base = Image.fromarray(rgb).convert("RGBA")
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # logo (base64 – never crashes)
    logo = b64_to_pil(st.session_state.get("logo_b64"), logo_size, "Logo")
    canvas.paste(logo, logo_xy, logo)

    # product (base64 – never crashes)
    phone = b64_to_pil(st.session_state.get("product_b64"), product_size, "Product")
    float_y = int(product_xy[1] + 15 * math.sin(t * 1.1))
    prod_x = (w - product_size[0]) // 2 + product_xy[0]
    canvas.paste(phone, (prod_x, float_y), phone)

    # TITLE – auto-fit font + centre
    title_font = adjust_title_font(product.upper(), w - 200, bold=True)
    title_img  = text_box(product.upper(), title_font, ACCENT_GOLD)
    title_x    = (w - title_img.width) // 2 + headline_xy[0]
    canvas.paste(title_img, (title_x, headline_xy[1]), title_img)

    # SPECS – auto-wrap + centre
    spec_lines = split_text_dynamic(specs, get_font(spec_size[1]), 310)
    start_y = h // 2 - 150
    for i, line in enumerate(spec_lines[:4]):
        alpha = int(255 * min(1, max(0, (t - 0.5 - i * 0.2) * 2)))
        if alpha <= 0: continue
        y = start_y + i * spec_spacing
        card = Image.new("RGBA", (320, 70), (*WHITE, alpha // 2))
        canvas.paste(card, (spec_xy[0] - 20, y - 10), card)
        txt_img = text_box(line, get_font(spec_size[1]), (*TEXT_COLOUR, alpha))
        canvas.paste(txt_img, (spec_xy[0], y), txt_img)

    # PRICE – pulse
    pulse = 1 + 0.05 * math.sin(t * 3)
    pw, ph = int(price_size[0] * pulse), int(price_size[1] * pulse)
    px = (w - pw) // 2 + price_xy[0]
    py = price_xy[1] + (price_size[1] - ph) // 2
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((px, py, px + pw, py + ph), radius=25, fill=(*ACCENT, 255))
    price_img = text_box(price, get_font(price_font), WHITE)
    canvas.paste(price_img,
                (px + (pw - price_img.width) // 2,
                 py + (ph - price_img.height) // 2),
                price_img)

    # CTA – fills button
    cta_img = text_box("SHOP NOW", get_font(cta_font), WHITE)
    canvas.paste(cta_img,
                (cta_xy[0] + (cta_size[0] - cta_img.width) // 2,
                 cta_xy[1] + (cta_size[1] - cta_img.height) // 2),
                cta_img)

    # website
    web_img = text_box("www.tripplek.co.ke", get_font(32, bold=False), TEXT_COLOUR)
    canvas.paste(web_img,
                ((w - web_img.width) // 2, h - 50),
                web_img)

    # NO colour-space crash – keep original RGBA
    np_canvas = np.asarray(canvas)
    np_canvas = cpu_filters(np_canvas)   # optional grain
    return Image.alpha_composite(base, Image.fromarray(np_canvas, "RGBA"))
# --------------------------------------------------------
# MULTI-FORMAT EXPORT  (TikTok / IG / WhatsApp)
# --------------------------------------------------------
def build_video(product, specs, price, ui, fmt="TikTok / Reels (9:16)"):
    w, h = FORMAT_SIZES[fmt]
    frames = []
    bar = st.progress(0)
    for i in range(TOTAL_FRAMES):
        frames.append(np.asarray(draw_frame(i / FPS, product, specs, price, **ui, fmt=fmt)))
        bar.progress((i + 1) / TOTAL_FRAMES)

    clip = ImageSequenceClip(frames, fps=FPS)
    audio_path = download(AUDIO_URL, ".mp3")
    if audio_path and os.path.isfile(audio_path):
        with contextlib.closing(AudioFileClip(audio_path)) as aclip:
            clip = clip.set_audio(aclip.subclip(0, DURATION))

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.close()
    # single-pass: crf 18 + fast preset + faststart
    clip.write_videofile(tmp.name,
                       codec="libx264",
                       audio_codec="aac",
                       ffmpeg_params=["-movflags", "+faststart", "-crf", "18", "-preset", "fast"],
                       logger=None,
                       threads=4)
    del clip
    gc.collect()
    return tmp.name

# --------------------------------------------------------
# UI  (with format picker)
# --------------------------------------------------------

st.title("📱 TrippleK Multi-Format Ad Generator")
st.caption("Base64 cache • Auto-wrap text • Auto-title font • 9:16 / 4:5 / 1:1")

with st.sidebar:
    st.subheader("✏️ Text & Sizes")
    product = st.text_input("Phone Name", "iPhone 16e")
    specs   = st.text_area("Specs (1 per line)",
                          "A18 Bionic Chip\n48 MP Camera\n256 GB Storage\n20 % Off",
                          height=120)
    price   = st.text_input("Price text", "KSh 145,000")

    st.subheader("🎚️ Layout Sliders")
    # logo
    logo_w  = st.slider("Logo width",  200, 1200, 420, 10)
    logo_h  = st.slider("Logo height", 60,  400, 100, 10)
    logo_x  = st.slider("Logo X", 0, 600, 60, 10)
    logo_y  = st.slider("Logo Y", 0, 600, 60, 10)
    # headline
    head_size = st.slider("Headline font size", 20, 200, 90, 2)
    head_x    = st.slider("Headline X offset", -400, 400, 0, 10)
    head_y    = st.slider("Headline Y", 0, 600, 220, 10)
    # product
    prod_w = st.slider("Product width",  300, 1500, 650, 10)
    prod_h = st.slider("Product height", 400, 1600, 900, 10)
    prod_x = st.slider("Product X offset", -400, 400, 0, 10)
    prod_y = st.slider("Product Y", 0, 1000, 450, 10)
    # specs
    spec_size = st.slider("Spec font size", 14, 120, 42, 2)
    spec_x    = st.slider("Spec X", 0, 1200, 750, 10)
    spec_y_off= st.slider("Spec Y offset from middle", -400, 400, 0, 10)
    spec_gap  = st.slider("Spec line gap", 30, 250, 90, 10)
    # price
    price_w = st.slider("Price tag width",  150, 800, 300, 10)
    price_h = st.slider("Price tag height", 40, 300, 90, 10)
    price_x = st.slider("Price X offset", -400, 400, 0, 10)
    price_y = st.slider("Price Y", HEIGHT-600, HEIGHT-50, HEIGHT-210, 10)
    price_font = st.slider("Price font size", 14, 150, 48, 2)
    # cta
    cta_w  = st.slider("CTA width",  150, 900, 350, 10)
    cta_h  = st.slider("CTA height", 30, 300, 80, 10)
    cta_x  = st.slider("CTA X", 0, 800, 60, 10)
    cta_y  = st.slider("CTA Y", HEIGHT-500, HEIGHT-50, HEIGHT-180, 10)
    cta_font = st.slider("CTA font size", 14, 150, 46, 2)

    # format picker
    format_choice = st.selectbox("📱 Export Format", list(FORMAT_SIZES.keys()), index=0)

    export = st.button("🚀 Generate Multi-Format MP4", type="primary", use_container_width=True)

# Pack UI dict
ui_pack = {
    "logo_size": (logo_w, logo_h),
    "logo_xy": (logo_x, logo_y),
    "product_size": (prod_w, prod_h),
    "product_xy": (prod_x, prod_y),
    "headline_size": head_size,
    "headline_xy": (head_x, head_y),
    "spec_size": (320, spec_size),
    "spec_xy": (spec_x, HEIGHT // 2 - 150 + spec_y_off),
    "spec_spacing": spec_gap,
    "price_size": (price_w, price_h),
    "price_xy": (price_x, price_y),
    "price_font": price_font,
    "cta_size": (cta_w, cta_h),
    "cta_xy": (cta_x, cta_y),
    "cta_font": cta_font
}

# Main column
if export:
    if not product.strip():
        st.error("Add a product name!")
        st.stop()
    with st.spinner("Rendering multi-format ad..."):
        path = build_video(product, specs, price, ui_pack, format_choice)
    st.success("✅ Multi-format ad ready!")
    with open(path, "rb") as f:
        st.download_button("⬇️ Download MP4", f, file_name=f"TrippleK_{format_choice.replace(' ', '_')}.mp4", use_container_width=True)
    st.video(path)
    try:
        os.remove(path)
    except:
        pass
    gc.collect()
else:
    preview = np.asarray(draw_frame(1.0, product, specs, price, **ui_pack, fmt=format_choice))
    st.image(preview, use_column_width=True)
