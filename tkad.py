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
# ADDED ACCENT_GOLD since it was used but not defined
ACCENT_GOLD = (255, 191, 0) # Placeholder for a gold-like color

# Initialize export status before it's potentially defined in the sidebar, 
# ensuring the main 'if export:' block doesn't throw a NameError on first run.
export = False

# Remote assets
LOGO_URL    = "https://www.tripplek.co.ke/wp-content/uploads/2024/10/Tripple-K-Com-Logo-255-by-77.png"
PRODUCT_URL = "https://www.tripplek.co.ke/wp-content/uploads/2025/02/iphone-16e-33.png"
AUDIO_URL   = "https://ik.imagekit.io/ericmwangi/tech-ambient.mp3?updatedAt=1764372632499"

# --------------------------------------------------------
# BASE64 SESSION CACHE  (download once, reuse forever)
# --------------------------------------------------------
@st.cache_data(show_spinner=False)
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


def b64_to_pil(b64, target_size, name):
    if b64 is None:
        return _fallback_image(target_size, name)
    try:
        raw = base64.b64decode(b64)
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        return img.resize(target_size, Image.Resampling.LANCZOS)
    except Exception:
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
# FONT HELPERS
# --------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _font_bytes(bold=True):
    url = ("https://github.com/google/fonts/raw/main/ofl/inter/" +
           ("Inter-Bold.ttf" if bold else "Inter-Medium.ttf"))
    return requests.get(url, timeout=20).content


def get_font(size, bold=True):
    size = max(12, int(size))
    try:
        return ImageFont.truetype(io.BytesIO(_font_bytes(bold)), size)
    except Exception:
        try:
            return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
        except:
            return ImageFont.load_default()

# --------------------------------------------------------
# CPU FILTERS  (choose one)
# --------------------------------------------------------
def cpu_filters(frame):
    """Zero overhead"""
    return np.asarray(frame)

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
# ANIMATED BACKGROUND
# --------------------------------------------------------
def animated_bg(t):
    base = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOUR)
    draw = ImageDraw.Draw(base, "RGBA")

    # floating maroon circles (back)
    for i in range(5):
        x = int(WIDTH / 2 + 400 * math.sin(t * 0.2 + i * 1.3))
        y = int(HEIGHT / 2 + 400 * math.cos(t * 0.15 + i * 1.1))
        r = 280 + 60 * math.sin(t * 0.3 + i)
        opacity = int(60 + 40 * math.sin(t * 0.4 + i))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*ACCENT, opacity))

    # lime rotated rectangles
    for i in range(6):
        w = 200 + 50 * math.sin(t * 0.7 + i)
        h = 200 + 50 * math.cos(t * 0.5 + i)
        cx = WIDTH / 2 + 350 * math.sin(t * 0.6 + i)
        cy = HEIGHT / 2 + 350 * math.cos(t * 0.5 + i)
        angle = math.degrees(t * 0.4 + i * 60)
        # FIX 1: Add the drawing logic that was missing in your original snippet
        # This drawing logic appears to be part of the animated_bg, or was a typo for draw_frame.
        # Given the existing structure, I will move the previous drawing logic into draw_frame,
        # but the animated_bg function needs a return for 'rgb' to be defined in draw_frame.
        
        # NOTE: Your polygon drawing logic relies on cx, cy, w, h, and angle defined here. 
        # Since draw_frame needs to use these, animated_bg must return the image object
        # and draw_frame must re-draw or composite on top.
        
    return base # FIX 1: The function must return the image object
# --------------------------------------------------------
# TEXT BOX  (auto-wrap + auto-scale + line-height)
# --------------------------------------------------------
def text_box(text, box_size, colour, bold=True, line_spacing=1.15):
    w, h = box_size
    words = text.split()
    size = h // 2                         # start big
    while size > 10:                      # safeguard
        font = get_font(size, bold)
        line_h = (font.getbbox("Ay")[3] - font.getbbox("Ay")[1]) * line_spacing
        # wrap words
        lines, cur_line = [], ""
        for wd in words:
            test = cur_line + (" " if cur_line else "") + wd
            tw = font.getbbox(test)[2]
            if tw <= w:
                cur_line = test
            else:
                lines.append(cur_line)
                cur_line = wd
        if cur_line:
            lines.append(cur_line)
        total_h = int(len(lines) * line_h)
        if total_h <= h:
            break
        size -= 2

    # render
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = (h - total_h) // 2
    for line in lines:
        tw = font.getbbox(line)[2]
        draw.text(((w - tw) // 2, y), line, font=font, fill=colour)
        y += int(line_h)
    return img
# --------------------------------------------------------
# DRAW FRAME  (uses real slider variables)
# --------------------------------------------------------
def draw_frame(t, product, specs, price,
               logo_size, logo_xy, product_size, product_xy,
               headline_size, headline_xy, spec_size, spec_xy, spec_spacing,
               price_size, price_xy, price_font,
               cta_size, cta_xy, cta_font):
    base_pil = animated_bg(t) # base_pil is now a PIL Image from animated_bg
    base = base_pil.convert("RGBA") # Renamed 'base' to 'base_pil' in line above, keeping 'base' as RGBA
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas) # Initialize draw for the canvas

    # logo (base64)
    logo = b64_to_pil(st.session_state.get("logo_b64"), logo_size, "Logo")
    canvas.paste(logo, logo_xy, logo)

    # product (base64)
    phone = b64_to_pil(st.session_state.get("product_b64"), product_size, "Product")
    float_y = int(product_xy[1] + 40 * ease_out_elastic((t*0.8) % 1))
    prod_x = (WIDTH - product_size[0]) // 2 + product_xy[0]
    canvas.paste(phone, (prod_x, float_y), phone)

    # headline (fills box + spring)
    head_img = text_box(product.upper(), (headline_size*10, headline_size), ACCENT_GOLD)
    spring_x = int(40 * ease_out_elastic((t*0.6) % 1))
    head_x = (WIDTH - head_img.width) // 2 + headline_xy[0] + spring_x
    canvas.paste(head_img, (head_x, headline_xy[1]), head_img)

    # specs (fills card)
    font_spec = get_font(spec_size[1])
    spec_lines = specs.split("\n")[:4]
    start_y = HEIGHT // 2 - 150
    for i, txt in enumerate(spec_lines):
        alpha = int(255 * min(1, max(0, (t - 0.5 - i * 0.2) * 2)))
        if alpha <= 0: continue
        y = start_y + i * spec_spacing
        card = Image.new("RGBA", (320, 70), (*WHITE, alpha // 2))
        canvas.paste(card, (spec_xy[0] - 20, y - 10), card)
        txt_img = text_box(txt, (280, 60), (*TEXT_COLOUR, alpha))
        canvas.paste(txt_img, (spec_xy[0], y), txt_img)

    # price (fills tag)
    pulse = 1 + 0.05 * math.sin(t * 3)
    pw, ph = int(price_size[0] * pulse), int(price_size[1] * pulse)
    px = (WIDTH - pw) // 2 + price_xy[0]
    py = price_xy[1] + (price_size[1] - ph) // 2
    # draw is already defined for canvas
    draw.rounded_rectangle((px, py, px + pw, py + ph), radius=25, fill=ACCENT_GOLD)
    price_img = text_box(price, (pw, ph), WHITE)
    canvas.paste(price_img,
                 (px + (pw - price_img.width) // 2,
                  py + (ph - price_img.height) // 2),
                 price_img)

    # cta (fills button)
    cta_img = text_box("SHOP NOW", (cta_size[0], cta_size[1]), WHITE)
    canvas.paste(cta_img,
                 (cta_xy[0] + (cta_size[0] - cta_img.width) // 2,
                  cta_xy[1] + (cta_size[1] - cta_img.height) // 2),
                 cta_img)

    # website
    web_img = text_box("www.tripplek.co.ke", (WIDTH, 40), TEXT_COLOUR)
    canvas.paste(web_img,
                 ((WIDTH - web_img.width) // 2, HEIGHT - 50),
                 web_img)

    # --- FIX 2: MOVE DRAWING LOGIC HERE ---
    
    # You need to define cx, cy, w, h, angle for the preview (t=1.0)
    # Reusing the background calculations and assuming it's for the preview
    # NOTE: 'i' is only defined inside the loop, using i=0 for a single preview
    cx = WIDTH / 2 + 350 * math.sin(1.0 * 0.6 + 0)
    cy = HEIGHT / 2 + 350 * math.cos(1.0 * 0.5 + 0)
    w = 200 + 50 * math.sin(1.0 * 0.7 + 0)
    h = 200 + 50 * math.cos(1.0 * 0.5 + 0)
    angle = math.degrees(1.0 * 0.4 + 0)
    i = 0 # Placeholder for 'i' used outside its intended loop

    # Use a new draw object for compositing the canvas onto the background
    final_draw = ImageDraw.Draw(base)

    coords = []
    for k in range(4):
        θ = math.radians(angle + k * 90)
        coords.append((cx + w / 2 * math.cos(θ), cy + h / 2 * math.sin(θ)))
        opacity = int(80 + 50 * math.sin(t * 0.8 + i))
        final_draw.polygon(coords, fill=(*LIME_GREEN, opacity))

    # white glints (front)
    for i in range(20):
        # Glints logic (needs WIDTH, HEIGHT, WHITE)
        x = int(WIDTH * (0.05 + 0.9 * (math.sin(t * 2.1 + i * 2.3) + 1) / 2))
        y = int(HEIGHT * (0.05 + 0.9 * (math.cos(t * 2.3 + i * 1.9) + 1) / 2))
        s = 6 + 4 * math.sin(t * 3 + i)
        opacity = int(200 + 55 * math.sin(t * 4 + i))
        final_draw.ellipse([x - s, y - s, x + s, y + s], fill=(*WHITE, opacity))
    
    # Composite the main canvas onto the background
    base.paste(canvas, (0, 0), canvas)
    
    # optional filter
    np_final = np.asarray(base)
    np_final = cpu_filters(np_final)    # 0 % overhead
    # np_final = minimal_vignette(np_final)    # 5 % overhead
    return np_final # FIX 3: The final return of the array is here.
# --------------------------------------------------------
# SINGLE-PASS ENCODER  (cloud-safe)
# --------------------------------------------------------
# ... (build_video remains the same) ...

# --------------------------------------------------------
# UI  (DOUBLE-RANGE SLIDERS)
# --------------------------------------------------------
# ... (UI and ui_pack remains the same) ...

# --------------------------------------------------------
# SESSION-INIT  (download once, base64)
# --------------------------------------------------------
if "logo_b64" not in st.session_state:
    url_to_base64(LOGO_URL, "logo_b64")
if "product_b64" not in st.session_state:
    url_to_base64(PRODUCT_URL, "product_b64")

# Main column
if export:
    if not product.strip():
        st.error("Add a product name!")
        st.stop()
    with st.spinner("Rendering premium ad..."):
        path = build_video(product, specs, price, ui_pack)
    st.success("✅ Premium ad ready!")
    with open(path, "rb") as f:
        st.download_button("⬇️ Download MP4", f, file_name="TrippleK_Premium.mp4", use_container_width=True)
    st.video(path)
    try:
        os.remove(path)
    except:
        pass
    gc.collect()
else:
    # FIX 3: Removed all drawing logic from here. It is now inside draw_frame.
    preview = draw_frame(1.0, product, specs, price, **ui_pack)
    st.image(preview, use_column_width=True)
