import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import tempfile
import os
import math
import requests
import gc
import time
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip

# --------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------
WIDTH, HEIGHT = 1080, 1920
FPS = 30
DURATION = 6
TEXT_MAX_Y = 1300

BG_DARK = "#0F0F12"
ACCENT_COLOR = "#00F0FF"
TEXT_WHITE = "#FFFFFF"

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037".strip()
AUDIO_URL = "https://ik.imagekit.io/ericmwangi/ambient-piano-112970.mp3?updatedAt=1764101548797".strip()
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf".strip()
VIDEO_BG_URL = "https://ik.imagekit.io/ericmwangi/oceanbg.mp4"

MODERN_TEMPLATES = ["Glass Morphism", "Neon Pulse", "Minimal Zen"]
ALL_TEMPLATES = MODERN_TEMPLATES + ["Golden Waves", "Modern Grid"]
TEXT_ANIMATIONS = ["Auto", "Typewriter", "Fade-In", "Highlight", "Neon Pulse"]

# --------------------------------------------------------
# CACHED ASSET LOADERS
# --------------------------------------------------------
@st.cache_resource
def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

@st.cache_resource
def load_font():
    try:
        resp = requests.get(FONT_URL, timeout=10)
        if resp.status_code == 200:
            return io.BytesIO(resp.content)
    except:
        pass
    return None

def get_font(size):
    font_io = load_font()
    if font_io:
        try:
            return ImageFont.truetype(font_io, size)
        except:
            pass
    return ImageFont.load_default()

@st.cache_resource
def load_logo():
    try:
        resp = requests.get(LOGO_URL, timeout=10)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            ratio = min(280 / logo.width, 140 / logo.height)
            new_size = (int(logo.width * ratio), int(logo.height * ratio))
            return logo.resize(new_size, Image.LANCZOS)
    except:
        pass
    fallback = Image.new("RGBA", (280, 140), (0,0,0,0))
    draw = ImageDraw.Draw(fallback)
    draw.text((20, 25), "SM", fill=ACCENT_COLOR, font=get_font(80))
    return fallback

@st.cache_data
def download_audio():
    try:
        r = requests.get(AUDIO_URL, timeout=15)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except:
        pass
    return None

@st.cache_data
def download_video_bg():
    try:
        r = requests.get(VIDEO_BG_URL, timeout=20)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception as e:
        st.warning(f"Ocean background load failed: {e}")
    return None

# --------------------------------------------------------
# TEXT & LAYOUT UTILITIES
# --------------------------------------------------------
def split_lines(text, font, max_width):
    words = text.split()
    if not words:
        return [""]
    lines, current = [], []
    for word in words:
        test = ' '.join(current + [word])
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines

def fit_font_adaptive(quote, max_width=WIDTH - 200, max_lines=4):
    if not quote.strip():
        return get_font(60)
    words = quote.split()
    est_lines = max(1, min(max_lines, (len(words) + 5) // 6))
    for size in range(82, 38, -2):
        font = get_font(size)
        lines = split_lines(quote, font, max_width)
        if len(lines) <= max_lines:
            too_wide = any((font.getbbox(line)[2] - font.getbbox(line)[0]) > max_width for line in lines)
            if not too_wide:
                return font
    return get_font(40)

# --------------------------------------------------------
# BACKGROUND & RENDERING
# --------------------------------------------------------
def create_background(template_name, t=0.0):
    base = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(base, "RGBA")
    if template_name == "Glass Morphism":
        cx, cy = WIDTH // 2, HEIGHT // 2
        for i in range(4):
            angle = t * 0.6 + i
            x = cx + int(250 * math.cos(angle))
            y = cy + int(180 * math.sin(angle * 0.8))
            r = 160 + 30 * math.sin(t + i)
            alpha = int(25 + 20 * math.sin(t * 1.2 + i))
            draw.ellipse([x - r, y - r, x + r, y + r], fill=ACCENT_COLOR + f"{alpha:02x}")
    elif template_name == "Neon Pulse":
        for i in range(5):
            r = 120 + i * 160 + 25 * math.sin(t * 0.9 + i)
            alpha = int(35 + 30 * abs(math.sin(t * 1.6 + i)))
            draw.ellipse([WIDTH//2 - r, HEIGHT//2 - r, WIDTH//2 + r, HEIGHT//2 + r],
                         outline=ACCENT_COLOR + f"{alpha:02x}", width=2)
        for i in range(15):
            x = int(WIDTH * (0.25 + 0.5 * math.sin(t * 0.5 + i)))
            y = int(HEIGHT * (0.2 + 0.6 * math.cos(t * 0.4 + i)))
            s = 3 + 2 * math.sin(t * 0.7 + i)
            a = int(120 + 100 * math.sin(t * 1.1 + i))
            draw.ellipse([x - s, y - s, x + s, y + s], fill=ACCENT_COLOR + f"{max(0, min(255, a)):02x}")
    elif template_name == "Minimal Zen":
        draw.line([(WIDTH//2 - 350, HEIGHT//2), (WIDTH//2 + 350, HEIGHT//2)], fill=ACCENT_COLOR + "15", width=2)
        off = 25 * math.sin(t * 0.8)
        draw.arc([WIDTH//2 - 280, HEIGHT//2 - 90 + off, WIDTH//2 + 280, HEIGHT//2 + 90 + off],
                 0, 180, fill=ACCENT_COLOR + "50", width=3)
    else:
        for x in range(0, WIDTH, 180):
            draw.line([(x, 0), (x, HEIGHT)], fill=ACCENT_COLOR + "08", width=1)
        for y in range(0, HEIGHT, 180):
            draw.line([(0, y), (WIDTH, y)], fill=ACCENT_COLOR + "08", width=1)
    return np.array(base)

def draw_text_overlay(overlay, lines, author, t, anim_type, font_quote, font_author):
    draw = ImageDraw.Draw(overlay)
    y0, line_h = 480, 110
    anim = {"Auto": "highlight"}.get(anim_type, anim_type.lower().replace(" ", "-"))
    if anim == "typewriter":
        full = " ".join(lines)
        chars = min(len(full), int(t * 10))
        displayed = full[:chars]
        wrapped = split_lines(displayed, font_quote, WIDTH - 200)
        for i, line in enumerate(wrapped):
            draw.text((WIDTH//2, y0 + i * line_h), line, fill=TEXT_WHITE, font=font_quote, anchor="mm")
        if t > len(full) / 10 and int(t * 4) % 2:
            x = WIDTH//2 + (font_quote.getbbox(wrapped[-1] or "A")[2] // 2) + 10
            y = y0 + (len(wrapped) - 1) * line_h
            draw.line([(x, y - 40), (x, y + 40)], fill=ACCENT_COLOR, width=2)
    elif anim == "fade-in":
        for i, line in enumerate(lines):
            start = i * 0.6
            alpha = min(255, int(255 * max(0, t - start) * 2)) if t >= start else 0
            if alpha > 0:
                draw.text((WIDTH//2, y0 + i * line_h), line, fill=TEXT_WHITE + f"{alpha:02x}", font=font_quote, anchor="mm")
    elif anim == "neon-pulse":
        glow = ACCENT_COLOR + "60"
        for i, line in enumerate(lines):
            y = y0 + i * line_h
            for dx, dy in [(-2, -2), (2, 2), (-2, 2), (2, -2)]:
                draw.text((WIDTH//2 + dx, y + dy), line, fill=glow, font=font_quote, anchor="mm")
            pulse = 0.7 + 0.3 * math.sin(t * 4 + i)
            alpha = int(255 * pulse)
            draw.text((WIDTH//2, y), line, fill=TEXT_WHITE + f"{alpha:02x}", font=font_quote, anchor="mm")
    else:  # highlight
        for i, line in enumerate(lines):
            y = y0 + i * line_h
            words = line.split()
            for j, word in enumerate(words):
                word_t = i * 0.8 + j * 0.2
                if word_t <= t < word_t + 0.2:
                    prefix = " ".join(words[:j])
                    px = font_quote.getbbox(prefix + " ")[2] if prefix else 0
                    lx = font_quote.getbbox(line)[2]
                    x0 = WIDTH//2 - lx//2 + px
                    wb = font_quote.getbbox(word)
                    draw.rectangle([x0 - 6, y + wb[1] - 6, x0 + wb[2] - wb[0] + 6, y + wb[3] + 6],
                                   fill=ACCENT_COLOR + "35")
                    break
            draw.text((WIDTH//2, y), line, fill=TEXT_WHITE, font=font_quote, anchor="mm")
    if author and (t > 1.2 or anim != "typewriter"):
        draw.text((WIDTH//2, y0 + len(lines) * line_h + 50), author, fill=ACCENT_COLOR, font=font_author, anchor="mm")
    draw.text((WIDTH//2, HEIGHT - 180), "Save this wisdom ✨", fill=ACCENT_COLOR, font=get_font(50), anchor="mm")

def render_frame(t, lines, author, logo, font_q, font_a, template, anim, bg_array=None):
    if bg_array is None:
        bg_array = create_background(template, t)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    if logo:
        overlay.paste(logo, (70, 60), logo)
    draw_text_overlay(overlay, lines, author, t, anim, font_q, font_a)
    fg = np.array(overlay)[:, :, :3]
    alpha = np.array(overlay)[:, :, 3:] / 255.0
    return (bg_array * (1 - alpha) + fg * alpha).astype(np.uint8)

def get_video_frame(clip, t):
    if t >= clip.duration:
        t = clip.duration - 0.01
    frame = clip.get_frame(t)
    img = Image.fromarray(frame).convert("RGB")
    w, h = img.size
    if w / h > WIDTH / HEIGHT:
        new_w = int(h * WIDTH / HEIGHT)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w * HEIGHT / WIDTH)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    return np.array(img.resize((WIDTH, HEIGHT), Image.LANCZOS))

def render_preview_frame(quote, author, template, anim):
    logo = load_logo()
    font_q = fit_font_adaptive(quote)
    font_a = get_font(52)
    lines = split_lines(quote, font_q, WIDTH - 200)
    t = 1.5
    if anim == "Typewriter":
        t = min(2.5, max(1.0, len(quote) / 8))
    elif anim == "Neon Pulse":
        t = 0.8
    return render_frame(t, lines, author, logo, font_q, font_a, template, anim)

# --------------------------------------------------------
# STREAMLIT APP
# --------------------------------------------------------
st.set_page_config(page_title="Ocean Quote Reels", layout="wide", page_icon="🌊")
st.title("🌊 Ocean Quote Reels")
st.caption("Enter your quote → See live preview → Export 6-second video")

col1, col2 = st.columns(2)
with col1:
    quote = st.text_area("Your Quote", "The ocean stirs the soul and fuels the imagination.", height=120, max_chars=200)
with col2:
    author = st.text_input("Author", "— Anonymous", max_chars=50)

col3, col4 = st.columns(2)
with col3:
    template = st.selectbox("🎨 Background Style", ALL_TEMPLATES)
with col4:
    anim = st.selectbox("🔤 Text Animation", TEXT_ANIMATIONS)

use_ocean_bg = st.checkbox("🌊 Use ocean video background", value=True)

# LIVE PREVIEW
st.markdown("### 👁️ Live Preview")
try:
    preview_img = render_preview_frame(quote, author, template, anim)
    st.image(preview_img, width=320, caption="Preview at optimal time")
except Exception as e:
    st.error("Preview unavailable. Check inputs.")

# EXPORT BUTTON
if st.button("🚀 Export 6-Second Video", type="primary", use_container_width=True):
    if not quote.strip():
        st.error("Please enter a quote.")
    else:
        with st.spinner("Rendering your 6-second video... (30–50 sec)"):
            logo = load_logo()
            font_q = fit_font_adaptive(quote)
            font_a = get_font(52)
            lines = split_lines(quote, font_q, WIDTH - 200)

            video_clip = None
            if use_ocean_bg:
                vid_path = download_video_bg()
                if vid_path:
                    try:
                        video_clip = VideoFileClip(vid_path)
                        if video_clip.duration < DURATION:
                            video_clip = video_clip.loop(duration=DURATION)
                        else:
                            video_clip = video_clip.subclip(0, DURATION)
                    except Exception as e:
                        st.warning("Using animated background instead of video.")

            frames = []
            total_frames = FPS * DURATION
            for i in range(total_frames):
                t = i / FPS
                if video_clip is not None:
                    bg = get_video_frame(video_clip, t)
                    frame = render_frame(t, lines, author, logo, font_q, font_a, template, anim, bg_array=bg)
                else:
                    frame = render_frame(t, lines, author, logo, font_q, font_a, template, anim)
                frames.append(frame)

            out_path = os.path.join(tempfile.gettempdir(), f"quote_{int(time.time())}.mp4")
            audio = download_audio()
            clip = ImageSequenceClip(frames, fps=FPS)
            if audio:
                try:
                    aclip = AudioFileClip(audio).subclip(0, clip.duration)
                    clip = clip.set_audio(aclip)
                except:
                    pass
            clip.write_videofile(out_path, codec="libx264", audio_codec="aac", logger=None, threads=4)

            st.success("✅ Your 6-second video is ready!")
            with open(out_path, "rb") as f:
                st.download_button("⬇️ Download Video", f, "Ocean_Quote.mp4", "video/mp4", use_container_width=True)
            st.video(out_path)

            clip.close()
            if video_clip:
                video_clip.close()
            del frames
            gc.collect()
