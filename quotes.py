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
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_reader import FFMPEG_VideoReader

# --------------------------------------------------------
# CONFIG
# --------------------------------------------------------
WIDTH, HEIGHT = 1080, 1920
FPS = 30
DURATION = 6
TEXT_BG_COLOR = (0, 0, 0, 180)  # Semi-transparent black

# Royalty-free backgrounds (Pixabay: free for commercial use)
BACKGROUND_VIDEOS = {
    "Ocean Waves": "https://ik.imagekit.io/ericmwangi/oceanbg.mp4",
    "Floating Clouds": "https://cdn.pixabay.com/video/2023/06/15/164555-806155701_large.mp4",
    "Misty Forest": "https://cdn.pixabay.com/video/2022/01/27/105839-710637991_large.mp4",
    "Gentle Fire": "https://cdn.pixabay.com/video/2022/02/15/110845-717522810_large.mp4",
    "Waterfall": "https://cdn.pixabay.com/video/2023/05/01/162303-799296582_large.mp4",
    "Starry Sky": "https://cdn.pixabay.com/video/2022/07/26/115453-752008984_large.mp4",
}
TEMPLATES = ["Glass Morphism", "Neon Pulse", "Minimal Zen", "Golden Waves", "Modern Grid"]

# --------------------------------------------------------
# CACHED LOADERS
# --------------------------------------------------------
@st.cache_resource
def load_font():
    try:
        resp = requests.get("https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf", timeout=10)
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
        resp = requests.get("https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037", timeout=10)
        if resp.status_code == 200:
            logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            ratio = min(280 / logo.width, 140 / logo.height)
            return logo.resize((int(logo.width * ratio), int(logo.height * ratio)), Image.LANCZOS)
    except:
        pass
    img = Image.new("RGBA", (280, 140), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.text((20, 25), "SM", fill="#00F0FF", font=get_font(80))
    return img

@st.cache_data(ttl=3600)
def download_asset(url, suffix):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception as e:
        st.sidebar.error(f"Load failed: {str(e)[:50]}")
    return None

# --------------------------------------------------------
# RENDER ENGINE (SHARED BY PREVIEW & EXPORT)
# --------------------------------------------------------
def split_lines(text, font, max_width):
    words = text.split()
    if not words: return [""]
    lines, current = [], []
    for word in words:
        test = ' '.join(current + [word])
        w = font.getbbox(test)[2] - font.getbbox(test)[0]
        if w <= max_width:
            current.append(word)
        else:
            if current: lines.append(' '.join(current))
            current = [word]
    if current: lines.append(' '.join(current))
    return lines

def create_animated_bg(template, t):
    base = Image.new("RGB", (WIDTH, HEIGHT), (15, 15, 18))
    draw = ImageDraw.Draw(base, "RGBA")
    if template == "Glass Morphism":
        cx, cy = WIDTH//2, HEIGHT//2
        for i in range(4):
            angle = t*0.6 + i
            x = cx + int(250 * math.cos(angle))
            y = cy + int(180 * math.sin(angle*0.8))
            r = 160 + 30*math.sin(t+i)
            a = int(25 + 20*math.sin(t*1.2+i))
            draw.ellipse([x-r,y-r,x+r,y+r], fill="#00F0FF"+f"{a:02x}")
    elif template == "Neon Pulse":
        for i in range(5):
            r = 120 + i*160 + 25*math.sin(t*0.9+i)
            a = int(35 + 30*abs(math.sin(t*1.6+i)))
            draw.ellipse([WIDTH//2-r,HEIGHT//2-r,WIDTH//2+r,HEIGHT//2+r], outline="#00F0FF"+f"{a:02x}", width=2)
        for i in range(15):
            x = int(WIDTH*(0.25+0.5*math.sin(t*0.5+i)))
            y = int(HEIGHT*(0.2+0.6*math.cos(t*0.4+i)))
            s = 3 + 2*math.sin(t*0.7+i)
            a = int(120 + 100*math.sin(t*1.1+i))
            draw.ellipse([x-s,y-s,x+s,y+s], fill="#00F0FF"+f"{max(0,min(255,a)):02x}")
    else:
        step = 180 if template == "Modern Grid" else 200
        for x in range(0, WIDTH, step):
            draw.line([(x,0),(x,HEIGHT)], fill="#00F0FF"+"08", width=1)
        for y in range(0, HEIGHT, step):
            draw.line([(0,y),(WIDTH,y)], fill="#00F0FF"+"08", width=1)
    return np.array(base)

def draw_quote(draw, lines, y0, font_q, font_a, author, show_bg):
    line_h = int(font_q.size * 1.25)
    # Measure boxes
    boxes = []
    for i, line in enumerate(lines):
        y = y0 + i * line_h
        left, top, right, bottom = font_q.getbbox(line)
        w, h = right - left, bottom - top
        x = WIDTH // 2 - w // 2
        boxes.append((x - 20, y - h - 10, x + w + 20, y + 10))
    # Draw background
    if show_bg:
        for box in boxes:
            draw.rectangle(box, fill=TEXT_BG_COLOR)
    # Draw text
    for i, line in enumerate(lines):
        y = y0 + i * line_h
        draw.text((WIDTH//2, y), line, fill="#FFFFFF", font=font_q, anchor="mm")
    if author:
        draw.text((WIDTH//2, y0 + len(lines)*line_h + 50), author, fill="#00F0FF", font=font_a, anchor="mm")
    draw.text((WIDTH//2, HEIGHT - 180), "Save this wisdom ✨", fill="#00F0FF", font=get_font(50), anchor="mm")

def render_frame(t, quote, author, font_size, y_offset, show_bg, bg_type, bg_ident, logo, bg_array=None):
    # Background
    if bg_array is None:
        if bg_type == "video":
            # This shouldn't happen in preview — video bg handled externally
            bg_array = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        else:
            bg_array = create_animated_bg(bg_ident, t)
    
    # Overlay
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    if logo:
        overlay.paste(logo, (70, 60), logo)
    draw = ImageDraw.Draw(overlay)
    
    font_q = get_font(max(60, font_size))
    font_a = get_font(max(40, int(font_q.size * 0.65)))
    lines = split_lines(quote, font_q, WIDTH - 200)
    
    draw_quote(draw, lines, y_offset, font_q, font_a, author, show_bg)
    
    # Composite
    fg = np.array(overlay)[:, :, :3]
    alpha = np.array(overlay)[:, :, 3:] / 255.0
    return (bg_array * (1 - alpha) + fg * alpha).astype(np.uint8)

def extract_video_frame(video_path, t=0.0):
    """Extract exact frame at time t"""
    try:
        with VideoFileClip(video_path) as clip:
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
    except Exception as e:
        st.error(f"Frame extract failed: {e}")
        return np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

# --------------------------------------------------------
# UI
# --------------------------------------------------------
st.set_page_config(page_title="WYSIWYG Quote Studio", layout="wide")
with st.sidebar:
    st.image("https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037", width=120)
    st.title("✨ WYSIWYG Studio")
    
    quote = st.text_area("Your Quote", "Breathe. It's just a bad day, not a bad life.", height=100)
    author = st.text_input("Author", "— Anonymous")
    
    st.markdown("### 🎨 Text Style")
    font_size = st.slider("Font Size", 60, 130, 85, step=1)
    y_offset = st.slider("Vertical Position", 350, 850, 520, step=5)
    show_bg = st.checkbox("Text Background", value=True)
    
    st.markdown("### 🖼️ Background")
    bg_mode = st.radio("Type", ["Online Video", "Animated Template"])
    if bg_mode == "Online Video":
        bg_name = st.selectbox("Video", list(BACKGROUND_VIDEOS.keys()))
        video_url = BACKGROUND_VIDEOS[bg_name]
    else:
        template = st.selectbox("Template", TEMPLATES)
        video_url = None
    
    export = st.button("🚀 Export 6s Video", type="primary", use_container_width=True)

# --------------------------------------------------------
# TRUE WYSIWYG PREVIEW (t=0.0 — same as video start)
# --------------------------------------------------------
logo = load_logo()
use_video = (bg_mode == "Online Video")

# Get background frame at t=0.0
if use_video:
    vid_path = download_asset(video_url, ".mp4")
    if vid_path:
        bg_frame = extract_video_frame(vid_path, t=0.0)
        bg_type_for_render = "video"
        bg_ident_for_render = None
    else:
        bg_frame = create_animated_bg("Minimal Zen", 0.0)
        bg_type_for_render = "template"
        bg_ident_for_render = "Minimal Zen"
else:
    bg_frame = create_animated_bg(template, 0.0)
    bg_type_for_render = "template"
    bg_ident_for_render = template

# Render EXACT same function used in export
preview_frame = render_frame(
    t=0.0,  # ← Key: matches first video frame
    quote=quote,
    author=author,
    font_size=font_size,
    y_offset=y_offset,
    show_bg=show_bg,
    bg_type=bg_type_for_render,
    bg_ident=bg_ident_for_render,
    logo=logo,
    bg_array=bg_frame
)

st.title("✨ WYSIWYG Quote Studio")
st.caption("Preview = First frame of your video. What you see is what you get.")
st.image(preview_frame, channels="RGB", width=360, caption="✅ Exact frame 0 of your video")

# --------------------------------------------------------
# EXPORT (uses same render_frame for all frames)
# --------------------------------------------------------
if export:
    if not quote.strip():
        st.error("Add a quote!")
    else:
        with st.spinner(".Rendering video (30-50 sec)..."):
            # Prepare background clip if video
            video_clip = None
            if use_video and vid_path:
                try:
                    video_clip = VideoFileClip(vid_path)
                    if video_clip.duration < DURATION:
                        video_clip = video_clip.loop(duration=DURATION)
                    else:
                        video_clip = video_clip.subclip(0, DURATION)
                except:
                    video_clip = None
            
            # Render all frames
            frames = []
            total = FPS * DURATION
            for i in range(total):
                t = i / FPS
                if video_clip is not None:
                    bg_arr = extract_video_frame(vid_path, t)
                    frame = render_frame(t, quote, author, font_size, y_offset, show_bg, "video", None, logo, bg_arr)
                else:
                    frame = render_frame(t, quote, author, font_size, y_offset, show_bg, "template", template, logo)
                frames.append(frame)
            
            # Save
            out = os.path.join(tempfile.gettempdir(), f"quote_{int(time.time())}.mp4")
            audio = download_asset("https://ik.imagekit.io/ericmwangi/ambient-piano-112970.mp3?updatedAt=1764101548797", ".mp3")
            from moviepy.editor import ImageSequenceClip, AudioFileClip
            clip = ImageSequenceClip(frames, fps=FPS)
            if audio:
                try:
                    aclip = AudioFileClip(audio).subclip(0, clip.duration)
                    clip = clip.set_audio(aclip)
                except:
                    pass
            clip.write_videofile(out, codec="libx264", audio_codec="aac", logger=None, threads=4)
            
            st.success("✅ Done!")
            with open(out, "rb") as f:
                st.download_button("⬇️ Download", f, "WYSIWYG_Quote.mp4", use_container_width=True)
            st.video(out)
            
            clip.close()
            if video_clip: video_clip.close()
            del frames
            gc.collect()