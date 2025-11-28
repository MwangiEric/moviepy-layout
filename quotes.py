import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import tempfile
import os
import math
import requests
import json
import re
import gc
import time
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip
import groq

# --------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------
WIDTH, HEIGHT = 1080, 1920
FPS = 30
TEXT_MAX_Y = 1400

BG_DARK = "#0F0F12"
ACCENT_COLOR = "#00F0FF"  # Neon cyan for modern look
TEXT_WHITE = "#FFFFFF"

LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037".strip()
AUDIO_URL = "https://ik.imagekit.io/ericmwangi/ambient-piano-112970.mp3?updatedAt=1764101548797".strip()
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf".strip()  # Modern sans-serif

MODERN_TEMPLATES = ["Glass Morphism", "Neon Pulse", "Minimal Zen"]
ALL_TEMPLATES = MODERN_TEMPLATES + [
    "Hexagon Grid", "Golden Waves", "Metallic Curves", "Modern Grid", "Low-Poly"
]

TEXT_ANIMATIONS = ["Auto", "Typewriter", "Fade-In", "Highlight", "Neon Pulse"]

# Animation mapping
ANIMATION_MAP = {
    "Glass Morphism": "fade-in",
    "Neon Pulse": "neon-pulse",
    "Minimal Zen": "highlight",
    "Golden Waves": "smooth-reveal",
    "Modern Grid": "highlight"
}

# --------------------------------------------------------
# UTILITY FUNCTIONS
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
    except Exception:
        pass
    return None

def get_font(size):
    font_io = load_font()
    if font_io:
        try:
            return ImageFont.truetype(font_io, size)
        except Exception:
            pass
    return ImageFont.load_default()

@st.cache_resource
def get_groq_client():
    if 'groq_key' not in st.secrets:
        st.error("❌ Add 'groq_key' to Streamlit Secrets")
        return None
    return groq.Client(api_key=st.secrets['groq_key'])

@st.cache_resource
def load_logo():
    try:
        resp = requests.get(LOGO_URL, timeout=10)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            ratio = min(280 / logo.width, 140 / logo.height)
            new_size = (int(logo.width * ratio), int(logo.height * ratio))
            return logo.resize(new_size, Image.LANCZOS)
    except Exception:
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
    except Exception:
        pass
    return None

# --------------------------------------------------------
# AI QUOTE GENERATION
# --------------------------------------------------------
def generate_quote(client, topic):
    prompt = f"""
    Generate a short, modern, and inspiring quote about {topic}.
    Requirements:
    - Quote: 10–25 words, concise and impactful
    - Author: Real or plausible name (e.g., "— R. Nakamura")
    - Caption: <70 chars with 1 emoji
    - Hashtags: 6 relevant tags
    Respond ONLY with valid JSON:
    {{
        "quote": "Clarity emerges not in noise, but in stillness.",
        "author": "— Lena Aris",
        "caption": "Find your quiet. 🧘",
        "hashtags": "#Mindfulness #Clarity #Stillness"
    }}
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.85,
            max_tokens=250
        )
        resp_text = chat_completion.choices[0].message.content
        json_match = re.search(r'\{.*\}', resp_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            tags = re.findall(r'#\w+', data.get("hashtags", ""))
            data["hashtags"] = " ".join(tags[:6])
            return data
    except Exception as e:
        st.error(f"AI error: {str(e)}")
    return None

@st.cache_data
def get_ai_quote(topic: str):
    client = get_groq_client()
    if not client:
        return None
    return generate_quote(client, topic)

# --------------------------------------------------------
# MODERN BACKGROUND TEMPLATES
# --------------------------------------------------------
def create_background(template_name, t=0.0):
    base = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(base, "RGBA")

    if template_name == "Glass Morphism":
        # Frosted glass blobs
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        for i in range(5):
            angle = t * 0.5 + i * 1.2
            cx = center_x + int(300 * math.cos(angle))
            cy = center_y + int(200 * math.sin(angle * 0.7))
            radius = 180 + 40 * math.sin(t + i)
            alpha = int(20 + 15 * math.sin(t * 1.3 + i))
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                         fill=ACCENT_COLOR + f"{alpha:02x}")

    elif template_name == "Neon Pulse":
        # Radiating neon rings
        for i in range(6):
            radius = 100 + i * 180 + 30 * math.sin(t * 0.8 + i)
            alpha = int(30 + 25 * abs(math.sin(t * 1.5 + i)))
            draw.ellipse([WIDTH//2 - radius, HEIGHT//2 - radius,
                          WIDTH//2 + radius, HEIGHT//2 + radius],
                         outline=ACCENT_COLOR + f"{alpha:02x}", width=3)
        # Floating particles
        for i in range(20):
            x = int(WIDTH * (0.3 + 0.4 * math.sin(t * 0.4 + i)))
            y = int(HEIGHT * (0.2 + 0.6 * math.cos(t * 0.3 + i)))
            size = 4 + 3 * math.sin(t * 0.6 + i)
            alpha = int(100 + 100 * math.sin(t * 1.2 + i))
            draw.ellipse([x - size, y - size, x + size, y + size],
                         fill=ACCENT_COLOR + f"{max(0, min(255, alpha)):02x}")

    elif template_name == "Minimal Zen":
        # Single elegant curve
        draw.line([(WIDTH//2 - 400, HEIGHT//2), (WIDTH//2 + 400, HEIGHT//2)],
                  fill=ACCENT_COLOR + "10", width=2)
        offset = 20 * math.sin(t * 0.7)
        draw.arc([WIDTH//2 - 300, HEIGHT//2 - 100 + offset,
                  WIDTH//2 + 300, HEIGHT//2 + 100 + offset],
                 0, 180, fill=ACCENT_COLOR + "60", width=4)

    # Fallback to original templates if needed
    else:
        # Reuse your original create_background logic here for other templates
        # For brevity, we'll return a solid color
        pass

    return np.array(base)

# --------------------------------------------------------
# TEXT RENDERING
# --------------------------------------------------------
def split_lines(text, font, max_width):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = ' '.join(current + [word])
        if font.getbbox(test)[2] <= max_width:
            current.append(word)
        else:
            if current: lines.append(' '.join(current))
            current = [word]
    if current: lines.append(' '.join(current))
    return lines

def fit_font(text, max_width, max_size=80, min_size=40):
    for size in range(max_size, min_size - 1, -2):
        font = get_font(size)
        if font.getbbox(text)[2] <= max_width:
            return font
    return get_font(min_size)

def draw_text_overlay(overlay, lines, author, t, text_animation, font_quote, font_author):
    draw = ImageDraw.Draw(overlay)
    quote_y = 500
    line_h = 100

    # Resolve animation
    if text_animation == "Auto":
        anim = "highlight"  # default
    else:
        anim_map = {
            "Typewriter": "typewriter",
            "Fade-In": "fade-in",
            "Highlight": "highlight",
            "Neon Pulse": "neon-pulse"
        }
        anim = anim_map.get(text_animation, "highlight")

    if anim == "typewriter":
        full = " ".join(lines)
        chars = min(len(full), int(t * 10))
        displayed = full[:chars]
        wrapped = split_lines(displayed, font_quote, WIDTH - 200)
        for i, line in enumerate(wrapped):
            draw.text((WIDTH//2, quote_y + i*line_h), line, fill=TEXT_WHITE, font=font_quote, anchor="mm")
        if t > len(full) / 10 and int(t * 4) % 2:
            x = WIDTH//2 + (font_quote.getbbox(wrapped[-1] or "A")[2] // 2) + 10
            y = quote_y + (len(wrapped) - 1) * line_h
            draw.line([(x, y-40), (x, y+40)], fill=ACCENT_COLOR, width=2)

    elif anim == "fade-in":
        for i, line in enumerate(lines):
            start = i * 0.6
            alpha = 0 if t < start else min(255, int(255 * (t - start) * 2))
            if alpha > 0:
                color = TEXT_WHITE + f"{alpha:02x}"
                draw.text((WIDTH//2, quote_y + i*line_h), line, fill=color, font=font_quote, anchor="mm")

    elif anim == "neon-pulse":
        glow_color = ACCENT_COLOR + "60"
        for i, line in enumerate(lines):
            y = quote_y + i * line_h
            # Glow
            for dx, dy in [(-2,-2), (2,2), (-2,2), (2,-2)]:
                draw.text((WIDTH//2 + dx, y + dy), line, fill=glow_color, font=font_quote, anchor="mm")
            # Main text with pulse
            pulse = 0.7 + 0.3 * math.sin(t * 4 + i)
            alpha = int(255 * pulse)
            draw.text((WIDTH//2, y), line, fill=TEXT_WHITE + f"{alpha:02x}", font=font_quote, anchor="mm")

    else:  # highlight
        for i, line in enumerate(lines):
            y = quote_y + i * line_h
            words = line.split()
            for j, word in enumerate(words):
                word_t = i * 0.8 + j * 0.2
                if word_t <= t < word_t + 0.2:
                    prefix = " ".join(words[:j])
                    px = font_quote.getbbox(prefix + " ")[2] if prefix else 0
                    lx = font_quote.getbbox(line)[2]
                    x0 = WIDTH//2 - lx//2 + px
                    w_bbox = font_quote.getbbox(word)
                    draw.rectangle([x0-5, y+w_bbox[1]-5, x0+w_bbox[2]-w_bbox[0]+5, y+w_bbox[3]+5],
                                   fill=ACCENT_COLOR + "30")
                    break
            draw.text((WIDTH//2, y), line, fill=TEXT_WHITE, font=font_quote, anchor="mm")

    if author and (t > 1.0 or anim not in ["typewriter"]):
        draw.text((WIDTH//2, quote_y + len(lines)*line_h + 50), author,
                  fill=ACCENT_COLOR, font=font_author, anchor="mm")

    draw.text((WIDTH//2, HEIGHT - 180), "Save this wisdom ✨",
              fill=ACCENT_COLOR, font=get_font(50), anchor="mm")

# --------------------------------------------------------
# FRAME GENERATION
# --------------------------------------------------------
def render_frame(t, lines, author, logo, font_quote, font_author, template, text_animation, bg_array=None):
    if bg_array is None:
        bg_array = create_background(template, t)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    if logo:
        overlay.paste(logo, (70, 60), logo)
    draw_text_overlay(overlay, lines, author, t, text_animation, font_quote, font_author)
    
    fg = np.array(overlay)[:, :, :3]
    alpha = np.array(overlay)[:, :, 3:] / 255.0
    return (bg_array * (1 - alpha) + fg * alpha).astype(np.uint8)

def get_video_background_frame(clip, t):
    if t >= clip.duration:
        t = clip.duration - 0.01
    frame = clip.get_frame(t)
    img = Image.fromarray(frame).convert("RGB")
    w, h = img.size
    target_w, target_h = WIDTH, HEIGHT
    if w / h > target_w / target_h:
        new_w = int(h * target_w / target_h)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w * target_h / target_w)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    img = img.resize((target_w, target_h), Image.LANCZOS)
    return np.array(img)

# --------------------------------------------------------
# STREAMLIT APP
# --------------------------------------------------------
st.set_page_config(page_title="Modern Quote Reels", layout="wide", page_icon="✨")
st.title("✨ Modern Quote Reels")
st.caption("Minimal • Neon • Glassmorphism • Video Backgrounds")

col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Quote Theme", "digital minimalism")
with col2:
    use_modern = st.checkbox("Use modern templates only", True)
    templates = MODERN_TEMPLATES if use_modern else ALL_TEMPLATES
    template = st.selectbox("🎨 Template", templates)

col3, col4 = st.columns(2)
with col3:
    anim = st.selectbox("🔤 Text Animation", TEXT_ANIMATIONS)
with col4:
    duration = st.slider("⏱️ Duration (sec)", 5, 10, 7)

st.markdown("### 🎥 Optional Video Background (9:16 .mp4)")
video_upload = st.file_uploader("Upload video", type=["mp4"])

if st.button("✨ Generate Quote", use_container_width=True):
    with st.spinner("Generating..."):
        content = get_ai_quote(topic)
        if content:
            st.session_state.content = content
            st.session_state.config = {
                "template": template,
                "animation": anim,
                "duration": duration,
                "video": video_upload
            }
        else:
            st.error("Failed to generate quote.")

if 'content' in st.session_state:
    content = st.session_state.content
    config = st.session_state.config

    st.subheader("✏️ Edit")
    quote = st.text_area("Quote", content["quote"], max_chars=200)
    author = st.text_input("Author", content["author"])
    st.text_area("Hashtags", content["hashtags"], disabled=True)

    st.subheader("📱 Preview")
    logo = load_logo()
    font_q = fit_font(quote, WIDTH - 200)
    font_a = get_font(50)
    lines = split_lines(quote, font_q, WIDTH - 200)
    preview = render_frame(2.0, lines, author, logo, font_q, font_a, config["template"], config["animation"])
    st.image(preview, width=320)

    if st.button("🚀 Export", type="primary", use_container_width=True):
        with st.spinner("Rendering..."):
            total_frames = FPS * config["duration"]
            frames = []
            video_clip = None

            # Handle video background
            if config["video"]:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(config["video"].getvalue())
                    tmp.flush()
                    video_clip = VideoFileClip(tmp.name)
                    if video_clip.duration < config["duration"]:
                        video_clip = video_clip.loop(duration=config["duration"])
                    else:
                        video_clip = video_clip.subclip(0, config["duration"])

            for i in range(total_frames):
                t = i / FPS
                if video_clip:
                    bg = get_video_background_frame(video_clip, t)
                    frame = render_frame(t, lines, author, logo, font_q, font_a,
                                       config["template"], config["animation"], bg_array=bg)
                else:
                    frame = render_frame(t, lines, author, logo, font_q, font_a,
                                       config["template"], config["animation"])
                frames.append(frame)

            # Export
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

            st.success("✅ Done!")
            with open(out_path, "rb") as f:
                st.download_button("⬇️ Download Video", f, "Modern_Quote.mp4", "video/mp4")
            st.video(out_path)

            clip.close()
            if video_clip: video_clip.close()
            del frames
            gc.collect()
