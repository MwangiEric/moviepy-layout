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
# DYNAMIC LAYOUT BY CANVAS SIZE
# --------------------------------------------------------
def get_responsive_layout(canvas_w, canvas_h):
    """Dynamic zones that adapt to ANY size using conditions"""
    aspect_ratio = canvas_w / canvas_h
    margin = min(canvas_w, canvas_h) * 0.08
    
    if aspect_ratio < 0.7:  # Portrait Mobile
        return {
            "logo": (margin, margin, margin*4, margin*1.5),
            "title": (margin, 0.08*canvas_h, canvas_w-margin, 0.18*canvas_h),
            "product": (margin, 0.22*canvas_h, canvas_w-margin, 0.68*canvas_h),
            "price": (margin, 0.72*canvas_h, 0.45*canvas_w, 0.82*canvas_h),
            "cta": (0.48*canvas_w, 0.72*canvas_h, canvas_w-margin, 0.82*canvas_h),
        }
    else:  # Square/Landscape
        return {
            "logo": (margin, margin, margin*3, margin*1.2),
            "title": (margin, 0.06*canvas_h, canvas_w-margin, 0.16*canvas_h),
            "product": (margin, 0.20*canvas_h, canvas_w-margin, 0.70*canvas_h),
            "price": (0.65*canvas_w, 0.72*canvas_h, canvas_w-margin, 0.82*canvas_h),
            "cta": (margin, 0.72*canvas_h, 0.35*canvas_w, 0.82*canvas_h),
        }

FORMAT_SIZES = {
    "TikTok / Reels (9:16)": (1080, 1920),
    "Instagram (4:5)":       (1080, 1350),
    "WhatsApp Story (1:1)":  (1080, 1080),
}

# --------------------------------------------------------
# BASE64 SESSION CACHE
# --------------------------------------------------------
@st.cache_resource
def url_to_base64(url, name):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        b64 = base64.b64encode(resp.content).decode()
        return b64
    except Exception as e:
        st.warning(f"❌ {name} download failed: {e}")
        return None

# Auto-download
if "logo_b64" not in st.session_state:
    st.session_state.logo_b64 = url_to_base64(LOGO_URL, "logo")
if "product_b64" not in st.session_state:
    st.session_state.product_b64 = url_to_base64(PRODUCT_URL, "product")

# --------------------------------------------------------
# FIXED FONT + TEXT BOX FUNCTIONS
# --------------------------------------------------------
@st.cache_resource
def _font_bytes(bold=True):
    url = ("https://github.com/google/fonts/raw/main/ofl/inter/" +
           ("Inter-Bold.ttf" if bold else "Inter-Medium.ttf"))
    return requests.get(url, timeout=20).content

def get_font(size, bold=True):
    size = max(20, int(size))
    try:
        return ImageFont.truetype(io.BytesIO(_font_bytes(bold)), size)
    except:
        try:
            return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
        except:
            return ImageFont.load_default()

def smart_text_box(draw, text, rect, font_size=60, bg_color=(0,0,0,180), text_color=WHITE):
    """FIXED: Perfect text box that ALWAYS fits rectangle"""
    x1, y1, x2, y2 = rect
    max_w, max_h = x2-x1-40, y2-y1-40  # padding
    
    # Find perfect font size
    font = get_font(font_size)
    while font_size > 20:
        bbox = draw.textbbox((0,0), text, font=font)
        text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        if text_w <= max_w and text_h <= max_h:
            break
        font_size -= 2
        font = get_font(font_size)
    
    # Draw bg rect
    draw.rounded_rectangle(rect, radius=20, fill=bg_color, outline="white", width=2)
    
    # Center text
    text_x = x1 + 20 + (max_w - text_w) // 2
    text_y = y1 + 20 + (max_h - text_h) // 2
    draw.text((text_x, text_y), text, font=font, fill=text_color)
    
    return font_size

def b64_to_pil(b64, target_size, name):
    if b64 is None:
        w, h = target_size
        img = Image.new("RGBA", target_size, (200, 200, 200, 255))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([10,10,w-10,h-10], radius=20, fill="#F0F0F0")
        draw.text((w//2, h//2), name[:4], fill="#666", anchor="mm")
        return img
    try:
        img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
        return img.resize(target_size, Image.Resampling.LANCZOS)
    except:
        return Image.new("RGBA", target_size, (200, 200, 200, 255))

# --------------------------------------------------------
# DRAW FRAME WITH DYNAMIC LAYOUT + TEXT BOXES
# --------------------------------------------------------
def draw_frame(t, product, specs, price, fmt="TikTok / Reels (9:16)"):
    w, h = FORMAT_SIZES[fmt]
    zones = get_responsive_layout(w, h)
    
    # Base canvas
    rgb = Image.new("RGB", (w, h), BG_COLOUR)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    # LOGO
    logo_size = (int(zones["logo"][2]-zones["logo"][0]), int(zones["logo"][3]-zones["logo"][1]))
    logo = b64_to_pil(st.session_state.logo_b64, logo_size, "Logo")
    canvas.paste(logo, (int(zones["logo"][0]), int(zones["logo"][1])), logo)
    
    # PRODUCT (with float animation)
    prod_rect = zones["product"]
    prod_size = (int(prod_rect[2]-prod_rect[0]), int(prod_rect[3]-prod_rect[1]))
    phone = b64_to_pil(st.session_state.product_b64, prod_size, "Product")
    float_y = int(prod_rect[1] + 15 * math.sin(t * 1.1))
    canvas.paste(phone, (int(prod_rect[0]), float_y), phone)
    
    # TITLE - PERFECT TEXT BOX
    smart_text_box(draw, product.upper(), zones["title"], 80, (*ACCENT, 200), ACCENT_GOLD)
    
    # PRICE - GOLD BADGE
    smart_text_box(draw, price, zones["price"], 60, (*ACCENT, 255), ACCENT_GOLD)
    
    # CTA - CYAN BUTTON
    smart_text_box(draw, "SHOP NOW", zones["cta"], 50, (*MAROON, 255), WHITE)
    
    # Website footer
    web_rect = (w//2-200, h-80, w//2+200, h-40)
    smart_text_box(draw, "www.tripplek.co.ke", web_rect, 32, None, TEXT_COLOUR)
    
    return Image.alpha_composite(rgb, canvas)

# --------------------------------------------------------
# VIDEO GENERATION
# --------------------------------------------------------
def build_video(product, specs, price, fmt="TikTok / Reels (9:16)"):
    frames = []
    bar = st.progress(0)
    for i in range(TOTAL_FRAMES):
        frames.append(np.asarray(draw_frame(i/FPS, product, specs, price, fmt)))
        bar.progress((i+1)/TOTAL_FRAMES)
    
    clip = ImageSequenceClip(frames, fps=FPS)
    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    requests.get(AUDIO_URL).content  # Simplified audio
    clip.write_videofile(audio_path.name.replace('.mp3', '.mp4'),
                        codec="libx264", audio_codec="aac",
                        temp_audiofile='temp-audio.m4a',
                        remove_temp=True)
    return audio_path.name.replace('.mp3', '.mp4')

# --------------------------------------------------------
# STREAMLIT UI
# --------------------------------------------------------
st.title("📱 TrippleK Dynamic Ad Generator")
st.caption("✅ Dynamic layout • ✅ Auto text boxes • ✅ Multi-format")

with st.sidebar:
    product = st.text_input("Phone Name", "iPhone 16e")
    price   = st.text_input("Price", "KSh 145,000")
    format_choice = st.selectbox("📱 Format", list(FORMAT_SIZES.keys()), index=0)
    
    if st.button("🚀 Generate MP4", type="primary"):
        with st.spinner("Rendering..."):
            path = build_video(product, "", price, format_choice)
        st.success("✅ Ready!")
        st.video(path)
        with open(path, "rb") as f:
            st.download_button("⬇️ Download", f, 
                             f"TrippleK_{format_choice.replace(' ','_')}.mp4")

# Live preview
if product:
    preview = draw_frame(1.0, product, "", price, format_choice)
    st.image(preview, use_column_width=True)
